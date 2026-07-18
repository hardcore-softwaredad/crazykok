import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .adr_service import (
    CATEGORIES,
    REQUIRED_SECTIONS,
    OPTIONAL_SECTIONS,
    SCHEMA_VERSION,
    STATUSES,
    AdrError,
    AdrProposal,
    AdrService,
    AdrUpdateProposal,
)


router = APIRouter(
    prefix="/internal/adrs",
    tags=["internal-adr-authoring"],
    include_in_schema=False,
)


def authoring_enabled() -> bool:
    configured = os.getenv("ADR_AUTHORING_ENABLED")
    if configured is not None:
        return configured.lower() in {"1", "true", "yes"}
    return os.getenv("APP_ENV", "development") == "development"


def service() -> AdrService:
    if not authoring_enabled():
        raise HTTPException(status_code=404, detail="Not found")
    default_directory = Path(__file__).resolve().parents[2] / "docs" / "adr"
    return AdrService(Path(os.getenv("ADR_DIRECTORY", default_directory)))


def run(operation):
    try:
        return operation()
    except AdrError as error:
        status = 404 if error.code == "not_found" else 409 if error.code == "stale_source" else 422
        raise HTTPException(status_code=status, detail=error.payload()) from error


@router.get("/schema")
def get_schema():
    service()
    return {
        "schema_version": SCHEMA_VERSION,
        "statuses": STATUSES,
        "categories": CATEGORIES,
        "required_sections": REQUIRED_SECTIONS,
        "optional_sections": OPTIONAL_SECTIONS,
        "tag_format": "lower-case kebab-case",
        "id_policy": "server allocated, four digits, immutable, never reused",
    }


@router.get("")
def list_adrs():
    return run(lambda: service().list())


@router.get("/{record_id}")
def get_adr(record_id: str):
    return run(lambda: service().get(record_id))


@router.post("/validate")
def validate_adr(proposal: AdrProposal, record_id: str = Query(default="0000", pattern=r"^\d{4}$")):
    return run(lambda: service().validate(proposal, record_id))


@router.post("", status_code=201)
def create_adr(proposal: AdrProposal):
    docs_origin = os.getenv("DOCS_ORIGIN", "https://docs.crazykok.local")
    record = run(lambda: service().create(proposal))
    result = record.model_dump(mode="json")
    result["docs_url"] = f"{docs_origin.rstrip('/')}/adr/{record.slug}"
    return result


@router.put("/{record_id}")
def update_adr(record_id: str, proposal: AdrUpdateProposal):
    return run(lambda: service().update(record_id, proposal))
