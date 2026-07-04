from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from .venue_registry import VENUE_FIELDS


class VenueValidationBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    @model_validator(mode="after")
    def validate_registered_values(self):
        values = self.model_dump(exclude_unset=True)
        for field in VENUE_FIELDS:
            value = values.get(field.name)
            if value is None or value == "":
                continue
            if field.enum and value not in field.enum:
                raise ValueError(f"{field.name} must be one of: {', '.join(field.enum)}")
            if field.value_type == "url":
                parsed = urlparse(str(value))
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    raise ValueError(f"{field.name} must be an http(s) URL")
            if field.value_type == "email" and ("@" not in str(value) or str(value).startswith("@")):
                raise ValueError(f"{field.name} must be an email address")
        latitude = values.get("latitude")
        longitude = values.get("longitude")
        if latitude is not None and not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if longitude is not None and not -180 <= longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        external_id = values.get("venue_external_id")
        if external_id and not re.fullmatch(r"VEN-[A-Z0-9]+(?:-[A-Z0-9]+)+", external_id):
            raise ValueError("venue_external_id must use the VEN-COUNTRY-...-SLUG format")
        postcode = values.get("postcode")
        country = values.get("country")
        if postcode and country in {"Netherlands", "NL"} and not re.fullmatch(r"\d{4}\s?[A-Za-z]{2}", postcode):
            raise ValueError("postcode must use the Dutch 1234 AB format")
        return self


def _create_fields() -> dict[str, tuple[Any, Any]]:
    result: dict[str, tuple[Any, Any]] = {}
    for field in VENUE_FIELDS:
        value_type = field.python_type
        if field.name in {"venue_external_id", "venue_name"}:
            result[field.name] = (value_type, Field(min_length=1, max_length=255))
        elif field.name == "active":
            result[field.name] = (bool, True)
        elif field.name == "research_status":
            result[field.name] = (str | None, "discovered")
        elif field.name == "confidence_rating":
            result[field.name] = (str | None, "E")
        else:
            result[field.name] = (value_type | None, None)
    return result


def _update_fields() -> dict[str, tuple[Any, Any]]:
    return {field.name: (field.python_type | None, None) for field in VENUE_FIELDS}


VenueCreate = create_model("VenueCreate", __base__=VenueValidationBase, **_create_fields())
VenueUpdate = create_model("VenueUpdate", __base__=VenueValidationBase, **_update_fields())
VenueRead = create_model(
    "VenueRead",
    __base__=VenueValidationBase,
    id=(int, ...),
    created_at=(datetime, ...),
    updated_at=(datetime, ...),
    **_create_fields(),
)


class DuplicateCandidate(BaseModel):
    id: int
    venue_external_id: str
    venue_name: str
    score: float
    signals: list[str]


class DuplicateCheckRequest(BaseModel):
    venue_external_id: str | None = None
    venue_name: str = Field(min_length=1)
    street_address: str | None = None
    postcode: str | None = None
    town: str | None = None
    municipality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    website_url: str | None = None


class VenueContactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    contact_external_id: str
    contact_type: str | None = None
    name: str | None = None
    role_title: str | None = None
    organization: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    website_url: str | None = None
    notes: str | None = None
    source_url: str | None = None
    last_verified_at: date | None = None
    confidence_rating: str | None = "D"
    active: bool = True


class VenueContactCreate(VenueContactBase):
    pass


class VenueContactRead(VenueContactBase):
    id: int
    venue_id: int
    created_at: datetime
    updated_at: datetime


class VenueAliasBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    alias_external_id: str
    alias: str
    alias_type: str | None = None
    source_url: str | None = None
    notes: str | None = None
    active: bool = True


class VenueAliasCreate(VenueAliasBase):
    pass


class VenueAliasRead(VenueAliasBase):
    id: int
    venue_id: int
    created_at: datetime
    updated_at: datetime


class VenueDocumentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    document_external_id: str
    document_type: str
    title: str
    url: str | None = None
    description: str | None = None
    source_url: str | None = None
    retrieved_at: date | None = None
    last_verified_at: date | None = None
    confidence_rating: str | None = "D"
    notes: str | None = None
    active: bool = True


class VenueDocumentCreate(VenueDocumentBase):
    pass


class VenueDocumentRead(VenueDocumentBase):
    id: int
    venue_id: int
    local_path: str | None = None
    original_filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    created_at: datetime
    updated_at: datetime


class VenuePhotoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    caption: str | None = None
    alt_text: str
    source_url: str | None = None
    retrieved_at: date | None = None
    sort_order: int = 0
    is_cover: bool = False
    active: bool = True


class VenuePhotoRead(VenuePhotoCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    venue_id: int
    local_path: str | None = None
    original_filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    created_at: datetime
    updated_at: datetime


class VenueNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note_type: str = "internal"
    body: str = Field(min_length=1)
    origin: str = "user"


class VenueNoteRead(VenueNoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    venue_id: int
    created_at: datetime
    updated_at: datetime
