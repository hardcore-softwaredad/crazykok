from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .hypermedia import api_url
from .venue_registry import CONFIDENCE_ORDER, VENUE_FIELD_NAMES, schema_document
from .venue_schemas import (
    DuplicateCheckRequest,
    VenueAliasCreate,
    VenueAliasRead,
    VenueContactCreate,
    VenueContactRead,
    VenueCreate,
    VenueDocumentCreate,
    VenueDocumentRead,
    VenueNoteCreate,
    VenueNoteRead,
    VenuePhotoCreate,
    VenuePhotoRead,
    VenueRead,
    VenueUpdate,
)
from .venue_service import (
    RELATED_IMPORTS,
    create_venue,
    digest,
    duplicate_candidates,
    import_result_csv,
    parse_venue_csv,
    parse_related_csv,
    preview_store,
    preview_venue_rows,
    preview_related_rows,
    read_upload,
    related_csv,
    update_venue,
    venue_csv,
    venue_to_dict,
)
from .venue_storage import remove_attachment, resolve_attachment, store_upload


router = APIRouter(prefix="/venues", tags=["venues"])
import_router = APIRouter(prefix="/venue-imports", tags=["venue imports"])


class ImportApplyRequest(BaseModel):
    preview_token: str
    resolutions: dict[str, dict[str, str]] = Field(default_factory=dict)


class MergeRequest(BaseModel):
    source_venue_id: int
    target_venue_id: int
    reason: str = Field(min_length=1)


class NotDuplicateRequest(BaseModel):
    venue_id_a: int
    venue_id_b: int
    reason: str = Field(min_length=1)


def find_venue(db: Session, venue_id: int) -> models.Venue:
    venue = db.get(models.Venue, venue_id)
    if not venue:
        raise HTTPException(404, detail={"code": "venue_not_found", "message": "Venue not found"})
    return venue


def venue_response(request: Request, venue: models.Venue) -> dict[str, Any]:
    result = venue_to_dict(venue)
    result["_links"] = {
        "self": {"href": api_url(request, f"venues/{venue.id}")},
        "collection": {"href": api_url(request, "venues")},
        "opportunities": {"href": api_url(request, "opportunities", [("venue_id", venue.id)])},
    }
    return result


@router.get("/schema")
def venue_schema():
    return schema_document()


@router.post("/duplicate-check")
def check_duplicates(payload: DuplicateCheckRequest, db: Session = Depends(get_db)):
    return {"candidates": duplicate_candidates(db, payload)}


@router.post("/not-duplicates", status_code=201)
def record_not_duplicate(payload: NotDuplicateRequest, db: Session = Depends(get_db)):
    if payload.venue_id_a == payload.venue_id_b:
        raise HTTPException(422, detail={"code": "same_venue", "message": "A venue cannot be distinct from itself"})
    a, b = sorted((payload.venue_id_a, payload.venue_id_b))
    find_venue(db, a)
    find_venue(db, b)
    decision = models.VenueNotDuplicate(venue_id_a=a, venue_id_b=b, reason=payload.reason)
    db.add(decision)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        decision = db.query(models.VenueNotDuplicate).filter_by(venue_id_a=a, venue_id_b=b).one()
    return {"id": decision.id, "venue_id_a": a, "venue_id_b": b, "reason": decision.reason}


@router.post("/merge")
def merge_venues(payload: MergeRequest, db: Session = Depends(get_db)):
    if payload.source_venue_id == payload.target_venue_id:
        raise HTTPException(422, detail={"code": "same_venue", "message": "Choose two different venues"})
    source = find_venue(db, payload.source_venue_id)
    target = find_venue(db, payload.target_venue_id)
    try:
        for model in (models.VenueContact, models.VenueDocument, models.VenueAlias, models.VenueNote):
            db.query(model).filter(model.venue_id == source.id).update({"venue_id": target.id})
        next_order = db.query(models.VenuePhoto).filter(models.VenuePhoto.venue_id == target.id).count()
        for photo in db.query(models.VenuePhoto).filter(models.VenuePhoto.venue_id == source.id).order_by(models.VenuePhoto.sort_order):
            photo.venue_id = target.id
            photo.sort_order = next_order
            photo.is_cover = False
            next_order += 1
        db.query(models.Opportunity).filter(models.Opportunity.venue_id == source.id).update({"venue_id": target.id})
        db.add(
            models.VenueAlias(
                alias_external_id=f"MERGED-{source.venue_external_id}", venue_id=target.id, alias=source.venue_name,
                alias_type="merged_venue", notes=f"Merged from {source.venue_external_id}: {payload.reason}", active=True,
            )
        )
        source.active = False
        source.research_status = "archived"
        source.internal_notes = "\n".join(filter(None, [source.internal_notes, f"Merged into {target.venue_external_id}: {payload.reason}"]))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"source": venue_to_dict(source), "target": venue_to_dict(target)}


