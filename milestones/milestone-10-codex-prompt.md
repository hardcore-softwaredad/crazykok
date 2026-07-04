# Codex Prompt — Milestone 10 Venue Management

Read `docs/AI_INSTRUCTIONS.md`, `docs/DOMAIN_MODEL.md`,
`docs/VENUE_SCHEMA.md`, `docs/VENUE_FIELD_DICTIONARY.md`,
`docs/VENUE_IMPORT_EXPORT_RULES.md`, `docs/RESEARCH_GUIDELINES.md`,
`docs/VENUE_SCHEMA_SQL_DDL.md`, `docs/VENUE_ERD.mmd`,
`docs/DATA_COLLECTION_POLICY.md`, the venue CSV templates, and the accepted
ADRs before coding.

## Goal

Build complete venue management and a safe, human-reviewed batch import flow.
The expected research workflow is:

1. a person gives ChatGPT a canonical template and asks it to research a
   manageable batch of venues;
2. ChatGPT returns CSV data with sources, research dates, and confidence;
3. the person uploads the files to the application;
4. the application previews validation errors, duplicates, and proposed
   changes without writing anything; and
5. the person approves the valid changes for transactional import.

This milestone does not build or expose a research-agent API. ChatGPT does not
receive database access and does not write directly to the application.

## Intended Outcome

- Venues are reusable domain records referenced by opportunities.
- A person can create, search, edit, archive, and inspect venues in the UI.
- Contacts, aliases, documents, photos, and notes have first-class related
  records rather than being packed into free text.
- The repository provides a versioned, self-explanatory research import kit
  that can be attached to a ChatGPT research request.
- The application can preview and import venue research in batches.
- Imports preserve sources, confidence, unknown values, and research dates.
- Re-importing the same external IDs updates records rather than duplicating
  them, subject to explicit conflict rules.
- Likely duplicates never become new venue rows without human review.
- Opportunity history and venue statistics are derived from operational
  records; no venue statistics table is introduced.

## Phase 0 — Reconcile The Domain And Decisions

Do not add this feature on top of the current legacy `Event` model. Complete
the documented migration to `Opportunity`, including a nullable `venue_id`
foreign key, or make that migration the first slice of this milestone. Keep a
compatibility migration for existing data, but expose only opportunity and
operation language in new APIs and UI.

Before implementation, use the ADR authoring API described in
`docs/ADR_AUTHORING.md` to accept or supersede proposed ADR 0026 and record the
local attachment-storage decision.

Reconcile the venue documents into one canonical contract. In particular:

- implement every venue field in `templates/venues_import_template.csv` and
  `docs/VENUE_SCHEMA_SQL_DDL.md`; these currently agree on 111 importable
  venue fields, in addition to database-only ID and timestamp fields;
- implement every field in the contact, document, and alias templates and
  their corresponding related tables;
- use `docs/VENUE_FIELD_DICTIONARY.md` for field meaning and enum guidance, but
  do not treat its shorter explanatory tables as permission to omit fields
  present in the canonical template and SQL DDL;
- the database may contain an incomplete `discovered` venue, so unknown facts
  remain null rather than being filled with placeholder strings;
- `venue_external_id` and `venue_name` are always required;
- town, municipality, province, country, a source, and confidence are required
  before a venue can become `basic` or better;
- enum values, field types, CSV headers, API schemas, and database constraints
  come from one code-owned field registry;
- the JSON schema, CSV templates, import parser, exporter, and tests are
  generated from or checked against that registry.

Do not hand-maintain several independent lists of the venue fields.

## Data Model

### Venue

Replace the current minimal venue table with the full 111-field venue contract
shared by `templates/venues_import_template.csv` and
`docs/VENUE_SCHEMA_SQL_DDL.md`. This includes identity and classification,
address and geocoding, public and booking contacts, site characteristics,
access and parking, transport, utilities, safety, vendor suitability, fees,
accessibility, weather exposure, document URLs, provenance, research state,
and internal notes. Use a migration that preserves existing rows. Legacy rows
receive deterministic migration-only external IDs and the lowest
confidence/research status; do not invent missing geography.

Add unique `venue_external_id`, a unique slug when present, timestamps, archive
state, and indexes supporting name, postcode, town, municipality, category,
research status, confidence, active state, and duplicate detection.

Keep stable venue facts on Venue. Dates, pitch assignments, one-off access
instructions, fees, and outcomes for a particular opportunity or operation do
not belong there.

### Related Records

Implement `VenueContact`, `VenueAlias`, `VenueDocument`, `VenuePhoto`, and
`VenueNote` with foreign keys and explicit cascade/archive behavior.

