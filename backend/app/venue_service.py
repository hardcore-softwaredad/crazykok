from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import threading
import time
import unicodedata
import uuid
from datetime import date
from difflib import SequenceMatcher
from typing import Any

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from .venue_registry import CONFIDENCE_ORDER, VENUE_FIELD_MAP, VENUE_FIELD_NAMES
from .venue_schemas import DuplicateCheckRequest, VenueCreate, VenueUpdate


MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 500
FORMULA_PREFIXES = ("=", "+", "-", "@")

RELATED_IMPORTS = {
    "contacts": {
        "model": models.VenueContact,
        "external_key": "contact_external_id",
        "fields": (
            "contact_external_id", "venue_external_id", "contact_type", "name", "role_title", "organization",
            "email", "phone", "mobile", "website_url", "notes", "source_url", "last_verified_at",
            "confidence_rating", "active",
        ),
        "date_fields": {"last_verified_at"},
        "required_fields": {"contact_external_id", "venue_external_id"},
    },
    "documents": {
        "model": models.VenueDocument,
        "external_key": "document_external_id",
        "fields": (
            "document_external_id", "venue_external_id", "document_type", "title", "url", "local_path",
            "description", "source_url", "retrieved_at", "last_verified_at", "confidence_rating", "notes", "active",
        ),
        "date_fields": {"retrieved_at", "last_verified_at"},
        "required_fields": {"document_external_id", "venue_external_id", "document_type", "title"},
    },
    "aliases": {
        "model": models.VenueAlias,
        "external_key": "alias_external_id",
        "fields": ("alias_external_id", "venue_external_id", "alias", "alias_type", "source_url", "notes", "active"),
        "date_fields": set(),
        "required_fields": {"alias_external_id", "venue_external_id", "alias"},
    },
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def normalize_postcode(value: str | None) -> str:
    return re.sub(r"\s+", "", (value or "")).upper()


def venue_to_dict(venue: models.Venue) -> dict[str, Any]:
    result = {"id": venue.id, "created_at": venue.created_at, "updated_at": venue.updated_at}
    result.update({field: getattr(venue, field) for field in VENUE_FIELD_NAMES})
    return result


def validate_completeness(values: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    status = values.get("research_status") or "discovered"
    if status in {"researched", "verified", "complete"}:
        for field in ("town", "municipality", "province", "country", "source_url_primary", "confidence_rating"):
            if not values.get(field):
                errors.append(
                    {"code": "status_requirement", "field": field, "message": f"{field} is required for {status} venues"}
                )
    if (values.get("latitude") is None) != (values.get("longitude") is None):
        errors.append(
            {"code": "coordinate_pair", "field": "latitude", "message": "latitude and longitude must be supplied together"}
        )
    return errors


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def duplicate_candidates(
    db: Session, candidate: DuplicateCheckRequest, exclude_venue_id: int | None = None
) -> list[dict[str, Any]]:
    query = db.query(models.Venue).filter(models.Venue.active.is_(True))
    if exclude_venue_id:
        query = query.filter(models.Venue.id != exclude_venue_id)
    if candidate.venue_external_id:
        query = query.filter(models.Venue.venue_external_id != candidate.venue_external_id)

    candidate_name = normalize_text(candidate.venue_name)
    candidate_town = normalize_text(candidate.town)
    candidate_municipality = normalize_text(candidate.municipality)
    candidate_postcode = normalize_postcode(candidate.postcode)
    results = []

    for venue in query.all():
        signals: list[str] = []
        score = 0.0
        names = [venue.venue_name]
        names.extend(alias.alias for alias in venue.aliases if alias.active)
        name_score = max((SequenceMatcher(None, candidate_name, normalize_text(name)).ratio() for name in names), default=0)
        if name_score >= 0.92:
            score += 45
            signals.append("same or very similar name/alias")
        elif name_score >= 0.78:
            score += 25
            signals.append("similar name/alias")

        if candidate_town and candidate_town == normalize_text(venue.town):
            score += 20
            signals.append("same town")
        if candidate_municipality and candidate_municipality == normalize_text(venue.municipality):
            score += 15
            signals.append("same municipality")
        if candidate_postcode and candidate_postcode == normalize_postcode(venue.postcode):
            score += 30
            signals.append("same postcode")
        if candidate.street_address and normalize_text(candidate.street_address) == normalize_text(venue.street_address):
            score += 25
            signals.append("same street address")
        if candidate.website_url and venue.website_url and candidate.website_url.rstrip("/") == venue.website_url.rstrip("/"):
            score += 35
            signals.append("same website")
        if None not in (candidate.latitude, candidate.longitude, venue.latitude, venue.longitude):
            distance = _haversine_meters(candidate.latitude, candidate.longitude, venue.latitude, venue.longitude)
            if distance <= 150:
                score += 30
                signals.append(f"coordinates within {round(distance)} m")
        if candidate_town and venue.town and candidate_town != normalize_text(venue.town):
            score -= 15
            signals.append("different town")

        if score >= 45:
            results.append(
                {
                    "id": venue.id,
                    "venue_external_id": venue.venue_external_id,
                    "venue_name": venue.venue_name,
                    "score": min(100.0, round(score, 1)),
                    "signals": signals,
                }
            )
    return sorted(results, key=lambda item: (-item["score"], item["venue_name"]))


def create_venue(db: Session, payload: VenueCreate) -> models.Venue:
    values = payload.model_dump()
    existing = db.query(models.Venue).filter(models.Venue.venue_external_id == values["venue_external_id"]).first()
    if existing:
        raise HTTPException(409, detail={"code": "external_id_exists", "message": "Venue external ID already exists"})
    errors = validate_completeness(values)
    if errors:
        raise HTTPException(422, detail=errors)
    venue = models.Venue(**values)
    db.add(venue)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(409, detail={"code": "venue_conflict", "message": "Venue external ID or slug already exists"}) from exc
    db.refresh(venue)
    return venue


def update_venue(db: Session, venue: models.Venue, payload: VenueUpdate) -> models.Venue:
    changes = payload.model_dump(exclude_unset=True)
    if "venue_external_id" in changes and changes["venue_external_id"] != venue.venue_external_id:
        raise HTTPException(422, detail={"code": "immutable_external_id", "message": "venue_external_id is immutable"})
    merged = {field: getattr(venue, field) for field in VENUE_FIELD_NAMES}
    merged.update(changes)
    errors = validate_completeness(merged)
    if errors:
        raise HTTPException(422, detail=errors)
    for key, value in changes.items():
        setattr(venue, key, value)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(409, detail={"code": "venue_conflict", "message": "Venue slug conflicts with another venue"}) from exc
    db.refresh(venue)
    return venue


def parse_csv_value(field_name: str, raw: str) -> Any:
    value = raw.strip()
    if not value:
        return None
    field = VENUE_FIELD_MAP[field_name]
    if field.value_type == "integer":
        return int(value)
    if field.value_type == "decimal":
        return float(value.replace(",", "."))
    if field.value_type == "date":
        return date.fromisoformat(value)
    if field.value_type == "boolean":
        lowered = value.casefold()
        if lowered not in {"true", "false", "yes", "no", "1", "0"}:
            raise ValueError("expected true or false")
        return lowered in {"true", "yes", "1"}
    if value.startswith(FORMULA_PREFIXES):
        raise ValueError("spreadsheet formulas are not accepted")
    return value


async def read_upload(upload: UploadFile) -> bytes:
    content = await upload.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(413, detail={"code": "file_too_large", "message": "CSV exceeds 5 MB"})
    return content


def parse_venue_csv(content: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(422, detail={"code": "csv_encoding", "message": "CSV must be UTF-8"}) from exc
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise HTTPException(422, detail={"code": "duplicate_header", "message": "CSV contains duplicate headers"})
        unknown = [header for header in headers if header not in VENUE_FIELD_MAP]
        if unknown:
            raise HTTPException(422, detail={"code": "unknown_header", "message": f"Unknown headers: {', '.join(unknown)}"})
        for required in ("venue_external_id", "venue_name"):
            if required not in headers:
                raise HTTPException(422, detail={"code": "missing_header", "message": f"Missing required header: {required}"})
        raw_rows = list(reader)
    except csv.Error as exc:
        raise HTTPException(422, detail={"code": "malformed_csv", "message": str(exc)}) from exc
    if len(raw_rows) > MAX_CSV_ROWS:
        raise HTTPException(422, detail={"code": "too_many_rows", "message": f"A batch may contain at most {MAX_CSV_ROWS} rows"})

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for row_number, raw_row in enumerate(raw_rows, start=2):
        parsed: dict[str, Any] = {}
        for name in headers:
            try:
                value = parse_csv_value(name, raw_row.get(name) or "")
                if value is not None:
                    parsed[name] = value
            except (ValueError, TypeError) as exc:
                errors.append(
                    {"row": row_number, "field": name, "code": "invalid_value", "message": str(exc)}
                )
        external_id = parsed.get("venue_external_id")
        if not external_id:
            errors.append({"row": row_number, "field": "venue_external_id", "code": "required", "message": "Required"})
        elif external_id in seen_ids:
            errors.append(
                {"row": row_number, "field": "venue_external_id", "code": "duplicate_in_file", "message": "Repeated external ID"}
            )
        else:
            seen_ids.add(external_id)
        parsed["_row"] = row_number
        rows.append(parsed)
    return rows, errors, headers


def parse_related_csv(kind: str, content: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contract = RELATED_IMPORTS[kind]
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise HTTPException(422, detail={"code": "duplicate_header", "message": f"{kind} CSV contains duplicate headers"})
        unknown = set(headers) - set(contract["fields"])
        if unknown:
            raise HTTPException(422, detail={"code": "unknown_header", "message": f"Unknown {kind} headers: {', '.join(sorted(unknown))}"})
        for required in (contract["external_key"], "venue_external_id"):
            if required not in headers:
                raise HTTPException(422, detail={"code": "missing_header", "message": f"Missing {kind} header: {required}"})
        raw_rows = list(reader)
    except UnicodeDecodeError as exc:
        raise HTTPException(422, detail={"code": "csv_encoding", "message": f"{kind} CSV must be UTF-8"}) from exc
    except csv.Error as exc:
        raise HTTPException(422, detail={"code": "malformed_csv", "message": str(exc)}) from exc
    if len(raw_rows) > MAX_CSV_ROWS:
        raise HTTPException(422, detail={"code": "too_many_rows", "message": f"A {kind} batch may contain at most {MAX_CSV_ROWS} rows"})

    rows, errors, seen = [], [], set()
    for row_number, raw in enumerate(raw_rows, start=2):
        parsed: dict[str, Any] = {"_row": row_number}
        for field in headers:
            value = (raw.get(field) or "").strip()
            if not value:
                continue
            try:
                if field == "local_path" and value:
                    raise ValueError("local paths cannot be imported; upload the file in the app")
                if field in contract["date_fields"]:
                    parsed[field] = date.fromisoformat(value)
                elif field == "active":
                    if value.casefold() not in {"true", "false", "yes", "no", "1", "0"}:
                        raise ValueError("expected true or false")
                    parsed[field] = value.casefold() in {"true", "yes", "1"}
                else:
                    if value.startswith(FORMULA_PREFIXES):
                        raise ValueError("spreadsheet formulas are not accepted")
                    parsed[field] = value
            except ValueError as exc:
                errors.append({"file": kind, "row": row_number, "field": field, "code": "invalid_value", "message": str(exc)})
        external_id = parsed.get(contract["external_key"])
        if not external_id:
            errors.append({"file": kind, "row": row_number, "field": contract["external_key"], "code": "required", "message": "Required"})
        elif external_id in seen:
            errors.append({"file": kind, "row": row_number, "field": contract["external_key"], "code": "duplicate_in_file", "message": "Repeated external ID"})
        else:
            seen.add(external_id)
        for required in contract["required_fields"]:
            if not parsed.get(required):
                errors.append({"file": kind, "row": row_number, "field": required, "code": "required", "message": "Required"})
        rows.append(parsed)
    return rows, errors


def preview_related_rows(
    db: Session, kind: str, rows: list[dict[str, Any]], incoming_venue_ids: set[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contract = RELATED_IMPORTS[kind]
    model = contract["model"]
    external_key = contract["external_key"]
    results, errors = [], []
    for row in rows:
        row_number = row["_row"]
        parent_external_id = row.get("venue_external_id")
        parent = db.query(models.Venue).filter(models.Venue.venue_external_id == parent_external_id).first()
        if not parent and parent_external_id not in incoming_venue_ids:
            errors.append(
                {"file": kind, "row": row_number, "field": "venue_external_id", "code": "parent_not_found", "message": "Venue is not in the database or this batch"}
            )
        existing = db.query(model).filter(getattr(model, external_key) == row.get(external_key)).first()
        values = {key: value for key, value in row.items() if not key.startswith("_") and key != "venue_external_id"}
        changes = {}
        if existing:
            changes = {key: {"before": getattr(existing, key), "after": value} for key, value in values.items() if getattr(existing, key) != value}
        results.append(
            {
                "file": kind, "row": row_number, "external_id": row.get(external_key),
                "venue_external_id": parent_external_id,
                "action": "update" if existing and changes else "unchanged" if existing else "create",
                "record_id": existing.id if existing else None, "changes": changes,
            }
        )
    error_rows = {(error["file"], error["row"]) for error in errors}
    for result in results:
        if (kind, result["row"]) in error_rows:
            result["action"] = "blocked_validation"
    return results, errors


def _model_errors(exc: ValidationError, row_number: int) -> list[dict[str, Any]]:
    return [
        {
            "row": row_number,
            "field": ".".join(str(part) for part in error["loc"]),
            "code": "validation_error",
            "message": error["msg"],
        }
        for error in exc.errors()
    ]


def preview_venue_rows(db: Session, rows: list[dict[str, Any]], parse_errors: list[dict[str, Any]]) -> dict[str, Any]:
    previews: list[dict[str, Any]] = []
    errors = list(parse_errors)
    for row in rows:
        row_number = row["_row"]
        supplied = {key: value for key, value in row.items() if not key.startswith("_")}
        external_id = supplied.get("venue_external_id")
        existing = db.query(models.Venue).filter(models.Venue.venue_external_id == external_id).first() if external_id else None
        if not existing and external_id:
            external_alias = db.query(models.VenueAlias).filter(
                models.VenueAlias.alias_external_id == external_id,
                models.VenueAlias.alias_type == "import_external_id",
                models.VenueAlias.active.is_(True),
            ).first()
            existing = external_alias.venue if external_alias else None
        if existing:
            changes = {
                key: {"before": getattr(existing, key), "after": value}
                for key, value in supplied.items()
                if key != "venue_external_id" and getattr(existing, key) != value
            }
            merged = {field: getattr(existing, field) for field in VENUE_FIELD_NAMES}
            merged.update(supplied)
            try:
                VenueUpdate(**supplied)
            except ValidationError as exc:
                errors.extend(_model_errors(exc, row_number))
            errors.extend({"row": row_number, **error} for error in validate_completeness(merged))
            incoming_confidence = supplied.get("confidence_rating") or "E"
            lower_confidence = bool(
                changes and incoming_confidence and
                CONFIDENCE_ORDER.get(incoming_confidence, 0) < CONFIDENCE_ORDER.get(existing.confidence_rating or "E", 0)
            )
            action = "unchanged" if not changes else "blocked_confidence" if lower_confidence else "update"
            previews.append(
                {
                    "row": row_number, "external_id": external_id, "venue_name": supplied.get("venue_name"),
                    "action": action, "venue_id": existing.id, "changes": changes,
                    "warnings": ["Incoming confidence is lower than the current record"] if lower_confidence else [],
                }
            )
        else:
            try:
                candidate_model = VenueCreate(**supplied)
                errors.extend({"row": row_number, **error} for error in validate_completeness(candidate_model.model_dump()))
            except ValidationError as exc:
                errors.extend(_model_errors(exc, row_number))
            candidates = []
            if supplied.get("venue_name"):
                duplicate_request = DuplicateCheckRequest(
                    **{key: supplied.get(key) for key in DuplicateCheckRequest.model_fields if supplied.get(key) is not None}
                )
                candidates = duplicate_candidates(db, duplicate_request)
            previews.append(
                {
                    "row": row_number, "external_id": external_id, "venue_name": supplied.get("venue_name"),
                    "action": "blocked_duplicate" if candidates else "create", "venue_id": None, "changes": {},
                    "duplicate_candidates": candidates, "warnings": [],
                }
            )
    error_rows = {error.get("row") for error in errors}
    for preview in previews:
        if preview["row"] in error_rows:
            preview["action"] = "blocked_validation"
    return {"rows": previews, "errors": errors}


class PreviewStore:
    def __init__(self):
        self._items: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def put(self, item: dict[str, Any]) -> str:
        token = uuid.uuid4().hex
        with self._lock:
            self._items[token] = {**item, "expires": time.time() + 30 * 60}
            self._items = {key: value for key, value in self._items.items() if value["expires"] > time.time()}
            while len(self._items) > 50:
                self._items.pop(next(iter(self._items)))
        return token

    def get(self, token: str) -> dict[str, Any] | None:
        with self._lock:
            item = self._items.get(token)
        if not item or item["expires"] <= time.time():
            return None
        return item

    def delete(self, token: str) -> None:
        with self._lock:
            self._items.pop(token, None)


preview_store = PreviewStore()


def csv_safe(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (date,)):
        return value.isoformat()
    rendered = str(value)
    if rendered.startswith(FORMULA_PREFIXES):
        return "'" + rendered
    return rendered


def venue_csv(venues: list[models.Venue], include_internal_notes: bool = False) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=VENUE_FIELD_NAMES, lineterminator="\n")
    writer.writeheader()
    for venue in venues:
        writer.writerow(
            {
                field: "" if field == "internal_notes" and not include_internal_notes else csv_safe(getattr(venue, field))
                for field in VENUE_FIELD_NAMES
            }
        )
    return output.getvalue()


def related_csv(kind: str, records: list[Any]) -> str:
    contract = RELATED_IMPORTS[kind]
    fields = contract["fields"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for record in records:
        row = {}
        for field in fields:
            if field == "venue_external_id":
                value = record.venue.venue_external_id
            elif field == "local_path":
                value = None
            else:
                value = getattr(record, field)
            row[field] = csv_safe(value)
        writer.writerow(row)
    return output.getvalue()


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def import_result_csv(result: dict[str, Any]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=("row", "external_id", "venue_name", "action", "message"), lineterminator="\n")
    writer.writeheader()
    for row in result.get("rows", []):
        writer.writerow(
            {
                "row": row.get("row"), "external_id": row.get("external_id"), "venue_name": row.get("venue_name"),
                "action": row.get("action"), "message": "; ".join(row.get("warnings", [])),
            }
        )
    return output.getvalue()
