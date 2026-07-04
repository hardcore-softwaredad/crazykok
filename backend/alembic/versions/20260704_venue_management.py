"""venue management and opportunity venue relationship

Revision ID: c41a9d738f10
Revises: 9a7f9e8b6d21
Create Date: 2026-07-04 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

from backend.app.venue_registry import VENUE_FIELDS


revision = "c41a9d738f10"
down_revision = "9a7f9e8b6d21"
branch_labels = None
depends_on = None


def venue_columns():
    columns = [sa.Column("id", sa.Integer(), primary_key=True)]
    for field in VENUE_FIELDS:
        if field.value_type == "integer":
            column_type = sa.Integer()
        elif field.value_type == "decimal":
            column_type = sa.Float()
        elif field.value_type == "date":
            column_type = sa.Date()
        elif field.value_type == "boolean":
            column_type = sa.Boolean()
        elif field.name in {"venue_external_id", "venue_name", "venue_slug", "postcode", "town", "municipality"}:
            column_type = sa.String(255)
        else:
            column_type = sa.Text()
        kwargs = {"nullable": field.name not in {"venue_external_id", "venue_name", "active"}}
        if field.name == "active":
            kwargs["server_default"] = sa.true()
        elif field.name == "research_status":
            kwargs["server_default"] = "discovered"
        elif field.name == "confidence_rating":
            kwargs["server_default"] = "E"
        columns.append(sa.Column(field.name, column_type, **kwargs))
    columns.extend(
        [
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("venue_external_id"),
            sa.UniqueConstraint("venue_slug"),
        ]
    )
    return columns


def upgrade() -> None:
    op.rename_table("venues", "venues_legacy")
    op.create_table("venues", *venue_columns())
    op.execute(
        sa.text(
            """
            INSERT INTO venues (
                id, venue_external_id, venue_name, street_address, town,
                research_status, confidence_rating, internal_notes, active,
                created_at, updated_at
            )
            SELECT
                id, printf('VEN-LEGACY-%06d', id), name, address, city,
                'discovered', 'E', notes, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM venues_legacy
            """
        )
    )
    op.drop_table("venues_legacy")

    for field in (
        "venue_external_id", "venue_name", "postcode", "town", "municipality", "venue_category_primary",
        "research_status", "confidence_rating", "active",
    ):
        op.create_index(f"ix_venues_{field}", "venues", [field])

    op.create_table(
        "venue_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_external_id", sa.String(255), nullable=False, unique=True),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_type", sa.String(100)), sa.Column("name", sa.String(255)),
        sa.Column("role_title", sa.String(255)), sa.Column("organization", sa.String(255)),
        sa.Column("email", sa.String(255)), sa.Column("phone", sa.String(100)), sa.Column("mobile", sa.String(100)),
        sa.Column("website_url", sa.Text()), sa.Column("notes", sa.Text()), sa.Column("source_url", sa.Text()),
        sa.Column("last_verified_at", sa.Date()), sa.Column("confidence_rating", sa.String(1), server_default="D"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_venue_contacts_venue_id", "venue_contacts", ["venue_id"])
    op.create_index("ix_venue_contacts_external_id", "venue_contacts", ["contact_external_id"])

    op.create_table(
        "venue_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_external_id", sa.String(255), nullable=False, unique=True),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=False), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("url", sa.Text()), sa.Column("local_path", sa.Text()), sa.Column("original_filename", sa.String(255)),
        sa.Column("mime_type", sa.String(150)), sa.Column("size_bytes", sa.Integer()), sa.Column("sha256", sa.String(64)),
        sa.Column("description", sa.Text()), sa.Column("source_url", sa.Text()), sa.Column("retrieved_at", sa.Date()),
        sa.Column("last_verified_at", sa.Date()), sa.Column("confidence_rating", sa.String(1), server_default="D"),
        sa.Column("notes", sa.Text()), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_venue_documents_venue_id", "venue_documents", ["venue_id"])
    op.create_index("ix_venue_documents_external_id", "venue_documents", ["document_external_id"])

    op.create_table(
        "venue_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alias_external_id", sa.String(255), nullable=False, unique=True),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(255), nullable=False), sa.Column("alias_type", sa.String(100)),
        sa.Column("source_url", sa.Text()), sa.Column("notes", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_venue_aliases_venue_id", "venue_aliases", ["venue_id"])
    op.create_index("ix_venue_aliases_external_id", "venue_aliases", ["alias_external_id"])
    op.create_index("ix_venue_aliases_alias", "venue_aliases", ["alias"])

    op.create_table(
        "venue_photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255)), sa.Column("caption", sa.Text()),
        sa.Column("alt_text", sa.String(500), nullable=False), sa.Column("source_url", sa.Text()),
        sa.Column("local_path", sa.Text()), sa.Column("original_filename", sa.String(255)),
        sa.Column("mime_type", sa.String(150)), sa.Column("size_bytes", sa.Integer()), sa.Column("sha256", sa.String(64)),
        sa.Column("retrieved_at", sa.Date()), sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("venue_id", "sort_order", name="uq_venue_photo_sort_order"),
    )
    op.create_index("ix_venue_photos_venue_id", "venue_photos", ["venue_id"])

    op.create_table(
        "venue_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note_type", sa.String(100), nullable=False, server_default="internal"),
        sa.Column("body", sa.Text(), nullable=False), sa.Column("origin", sa.String(255), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_venue_notes_venue_id", "venue_notes", ["venue_id"])

    op.create_table(
        "venue_import_batches",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("venues_filename", sa.String(255), nullable=False),
        sa.Column("venues_sha256", sa.String(64), nullable=False), sa.Column("related_filenames", sa.Text()),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unchanged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_venue_import_batches_sha", "venue_import_batches", ["venues_sha256"])

    op.create_table(
        "venue_not_duplicate_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("venue_id_a", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("venue_id_b", sa.Integer(), sa.ForeignKey("venues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("venue_id_a", "venue_id_b", name="uq_not_duplicate_pair"),
    )

    op.rename_table("events", "opportunities")
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.add_column(sa.Column("venue_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_opportunities_venue_id", "venues", ["venue_id"], ["id"], ondelete="SET NULL")
        batch_op.create_index("ix_opportunities_venue_id", ["venue_id"])


def downgrade() -> None:
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_index("ix_opportunities_venue_id")
        batch_op.drop_constraint("fk_opportunities_venue_id", type_="foreignkey")
        batch_op.drop_column("venue_id")
    op.rename_table("opportunities", "events")

    for table in (
        "venue_not_duplicate_decisions", "venue_import_batches", "venue_notes", "venue_photos",
        "venue_aliases", "venue_documents", "venue_contacts",
    ):
        op.drop_table(table)

    op.rename_table("venues", "venues_full")
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("address", sa.String(255)), sa.Column("city", sa.String(100)),
        sa.Column("capacity", sa.Integer()), sa.Column("notes", sa.Text()),
    )
    op.execute(
        sa.text(
            "INSERT INTO venues (id, name, address, city, notes) "
            "SELECT id, venue_name, street_address, town, internal_notes FROM venues_full"
        )
    )
    op.drop_table("venues_full")
