# Codex Prompt — Implement Comprehensive Venue Schema

You are implementing the venue schema for Drenthe Opportunities & Engagements.

## Read First

- docs/VENUE_SCHEMA.md
- docs/VENUE_FIELD_DICTIONARY.md
- docs/VENUE_IMPORT_EXPORT_RULES.md
- docs/VENUE_SCHEMA_SQL_DDL.md
- docs/PARKING_LOT.md
- docs/adr/

## Goal

Implement a comprehensive venue schema that supports reliable CSV import/export and future deep research.

## Required Deliverables

1. SQLAlchemy models:
   - Venue
   - VenueContact
   - VenueDocument
   - VenueAlias

2. Alembic migration for these tables.

3. Pydantic schemas:
   - create/update/read DTOs
   - CSV import row schemas if project has import layer started

4. CRUD endpoints:
   - `/api/venues`
   - `/api/venues/{id}`
   - related contact/document/alias endpoints if practical

5. CSV import/export:
   - import `venues_import_template.csv`
   - export all venues with the same canonical headers
   - upsert by `venue_external_id`

6. Validation:
   - required fields
   - enum-like fields
   - duplicate detection by external ID
   - duplicate warning by normalized venue_name + town + municipality

7. Tests:
   - create venue
   - update venue
   - import venue CSV
   - duplicate external ID handling
   - export venue CSV

## Important Rules

- Do not add VenueStatistics or aggregate analytics tables.
- Do not implement commerce/inventory/barcode/order/shipping features.
- Unknown values must remain unknown/null.
- Do not overwrite high-confidence data with lower-confidence imported data unless explicitly coded as an override option.
- Use `venue_external_id` as the stable import/export key.
