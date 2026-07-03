# Milestone Roadmap

## Milestone 01 — Foundation Documentation

Status: prepared

Includes domain model, architecture, ADRs, and milestone prompts.

## Milestone 02 — Backend Skeleton

Implement the updated opportunity/operation domain model.

Deliverables:

- FastAPI app
- SQLite config
- SQLAlchemy models
- Alembic migrations
- CRUD services
- search endpoint
- initial tests

## Milestone 03 — Frontend Skeleton

Deliverables:

- React + TypeScript app
- opportunity list
- opportunity detail
- application status UI
- operation status UI
- filters
- API integration

## Milestone 04 — Import/Export

Deliverables:

- CSV import/export for opportunities
- duplicate detection
- validation
- source preservation
- confidence preservation

## Milestone 05 — Map & Calendar Planning Views

Deliverables:

- Leaflet map view
- FullCalendar planning view
- clickable opportunity markers/events
- application deadline display
- committed operation display

## Milestone 06 — Calendar Feeds & Operations Calendar

Deliverables:

- read-only ICS feeds
- subscribable Apple/Google/Outlook calendar feeds
- all opportunities feed
- filtered opportunities feeds
- committed operations feed
- application deadlines feed
- operation tasks feed

## Milestone 07 — Operations & Outcomes

Deliverables:

- operation planning
- setup/teardown details
- staffing/equipment notes
- operation outcomes
- year-over-year comparisons
- revenue/cost/profit tracking

## Milestone 08 — HATEOS API Navigation

Deliverables:

- HATEOS scaffolding to api results
- links to navigate via the api (next, previous, related object records)

## Milestone 09 — Decision Log

Deliverables:

- web accessible UI for ADRs
- navigation between recods (next, previous)
- overview of all adrs linking to their markdown view
- filter & search by tags, categories, keywords, search hit
- expose on new subdomain 'docs.crazykok'