- Contacts, aliases, and documents use stable external IDs for import.
- Documents support a source URL, a locally stored attachment, or both.
- Photos store caption, alt text, sort order, cover-photo flag, source URL,
  retrieval date, MIME type, size, and SHA-256 digest.
- Notes are appendable records with type, author/origin, and timestamp.
- Only one active cover photo is allowed per venue.

The existing venue source URLs, research dates, research status, and confidence
rating are the provenance contract for this milestone. Do not add field-level
evidence or research-agent audit tables unless a later workflow demonstrates
that record-level provenance is insufficient.

## Research Import Kit

Create a versioned import kit that a user can download from the venue import
screen or take directly from the repository. It contains:

- `venues_import_template.csv`;
- `venue_contacts_import_template.csv`;
- `venue_documents_import_template.csv`;
- `venue_aliases_import_template.csv`;
- one concise `RESEARCH_INSTRUCTIONS.md`;
- allowed enum values and confidence definitions; and
- a small valid example batch.

The instructions tell ChatGPT to:

- return CSV only in the supplied shape, preferably as downloadable files;
- keep the header unchanged and one logical record per row;
- use stable external IDs in the documented format;
- leave unknown values empty instead of guessing;
- use semicolons only for documented multi-value fields;
- include a primary source URL, source title, research date, verification date
  when applicable, research status, and confidence;
- prefer official venue, municipality, organiser, and document sources;
- separate venue-stable facts from opportunity-specific facts;
- avoid formulas or cells beginning with `=`, `+`, `-`, or `@`; and
- keep each requested batch to a documented manageable size.

The kit has a schema version. The importer reports an unsupported version
clearly rather than interpreting incompatible data.

## Import And Export

### Accepted Batch Shape

The import screen accepts a required venues CSV and optional contacts,
documents, and aliases CSVs for the same batch. Related rows reference their
parent by `venue_external_id`. Actual photo bytes are uploaded by a person;
research imports may provide photo-gallery or document URLs but do not fetch
remote content.

Accept UTF-8 CSV with a byte-order mark when present. Reject duplicate headers,
unknown headers, duplicate external IDs within a file, spreadsheet formulas,
oversized files, excessive rows, and malformed quoting with useful errors.

Imports may include the full canonical header set or a documented subset:

- missing columns mean “not supplied” and never modify existing values;
- empty cells mean unknown for a new record and “no change” on update;
- clearing an existing value is not supported by ordinary CSV import and must
  be done through the edit UI;
- export always emits the complete canonical header set.

This distinction prevents a sparse ChatGPT response from erasing previously
verified data.

### Preview Before Apply

Parsing and preview perform no database or attachment writes. Show one row per
venue with a proposed action:

- `create`;
- `update`;
- `unchanged`;
- `blocked_duplicate`;
- `blocked_validation`; or
- `skipped`.

For updates, show a field-level before/after diff. Show source and confidence
beside the changes. Errors and warnings include filename, row number, external
ID, field, stable error code, and explanation. Let the user download the full
preview report as CSV.

Preview tokens are short-lived server-side or cryptographically tied to the
uploaded content. Applying must parse and validate the files again so a stale
or altered preview cannot be applied accidentally.

### Apply Rules

- Validate the complete batch before writing.
- Apply venues and all related rows in one transaction.
- Upsert by stable external ID.
- Never replace a populated value with an empty cell.
- Never overwrite an A/B-confidence venue with a lower-confidence batch by
  default.
- For equal or stronger confidence, show every changed populated field and
  require user approval before apply.
- A lower-confidence override is available only as an explicit per-row choice
  with a recorded reason.
- Preserve the imported source, research dates, status, confidence, import
  filename, and import timestamp.
- Return an applied/unchanged/skipped/error count and a downloadable result
  report.
- Re-importing an unchanged batch is safe and creates no duplicate children.

Persist lightweight import history containing filenames, file digests, schema
version, start/end timestamps, counts, and the result report. Do not retain raw
uploaded CSV indefinitely unless the retention policy explicitly says so.

### Export

Export venues, contacts, documents, and aliases using exactly the canonical
headers and deterministic ordering. Protect exported CSV against spreadsheet
formula injection. A CSV export followed by previewed re-import must be a
no-op.

Support a **Research refresh export** from the venue overview. The user may
export all venues, the current filtered result set, or explicitly selected
venues. The export includes the stable `venue_external_id` and all current
research fields so it can be given to ChatGPT with instructions to preserve
every external ID and update only researched values.

When that CSV returns:

- an existing `venue_external_id` is always an update candidate, never a fuzzy
  duplicate;
- an unknown external ID is a create candidate and runs through duplicate
  detection;