@router.get("/export.csv")
def export_venues(
    ids: str | None = Query(default=None, description="Comma-separated venue IDs"),
    q: str | None = None,
    include_internal_notes: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(models.Venue)
    if ids:
        try:
            selected = [int(value) for value in ids.split(",") if value]
        except ValueError as exc:
            raise HTTPException(422, detail={"code": "invalid_ids", "message": "ids must be integers"}) from exc
        query = query.filter(models.Venue.id.in_(selected))
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                models.Venue.venue_name.ilike(pattern), models.Venue.venue_external_id.ilike(pattern),
                models.Venue.town.ilike(pattern), models.Venue.municipality.ilike(pattern),
            )
        )
    content = venue_csv(query.order_by(models.Venue.venue_external_id).all(), include_internal_notes=include_internal_notes)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="venues-export.csv"'},
    )


@router.get("/import-kit.zip")
def import_kit():
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "templates" / "venues_import_template.csv",
        root / "templates" / "venue_contacts_import_template.csv",
        root / "templates" / "venue_documents_import_template.csv",
        root / "templates" / "venue_aliases_import_template.csv",
        root / "templates" / "venues_import_example.csv",
    ]
    instructions = """# Venue research batch instructions

Preserve every CSV header and stable external ID. Leave unknown cells empty; do not guess.
Prefer official venue, municipality, and organiser sources. Include source URLs, research dates,
research status, and confidence. Keep stable venue facts separate from opportunity-specific facts.
Return UTF-8 CSV files and do not place spreadsheet formulas in any cell.
"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if path.exists():
                archive.write(path, arcname=path.name)
        archive.writestr("RESEARCH_INSTRUCTIONS.md", instructions)
        archive.writestr("venue_schema.json", json.dumps(schema_document(), indent=2, default=str))
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="venue-research-import-kit-v1.zip"'},
    )


@router.get("")
def list_venues(
    request: Request,
    q: str | None = Query(default=None, max_length=150),
    town: str | None = None,
    municipality: str | None = None,
    category: str | None = None,
    research_status: str | None = None,
    confidence: str | None = None,
    active: bool | None = True,
    missing_coordinates: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Venue)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                models.Venue.venue_name.ilike(pattern), models.Venue.venue_external_id.ilike(pattern),
                models.Venue.town.ilike(pattern), models.Venue.municipality.ilike(pattern),
                models.Venue.postcode.ilike(pattern),
            )
        )
    if town:
        query = query.filter(models.Venue.town == town)
    if municipality:
        query = query.filter(models.Venue.municipality == municipality)
    if category:
        query = query.filter(models.Venue.venue_category_primary == category)
    if research_status:
        query = query.filter(models.Venue.research_status == research_status)
    if confidence:
        query = query.filter(models.Venue.confidence_rating == confidence)
    if active is not None:
        query = query.filter(models.Venue.active == active)
    if missing_coordinates is True:
        query = query.filter(or_(models.Venue.latitude.is_(None), models.Venue.longitude.is_(None)))
    return [venue_response(request, venue) for venue in query.order_by(models.Venue.venue_name).all()]


@router.post("", status_code=201)
def post_venue(
    request: Request,
    payload: VenueCreate,
    allow_duplicate: bool = Query(False),
    duplicate_reason: str | None = Query(None),
    db: Session = Depends(get_db),
):
    candidate_payload = DuplicateCheckRequest(
        **{
            key: value for key, value in payload.model_dump().items()
            if key in DuplicateCheckRequest.model_fields and value is not None
        }
    )
    candidates = duplicate_candidates(db, candidate_payload)
    if candidates and not allow_duplicate:
        raise HTTPException(
            409,
            detail={"code": "probable_duplicate", "message": "Review likely duplicates before creating", "candidates": candidates},
        )
    if candidates and allow_duplicate and not duplicate_reason:
        raise HTTPException(422, detail={"code": "duplicate_reason_required", "message": "Explain why this is a distinct venue"})
    venue = create_venue(db, payload)
    if candidates:
        for candidate in candidates:
            a, b = sorted((venue.id, candidate["id"]))
            db.add(models.VenueNotDuplicate(venue_id_a=a, venue_id_b=b, reason=duplicate_reason))
        db.commit()
    return venue_response(request, venue)


@router.get("/{venue_id}")
def get_venue(request: Request, venue_id: int, db: Session = Depends(get_db)):
    return venue_response(request, find_venue(db, venue_id))


@router.patch("/{venue_id}")
def patch_venue(request: Request, venue_id: int, payload: VenueUpdate, db: Session = Depends(get_db)):
    return venue_response(request, update_venue(db, find_venue(db, venue_id), payload))


@router.post("/{venue_id}/archive")
def archive_venue(request: Request, venue_id: int, db: Session = Depends(get_db)):
    venue = find_venue(db, venue_id)
    venue.active = False
    venue.research_status = "archived"
    db.commit()
    db.refresh(venue)
    return venue_response(request, venue)


@router.post("/{venue_id}/restore")
def restore_venue(request: Request, venue_id: int, db: Session = Depends(get_db)):
    venue = find_venue(db, venue_id)
    venue.active = True
    if venue.research_status == "archived":
        venue.research_status = "discovered"
    db.commit()
    db.refresh(venue)
    return venue_response(request, venue)


@router.get("/{venue_id}/opportunities")
def venue_opportunities(venue_id: int, db: Session = Depends(get_db)):
    find_venue(db, venue_id)
    rows = db.query(models.Opportunity).filter(models.Opportunity.venue_id == venue_id).order_by(models.Opportunity.event_date.desc()).all()
    return [
        {
            "id": row.id, "name": row.name, "event_date": row.event_date, "application_status": row.application_status,
            "expected_revenue": row.expected_revenue, "expected_attendance": row.expected_attendance,
        }
        for row in rows
    ]


@router.get("/{venue_id}/statistics")
def venue_statistics(venue_id: int, db: Session = Depends(get_db)):
    find_venue(db, venue_id)
    opportunities = db.query(models.Opportunity).filter(models.Opportunity.venue_id == venue_id).all()
    return {
        "opportunity_count": len(opportunities),
        "active_opportunity_count": sum(1 for item in opportunities if item.is_active),
        "published_attendance_total": sum(item.expected_attendance or 0 for item in opportunities),
        "projected_revenue_total": sum(item.expected_revenue or 0 for item in opportunities),
        "derived": True,
    }


def _list_children(db: Session, model, venue_id: int):
    find_venue(db, venue_id)
    return db.query(model).filter(model.venue_id == venue_id).order_by(model.id).all()


def _create_child(db: Session, model, venue_id: int, payload):
    find_venue(db, venue_id)
    child = model(venue_id=venue_id, **payload.model_dump())
    db.add(child)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail={"code": "external_id_exists", "message": "Related external ID already exists"}) from exc
    db.refresh(child)
    return child


def _update_child(db: Session, model, venue_id: int, child_id: int, changes: dict[str, Any]):
    child = db.query(model).filter(model.id == child_id, model.venue_id == venue_id).first()
    if not child:
        raise HTTPException(404, detail={"code": "related_record_not_found", "message": "Related record not found"})
    allowed = {column.name for column in model.__table__.columns} - {"id", "venue_id", "created_at", "updated_at"}
    unknown = set(changes) - allowed
    if unknown:
        raise HTTPException(422, detail={"code": "unknown_fields", "fields": sorted(unknown)})
    for field, value in changes.items():
        setattr(child, field, value)
    db.commit()
    db.refresh(child)
    return child


def _archive_child(db: Session, model, venue_id: int, child_id: int):
    child = db.query(model).filter(model.id == child_id, model.venue_id == venue_id).first()
    if not child:
        raise HTTPException(404, detail={"code": "related_record_not_found", "message": "Related record not found"})
    if hasattr(child, "active"):
        child.active = False
    else:
        db.delete(child)
    db.commit()


@router.get("/{venue_id}/contacts", response_model=list[VenueContactRead])
def list_contacts(venue_id: int, db: Session = Depends(get_db)):
    return _list_children(db, models.VenueContact, venue_id)


@router.post("/{venue_id}/contacts", response_model=VenueContactRead, status_code=201)
def create_contact(venue_id: int, payload: VenueContactCreate, db: Session = Depends(get_db)):
    return _create_child(db, models.VenueContact, venue_id, payload)


@router.patch("/{venue_id}/contacts/{child_id}", response_model=VenueContactRead)
def update_contact(venue_id: int, child_id: int, changes: dict[str, Any], db: Session = Depends(get_db)):
    return _update_child(db, models.VenueContact, venue_id, child_id, changes)


@router.delete("/{venue_id}/contacts/{child_id}", status_code=204)
def archive_contact(venue_id: int, child_id: int, db: Session = Depends(get_db)):
    _archive_child(db, models.VenueContact, venue_id, child_id)


@router.get("/{venue_id}/aliases", response_model=list[VenueAliasRead])
def list_aliases(venue_id: int, db: Session = Depends(get_db)):
    return _list_children(db, models.VenueAlias, venue_id)


@router.post("/{venue_id}/aliases", response_model=VenueAliasRead, status_code=201)
def create_alias(venue_id: int, payload: VenueAliasCreate, db: Session = Depends(get_db)):
    return _create_child(db, models.VenueAlias, venue_id, payload)


@router.patch("/{venue_id}/aliases/{child_id}", response_model=VenueAliasRead)
def update_alias(venue_id: int, child_id: int, changes: dict[str, Any], db: Session = Depends(get_db)):
    return _update_child(db, models.VenueAlias, venue_id, child_id, changes)


@router.delete("/{venue_id}/aliases/{child_id}", status_code=204)
def archive_alias(venue_id: int, child_id: int, db: Session = Depends(get_db)):
    _archive_child(db, models.VenueAlias, venue_id, child_id)


@router.get("/{venue_id}/documents", response_model=list[VenueDocumentRead])
def list_documents(venue_id: int, db: Session = Depends(get_db)):
    return _list_children(db, models.VenueDocument, venue_id)


@router.post("/{venue_id}/documents", response_model=VenueDocumentRead, status_code=201)
def create_document(venue_id: int, payload: VenueDocumentCreate, db: Session = Depends(get_db)):
    return _create_child(db, models.VenueDocument, venue_id, payload)


@router.patch("/{venue_id}/documents/{child_id}", response_model=VenueDocumentRead)
def update_document(venue_id: int, child_id: int, changes: dict[str, Any], db: Session = Depends(get_db)):
    return _update_child(db, models.VenueDocument, venue_id, child_id, changes)


@router.delete("/{venue_id}/documents/{child_id}", status_code=204)
def archive_document(venue_id: int, child_id: int, db: Session = Depends(get_db)):
    _archive_child(db, models.VenueDocument, venue_id, child_id)


@router.post("/{venue_id}/documents/upload", response_model=VenueDocumentRead, status_code=201)
async def upload_document(
    venue_id: int,
    document_external_id: str = Form(...),
    document_type: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    find_venue(db, venue_id)
    stored = await store_upload(file, "documents")
    absolute_path = stored.pop("absolute_path")
    document = models.VenueDocument(
        venue_id=venue_id, document_external_id=document_external_id, document_type=document_type, title=title, **stored
    )
    db.add(document)
    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        absolute_path.unlink(missing_ok=True)
        raise
    return document


@router.get("/{venue_id}/documents/{document_id}/download")
def download_document(venue_id: int, document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.VenueDocument).filter(
        models.VenueDocument.id == document_id, models.VenueDocument.venue_id == venue_id
    ).first()
    if not document or not document.local_path:
        raise HTTPException(404, detail={"code": "document_not_found", "message": "Document not found"})
    path = resolve_attachment(document.local_path)
    return FileResponse(path, media_type=document.mime_type, filename=document.original_filename or path.name)


@router.get("/{venue_id}/photos", response_model=list[VenuePhotoRead])
def list_photos(venue_id: int, db: Session = Depends(get_db)):
    return _list_children(db, models.VenuePhoto, venue_id)


@router.post("/{venue_id}/photos", response_model=VenuePhotoRead, status_code=201)
def create_photo(venue_id: int, payload: VenuePhotoCreate, db: Session = Depends(get_db)):
    if payload.is_cover:
        db.query(models.VenuePhoto).filter(models.VenuePhoto.venue_id == venue_id).update({"is_cover": False})
    return _create_child(db, models.VenuePhoto, venue_id, payload)


@router.patch("/{venue_id}/photos/{child_id}", response_model=VenuePhotoRead)
def update_photo(venue_id: int, child_id: int, changes: dict[str, Any], db: Session = Depends(get_db)):
    if changes.get("is_cover"):
        db.query(models.VenuePhoto).filter(models.VenuePhoto.venue_id == venue_id).update({"is_cover": False})
    return _update_child(db, models.VenuePhoto, venue_id, child_id, changes)


@router.delete("/{venue_id}/photos/{child_id}", status_code=204)
def archive_photo(venue_id: int, child_id: int, db: Session = Depends(get_db)):
    _archive_child(db, models.VenuePhoto, venue_id, child_id)


@router.post("/{venue_id}/photos/upload", response_model=VenuePhotoRead, status_code=201)
async def upload_photo(
    venue_id: int,
    alt_text: str = Form(...),
    caption: str | None = Form(None),
    is_cover: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    find_venue(db, venue_id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(415, detail={"code": "photo_must_be_image", "message": "Photos must be images"})
    stored = await store_upload(file, "photos")
    absolute_path = stored.pop("absolute_path")
    max_order = db.query(models.VenuePhoto.sort_order).filter(models.VenuePhoto.venue_id == venue_id).order_by(
        models.VenuePhoto.sort_order.desc()
    ).first()
    sort_order = (max_order[0] + 1) if max_order else 0
    if is_cover:
        db.query(models.VenuePhoto).filter(models.VenuePhoto.venue_id == venue_id).update({"is_cover": False})
    photo = models.VenuePhoto(
        venue_id=venue_id, alt_text=alt_text, caption=caption, is_cover=is_cover, sort_order=sort_order, **stored
    )
    db.add(photo)
    try:
        db.commit()
        db.refresh(photo)
    except Exception:
        db.rollback()
        absolute_path.unlink(missing_ok=True)
        raise
    return photo


@router.get("/{venue_id}/photos/{photo_id}/content")
def photo_content(venue_id: int, photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(models.VenuePhoto).filter(
        models.VenuePhoto.id == photo_id, models.VenuePhoto.venue_id == venue_id
    ).first()
    if not photo or not photo.local_path:
        raise HTTPException(404, detail={"code": "photo_not_found", "message": "Photo not found"})
    path = resolve_attachment(photo.local_path)
    return FileResponse(path, media_type=photo.mime_type, filename=photo.original_filename or path.name)


@router.get("/{venue_id}/notes", response_model=list[VenueNoteRead])
def list_notes(venue_id: int, db: Session = Depends(get_db)):
    return _list_children(db, models.VenueNote, venue_id)


@router.post("/{venue_id}/notes", response_model=VenueNoteRead, status_code=201)
def create_note(venue_id: int, payload: VenueNoteCreate, db: Session = Depends(get_db)):
    return _create_child(db, models.VenueNote, venue_id, payload)


@router.patch("/{venue_id}/notes/{child_id}", response_model=VenueNoteRead)
def update_note(venue_id: int, child_id: int, changes: dict[str, Any], db: Session = Depends(get_db)):
    return _update_child(db, models.VenueNote, venue_id, child_id, changes)


@router.delete("/{venue_id}/notes/{child_id}", status_code=204)
def delete_note(venue_id: int, child_id: int, db: Session = Depends(get_db)):
    _archive_child(db, models.VenueNote, venue_id, child_id)


@import_router.post("/preview")
async def preview_import(
    venues_file: UploadFile = File(...),
    contacts_file: UploadFile | None = File(None),
    documents_file: UploadFile | None = File(None),
    aliases_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    content = await read_upload(venues_file)
    rows, errors, headers = parse_venue_csv(content)
    result = preview_venue_rows(db, rows, errors)
    related_uploads = {"contacts": contacts_file, "documents": documents_file, "aliases": aliases_file}
    related: dict[str, list[dict[str, Any]]] = {}
    related_contents: dict[str, bytes] = {}
    related_filenames: dict[str, str] = {}
    incoming_venue_ids = {row.get("venue_external_id") for row in rows if row.get("venue_external_id")}
    for kind, upload in related_uploads.items():
        if upload is None:
            continue
        related_content = await read_upload(upload)
        related_rows, related_errors = parse_related_csv(kind, related_content)
        related_preview, parent_errors = preview_related_rows(db, kind, related_rows, incoming_venue_ids)
        related[kind] = related_preview
        related_contents[kind] = related_content
        related_filenames[kind] = upload.filename or f"{kind}.csv"
        result["errors"].extend(related_errors)
        result["errors"].extend(parent_errors)
    token = preview_store.put(
        {
            "content": content, "rows": rows, "filename": venues_file.filename or "venues.csv",
            "sha256": digest(content), "headers": headers, "related_contents": related_contents,
            "related_filenames": related_filenames,
        }
    )
    return {**result, "related": related, "preview_token": token, "filename": venues_file.filename, "sha256": digest(content)}


@import_router.post("/apply", status_code=201)
def apply_import(payload: ImportApplyRequest, db: Session = Depends(get_db)):
    item = preview_store.get(payload.preview_token)
    if not item:
        raise HTTPException(410, detail={"code": "preview_expired", "message": "Preview expired; upload the file again"})
    rows, parse_errors, _ = parse_venue_csv(item["content"])
    preview = preview_venue_rows(db, rows, parse_errors)
    related_parsed: dict[str, list[dict[str, Any]]] = {}
    related_previews: dict[str, list[dict[str, Any]]] = {}
    incoming_venue_ids = {row.get("venue_external_id") for row in rows if row.get("venue_external_id")}
    for kind, content in item.get("related_contents", {}).items():
        child_rows, child_errors = parse_related_csv(kind, content)
        child_preview, parent_errors = preview_related_rows(db, kind, child_rows, incoming_venue_ids)
        related_parsed[kind] = child_rows
        related_previews[kind] = child_preview
        preview["errors"].extend(child_errors)
        preview["errors"].extend(parent_errors)
    if preview["errors"]:
        raise HTTPException(422, detail={"code": "batch_invalid", "errors": preview["errors"]})

    counts = {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0}
    applied_rows = []
    by_row = {entry["row"]: entry for entry in preview["rows"]}
    try:
        for source in rows:
            row_number = source.pop("_row")
            entry = by_row[row_number]
            action = entry["action"]
            resolution = payload.resolutions.get(str(row_number), {})
            values = {key: value for key, value in source.items() if value is not None}

            if action == "blocked_duplicate":
                choice = resolution.get("action")
                if choice == "skip":
                    counts["skipped"] += 1
                    entry["action"] = "skipped"
                    applied_rows.append(entry)
                    continue
                if choice == "map":
                    target_id = int(resolution.get("venue_id", "0"))
                    venue = find_venue(db, target_id)
                    incoming_external_id = values.pop("venue_external_id", None)
                    incoming_name = values.pop("venue_name", None)
                    for key, value in values.items():
                        setattr(venue, key, value)
                    if incoming_external_id:
                        db.add(
                            models.VenueAlias(
                                alias_external_id=incoming_external_id, venue_id=venue.id,
                                alias=incoming_name or venue.venue_name, alias_type="import_external_id",
                                notes="Mapped during reviewed venue import", active=True,
                            )
                        )
                    counts["updated"] += 1
                    entry["action"] = "updated_mapped"
                    applied_rows.append(entry)
                    continue
                if choice != "create_distinct" or not resolution.get("reason"):
                    raise HTTPException(409, detail={"code": "duplicate_unresolved", "row": row_number})
                action = "create"

            if action == "blocked_confidence":
                if resolution.get("action") == "skip":
                    counts["skipped"] += 1
                    entry["action"] = "skipped"
                    applied_rows.append(entry)
                    continue
                if resolution.get("action") != "override" or not resolution.get("reason"):
                    raise HTTPException(409, detail={"code": "confidence_unresolved", "row": row_number})
                action = "update"

            if action == "create":
                db.add(models.Venue(**VenueCreate(**values).model_dump()))
                counts["created"] += 1
            elif action == "update":
                venue = db.get(models.Venue, entry["venue_id"])
                for key, value in values.items():
                    if key != "venue_external_id":
                        setattr(venue, key, value)
                counts["updated"] += 1
            elif action == "unchanged":
                counts["unchanged"] += 1
            applied_rows.append(entry)

        db.flush()
        related_counts = {"created": 0, "updated": 0, "unchanged": 0}
        for kind, child_rows in related_parsed.items():
            contract = RELATED_IMPORTS[kind]
            model = contract["model"]
            external_key = contract["external_key"]
            for child_row in child_rows:
                values = {key: value for key, value in child_row.items() if not key.startswith("_")}
                venue_external_id = values.pop("venue_external_id")
                parent = db.query(models.Venue).filter(models.Venue.venue_external_id == venue_external_id).one()
                existing = db.query(model).filter(getattr(model, external_key) == values[external_key]).first()
                if existing:
                    changed = False
                    for key, value in values.items():
                        if getattr(existing, key) != value:
                            setattr(existing, key, value)
                            changed = True
                    if existing.venue_id != parent.id:
                        existing.venue_id = parent.id
                        changed = True
                    related_counts["updated" if changed else "unchanged"] += 1
                else:
                    db.add(model(venue_id=parent.id, **values))
                    related_counts["created"] += 1

        result = {"rows": applied_rows, "related": related_previews, "counts": counts, "related_counts": related_counts}
        batch = models.VenueImportBatch(
            schema_version=1, venues_filename=item["filename"], venues_sha256=item["sha256"], status="applied",
            related_filenames=json.dumps(item.get("related_filenames", {})),
            created_count=counts["created"], updated_count=counts["updated"], unchanged_count=counts["unchanged"],
            skipped_count=counts["skipped"], error_count=0, result_json=json.dumps(result, default=str),
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        preview_store.delete(payload.preview_token)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    return {"batch_id": batch.id, **result}


@import_router.get("")
def import_history(db: Session = Depends(get_db)):
    batches = db.query(models.VenueImportBatch).order_by(models.VenueImportBatch.id.desc()).all()
    return [
        {
            "id": batch.id, "filename": batch.venues_filename, "sha256": batch.venues_sha256, "status": batch.status,
            "created": batch.created_count, "updated": batch.updated_count, "unchanged": batch.unchanged_count,
            "skipped": batch.skipped_count, "errors": batch.error_count, "completed_at": batch.completed_at,
        }
        for batch in batches
    ]


@import_router.get("/export/{kind}.csv")
def export_related(kind: str, db: Session = Depends(get_db)):
    if kind not in RELATED_IMPORTS:
        raise HTTPException(404, detail={"code": "export_not_found", "message": "Unknown related export"})
    model = RELATED_IMPORTS[kind]["model"]
    external_key = RELATED_IMPORTS[kind]["external_key"]
    records = db.query(model).order_by(getattr(model, external_key)).all()
    return Response(
        content=related_csv(kind, records), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="venue-{kind}-export.csv"'},
    )


@import_router.get("/{batch_id}/report.csv")
def import_report(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(models.VenueImportBatch, batch_id)
    if not batch:
        raise HTTPException(404, detail={"code": "import_not_found", "message": "Import batch not found"})
    content = import_result_csv(json.loads(batch.result_json))
    return Response(
        content=content, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="venue-import-{batch.id}-report.csv"'},
    )
