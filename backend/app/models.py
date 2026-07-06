from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base
from .venue_registry import VENUE_FIELDS


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    event_date = Column(Date, nullable=True)
    application_deadline = Column(Date, nullable=True)
    organizer = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    application_status = Column(String(50), nullable=False, default="researching")
    source_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    expected_revenue = Column(Integer, nullable=True)
    expected_attendance = Column(Integer, nullable=True)
    profit_score = Column(Float, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    venue = relationship("Venue", back_populates="opportunities")
    operations = relationship("Operation", back_populates="opportunity", cascade="all, delete-orphan")


# Temporary source-compatibility alias while the existing opportunity UI is migrated.
Event = Opportunity


class Organizer(Base):
    __tablename__ = "organizers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    contact_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)


class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = Column(String(50), nullable=False, default="committed", index=True)
    commitment_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    opportunity = relationship("Opportunity", back_populates="operations")


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    contacts = relationship("VenueContact", back_populates="venue", cascade="all, delete-orphan")
    documents = relationship("VenueDocument", back_populates="venue", cascade="all, delete-orphan")
    aliases = relationship("VenueAlias", back_populates="venue", cascade="all, delete-orphan")
    photos = relationship("VenuePhoto", back_populates="venue", cascade="all, delete-orphan")
    venue_notes = relationship("VenueNote", back_populates="venue", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="venue")


def _venue_column(field):
    kwargs = {"nullable": field.name not in {"venue_external_id", "venue_name", "active"}}
    if field.name == "active":
        kwargs["default"] = True
    elif field.name == "research_status":
        kwargs["default"] = "discovered"
    elif field.name == "confidence_rating":
        kwargs["default"] = "E"

    if field.value_type == "integer":
        column_type = Integer
    elif field.value_type == "decimal":
        column_type = Float
    elif field.value_type == "date":
        column_type = Date
    elif field.value_type == "boolean":
        column_type = Boolean
    elif field.name in {"venue_external_id", "venue_name", "venue_slug", "postcode", "town", "municipality"}:
        column_type = String(255)
    else:
        column_type = Text

    unique = field.name in {"venue_external_id", "venue_slug"}
    index = field.name in {
        "venue_external_id", "venue_name", "postcode", "town", "municipality", "venue_category_primary",
        "research_status", "confidence_rating", "active",
    }
    return Column(column_type, unique=unique, index=index, **kwargs)


for _field in VENUE_FIELDS:
    setattr(Venue, _field.name, _venue_column(_field))


class VenueContact(Base):
    __tablename__ = "venue_contacts"

    id = Column(Integer, primary_key=True)
    contact_external_id = Column(String(255), nullable=False, unique=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type = Column(String(100))
    name = Column(String(255))
    role_title = Column(String(255))
    organization = Column(String(255))
    email = Column(String(255))
    phone = Column(String(100))
    mobile = Column(String(100))
    website_url = Column(Text)
    notes = Column(Text)
    source_url = Column(Text)
    last_verified_at = Column(Date)
    confidence_rating = Column(String(1), default="D")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    venue = relationship("Venue", back_populates="contacts")


class VenueDocument(Base):
    __tablename__ = "venue_documents"

    id = Column(Integer, primary_key=True)
    document_external_id = Column(String(255), nullable=False, unique=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(Text)
    local_path = Column(Text)
    original_filename = Column(String(255))
    mime_type = Column(String(150))
    size_bytes = Column(Integer)
    sha256 = Column(String(64))
    description = Column(Text)
    source_url = Column(Text)
    retrieved_at = Column(Date)
    last_verified_at = Column(Date)
    confidence_rating = Column(String(1), default="D")
    notes = Column(Text)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    venue = relationship("Venue", back_populates="documents")


class VenueAlias(Base):
    __tablename__ = "venue_aliases"

    id = Column(Integer, primary_key=True)
    alias_external_id = Column(String(255), nullable=False, unique=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    alias = Column(String(255), nullable=False, index=True)
    alias_type = Column(String(100))
    source_url = Column(Text)
    notes = Column(Text)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    venue = relationship("Venue", back_populates="aliases")


class VenuePhoto(Base):
    __tablename__ = "venue_photos"
    __table_args__ = (UniqueConstraint("venue_id", "sort_order", name="uq_venue_photo_sort_order"),)

    id = Column(Integer, primary_key=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255))
    caption = Column(Text)
    alt_text = Column(String(500), nullable=False)
    source_url = Column(Text)
    local_path = Column(Text)
    original_filename = Column(String(255))
    mime_type = Column(String(150))
    size_bytes = Column(Integer)
    sha256 = Column(String(64))
    retrieved_at = Column(Date)
    sort_order = Column(Integer, nullable=False, default=0)
    is_cover = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    venue = relationship("Venue", back_populates="photos")


class VenueNote(Base):
    __tablename__ = "venue_notes"

    id = Column(Integer, primary_key=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    note_type = Column(String(100), nullable=False, default="internal")
    body = Column(Text, nullable=False)
    origin = Column(String(255), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    venue = relationship("Venue", back_populates="venue_notes")


class VenueImportBatch(Base):
    __tablename__ = "venue_import_batches"

    id = Column(Integer, primary_key=True)
    schema_version = Column(Integer, nullable=False, default=1)
    venues_filename = Column(String(255), nullable=False)
    venues_sha256 = Column(String(64), nullable=False, index=True)
    related_filenames = Column(Text)
    status = Column(String(50), nullable=False, default="applied")
    created_count = Column(Integer, nullable=False, default=0)
    updated_count = Column(Integer, nullable=False, default=0)
    unchanged_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    result_json = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class VenueNotDuplicate(Base):
    __tablename__ = "venue_not_duplicate_decisions"
    __table_args__ = (UniqueConstraint("venue_id_a", "venue_id_b", name="uq_not_duplicate_pair"),)

    id = Column(Integer, primary_key=True)
    venue_id_a = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    venue_id_b = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