- an existing external ID paired with a materially different name/location is
  blocked as a possible ID mismatch rather than blindly updating the row;
- unchanged rows are reported as no-ops; and
- changed rows show a before/after field diff before approval.

Contacts, documents, and aliases follow the same pattern using their own stable
external IDs and the parent `venue_external_id`. Exported values and IDs must
round-trip without normalization drift.

## Duplicate Detection

Use deterministic normalization shared by CRUD and import: Unicode
normalization, case folding, punctuation and whitespace normalization,
postcode normalization, and normalized aliases.

Score and explain at least these signals:

- exact or close normalized name/alias plus town and municipality;
- exact postcode and street address;
- coordinates within a documented small radius;
- matching authoritative website or map identity;
- conflicting geography that lowers the score.

External ID equality is an upsert match, not a fuzzy duplicate. A likely fuzzy
match blocks creation and asks the user to choose:

- map the incoming row to the existing venue;
- skip the row;
- confirm it is a distinct venue with a reason; or
- merge duplicate existing records through a separate reviewed flow.

Store explicit `not_duplicate` decisions so a known false positive does not
block every later batch. A merge moves related records and opportunities,
preserves the losing external ID as an alias/redirect, and archives rather
than deletes the losing venue.

## Venue API

Provide human-facing CRUD endpoints for venues and related resources. The
FastAPI application currently serves unprefixed routes behind an ingress that
adds `/api`; document public URLs with `/api` without creating `/api/api`
internally.

Add endpoints for:

- venue list/search/detail/create/update/archive/restore;
- contacts, aliases, documents, photos, and notes;
- duplicate preview and reviewed merge;
- import-kit download;
- batch preview, apply, history, and result-report download; and
- canonical CSV export.

Keep stable machine-readable validation and import error codes so the UI can
render actionable messages.

## Attachments And Photos

Store attachment bytes beneath one configured application-data root, outside
the frontend bundle and repository. Store metadata in SQLite. Use generated
storage names rather than client filenames, reject path traversal, calculate a
SHA-256 digest, cap file size, and allow only a documented MIME/type list.

Uploads are explicit multipart API calls. Remote URLs remain references and
are not fetched by this milestone. Stream downloads with safe content headers.
Test with a temporary storage root. Document backup, restore, orphan cleanup,
and the distinction between archiving metadata and deleting bytes.

## Human UI

### Venue Overview

Add a venue route and navigation entry. The overview supports text search,
active/archive state, town, municipality, category, research status,
confidence, missing coordinates, stale verification, and suspected duplicate
filters. Show visible completeness and provenance warnings.

### Import Workspace

Provide a guided flow:

1. download the research import kit;
2. select the venue and optional related CSV files;
3. preview parsing and validation;
4. review creates, diffs, duplicates, confidence conflicts, and warnings;
5. choose per-row resolutions where required;
6. apply the valid batch; and
7. download the result report.

The browser must retain the review state after a validation error and clearly
state that preview has not changed the database.

Also provide a **Refresh existing research** entry point that begins by
exporting selected or filtered venue records. Explain in the UI that the
returned CSV must preserve `venue_external_id`; this is what makes bulk updates
deterministic and prevents them from being mistaken for new duplicates.

### Venue Detail

Use a stable slug/external-ID URL and tabs:

1. **Overview** — identity, category, address, coordinates, map picker,
   logistics, utilities, accessibility, suitability, research state, source,
   and confidence.
2. **Contacts** — list and CRUD for venue contacts.
3. **Documents** — links, secure attachments, and metadata.
4. **Photos** — gallery, upload/reference form, cover selection, captions, and
   accessible alt text.
5. **Opportunities** — linked chronological history; no duplicated facts.
6. **Notes** — appendable research/internal notes with origin and date.
7. **Statistics** — read-only derived counts and outcome summaries. Label
   incomplete data and never persist aggregates on Venue.

The map picker edits coordinates and geocode precision/source. It must work as
plain latitude/longitude inputs if map tiles are unavailable, and it must not
silently geocode or move a marker based on an unverified guess.

### Field Types, Controls, And Validation

The backend's canonical field registry drives database/Pydantic types, CSV
parsing, nullability, constraints, enums, and API validation. It exposes
framework-neutral semantic metadata through the API, not React component or
widget choices. Each frontend owns a small adapter that maps those semantic
types to its native controls. Do not render every field as a text input.

Use appropriate controls by semantic type:

- short strings use text inputs and long notes/descriptions use text areas;
- controlled vocabularies use selects or radio groups populated from the
  canonical enum list;
