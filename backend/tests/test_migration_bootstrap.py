import pytest
from sqlalchemy import create_engine, text

from backend.app.migration_bootstrap import (
    INITIAL_REVISION,
    RESEARCH_FIELDS_REVISION,
    bootstrap_unversioned_schema,
)


def tables(connection, with_research_fields: bool = False):
    extra = (
        ", application_deadline DATE, application_status VARCHAR(50), source_url VARCHAR(500), notes TEXT"
        if with_research_fields
        else ""
    )
    connection.execute(text(f"CREATE TABLE events (id INTEGER PRIMARY KEY, name VARCHAR(255){extra})"))
    connection.execute(text("CREATE TABLE organizers (id INTEGER PRIMARY KEY, name VARCHAR(255))"))
    connection.execute(text("CREATE TABLE venues (id INTEGER PRIMARY KEY, name VARCHAR(255))"))


@pytest.mark.parametrize(
    ("with_research_fields", "revision"),
    [(False, INITIAL_REVISION), (True, RESEARCH_FIELDS_REVISION)],
)
def test_bootstrap_stamps_known_legacy_schema(with_research_fields, revision):
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        tables(connection, with_research_fields)
        assert bootstrap_unversioned_schema(connection) == revision
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == revision


def test_bootstrap_leaves_empty_and_versioned_databases_alone():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        assert bootstrap_unversioned_schema(connection) is None
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        assert bootstrap_unversioned_schema(connection) is None


def test_bootstrap_recovers_an_empty_version_table_left_by_failed_alembic_run():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        tables(connection, with_research_fields=True)
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        assert bootstrap_unversioned_schema(connection) == RESEARCH_FIELDS_REVISION
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == RESEARCH_FIELDS_REVISION


def test_bootstrap_rejects_partial_schema():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE events (id INTEGER PRIMARY KEY, application_status VARCHAR(50))"))
        connection.execute(text("CREATE TABLE organizers (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE venues (id INTEGER PRIMARY KEY)"))
        with pytest.raises(RuntimeError, match="partially migrated"):
            bootstrap_unversioned_schema(connection)
