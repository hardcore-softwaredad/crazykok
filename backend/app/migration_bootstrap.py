from __future__ import annotations

from sqlalchemy import Connection, inspect, text


INITIAL_REVISION = "52d7c0a57cb7"
RESEARCH_FIELDS_REVISION = "9a7f9e8b6d21"
VENUE_MANAGEMENT_REVISION = "c41a9d738f10"

LEGACY_TABLES = {"events", "organizers", "venues"}
CURRENT_TABLES = {
    "opportunities",
    "organizers",
    "venues",
    "venue_contacts",
    "venue_documents",
    "venue_aliases",
    "venue_photos",
    "venue_notes",
    "venue_import_batches",
    "venue_not_duplicate_decisions",
}
RESEARCH_COLUMNS = {"application_deadline", "application_status", "source_url", "notes"}


def _stamp(connection: Connection, revision: str, version_table_exists: bool) -> str:
    if not version_table_exists:
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
        )
    connection.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": revision},
    )
    return revision


def bootstrap_unversioned_schema(connection: Connection) -> str | None:
    """Stamp a recognized create_all-era schema before normal Alembic upgrades.

    Early development builds created tables directly from SQLAlchemy metadata.
    Those databases contain valid user data but no ``alembic_version`` table.
    Only exact, known schema generations are stamped; partial or mixed schemas
    fail closed instead of guessing or dropping data.
    """

    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    version_table_exists = "alembic_version" in tables
    if version_table_exists:
        existing_revision = connection.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar_one_or_none()
        if existing_revision is not None:
            return None

    application_tables = tables & (LEGACY_TABLES | CURRENT_TABLES)
    if not application_tables:
        return None

    if "events" in tables and "opportunities" in tables:
        raise RuntimeError("Refusing to bootstrap a mixed events/opportunities schema")

    if "opportunities" in tables:
        missing = CURRENT_TABLES - tables
        opportunity_columns = {column["name"] for column in inspector.get_columns("opportunities")}
        venue_columns = {column["name"] for column in inspector.get_columns("venues")}
        if missing or "venue_id" not in opportunity_columns or "venue_external_id" not in venue_columns:
            raise RuntimeError(
                "Refusing to stamp an incomplete current schema; missing tables: "
                + ", ".join(sorted(missing))
            )
        return _stamp(connection, VENUE_MANAGEMENT_REVISION, version_table_exists)

    missing = LEGACY_TABLES - tables
    if missing:
        raise RuntimeError(
            "Refusing to stamp an incomplete legacy schema; missing tables: "
            + ", ".join(sorted(missing))
        )

    event_columns = {column["name"] for column in inspector.get_columns("events")}
    present_research_columns = event_columns & RESEARCH_COLUMNS
    if present_research_columns == RESEARCH_COLUMNS:
        return _stamp(connection, RESEARCH_FIELDS_REVISION, version_table_exists)
    if not present_research_columns:
        return _stamp(connection, INITIAL_REVISION, version_table_exists)
    raise RuntimeError(
        "Refusing to stamp a partially migrated events schema; research columns present: "
        + ", ".join(sorted(present_research_columns))
    )