- `yes`/`no`/`limited`/`unknown`-style fields use an enum control rather than a
  two-state checkbox, so uncertainty is not lost;
- true database booleans use checkboxes or switches;
- integers and decimals use numeric inputs with suitable bounds and steps;
- dates use date inputs and ISO serialization;
- URLs, email addresses, and phone numbers use their semantic input types;
- latitude and longitude use bounded decimal inputs paired with the map;
- semicolon-separated multi-value fields use a tag/list editor in the UI and
  serialize canonically for CSV; and
- local attachments use file controls while remote document/photo locations
  use URL inputs.

Group the venue fields into the same domain sections used by the schema rather
than showing one enormous form. Validate immediately in the UI and show field-
specific messages, but repeat every validation rule on the backend; client-side
validation is usability, not a trust boundary.

The internal database ID, timestamps, import-history metadata, and derived
statistics are read-only. `venue_external_id` is entered or generated at
creation/import and is read-only afterward through ordinary CRUD because it is
the stable import key. Provide a separately reviewed correction workflow if an
external ID ever needs to change. Slugs may be regenerated only through an
explicit action that handles existing links safely.

## Delivery Slices

Implement in this order, keeping each slice deployable:

1. **Contract and migration:** ADRs, canonical field registry, Opportunity
   relationship, venue/related/import-history models, Alembic migration, and
   migration tests.
2. **Venue CRUD API:** schemas, list/detail/search, archive/restore, related
   resources, duplicate service, and OpenAPI examples.
3. **Import engine:** research kit, secure CSV parser, preview model,
   validation, diffs, confidence rules, duplicate resolutions, transactional
   apply, import history, reports, and deterministic export.
4. **Files:** document/photo metadata, secure local upload/download, and
   storage lifecycle documentation.
5. **Venue UI:** overview, detail tabs, related CRUD, map fallback, gallery,
   opportunity history, notes, and derived statistics.
6. **Import UI:** upload, preview, diff/conflict review, apply, history, and
   report download.
7. **Hardening:** accessibility, integration tests, migration rehearsal on a
   database copy, backup/restore rehearsal, and user workflow documentation.

## Verification

### Backend

- Migration upgrade/downgrade and legacy-row preservation.
- Venue and related-record create/read/update/archive behavior.
- Enum, coordinate, URL, status-dependent completeness, and null validation.
- Import-kit templates match the canonical field registry.
- Full and sparse CSV parsing, BOM handling, formula protection, malformed
  input errors, batch limits, and related-parent validation.
- Preview performs zero writes and reports field-level diffs.
- Apply is atomic; any invalid unresolved row prevents writes.
- Missing columns and empty update cells do not erase existing values.
- Lower-confidence overwrites require explicit reviewed overrides.
- External-ID re-import and child-record upsert create no duplicates.
- Each fuzzy duplicate signal, false-positive suppression, and merge
  referential integrity.
- Export header parity, deterministic order, formula protection, and no-op
  export/re-import round trip.
- Upload size/type/path checks, digesting, safe download, and cleanup behavior.
- Opportunity history and statistics are derived and correctly scoped.

### Frontend

- Venue overview filters and URL-backed state.
- Create/edit validation and duplicate review.
- Import file selection, zero-write preview, field diffs, row resolutions,
  confidence conflicts, apply summary, and report download.
- Review state survives errors without silently applying data.
- Keyboard-accessible tabs, forms, dialogs, map fallback, and gallery.
- Source, confidence, unknown, and stale states are visible.
- Contacts/documents/photos/notes CRUD and opportunity links.

### End To End

Prove one representative workflow:

1. download the research kit;
2. preview a batch containing a new venue, an external-ID update, a sparse
   update, and a fuzzy duplicate;
3. confirm the database is unchanged after preview;
4. resolve the duplicate and apply the batch;
5. re-import it and confirm there are no duplicate records or changes;
6. attach a document and photo and link an opportunity;
7. inspect the source, confidence, history, and derived statistics in the UI;
8. export the venue and preview the export as a no-op import.

## Completion Criteria

Milestone 10 is complete when all roadmap deliverables work and a person can
reliably move a batch researched by ChatGPT from the canonical templates,
through a zero-write review, into venue records without losing provenance or
creating silent duplicates.

## Non-Goals

- a research agent, agent-specific API, autonomous browsing, or scraping;
- direct ChatGPT/database integration;
- downloading remote documents or photos automatically;
- automatic geocoding without a separately reviewed provider decision;
- field-level evidence tables before a demonstrated need;
- venue-level outcome or statistics tables;
- copying opportunity/operation-specific facts onto venues;
- authentication, cloud storage, commerce, inventory, or route optimization.
