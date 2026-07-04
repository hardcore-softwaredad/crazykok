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

## Milestone 08 — HATEOAS API Navigation

Status: complete

Deliverables:

- HATEOAS scaffolding for API results
- links to navigate via the API (next, previous, related resource records)

Implementation plan: `milestones/milestone-08-codex-prompt.md`.

## Milestone 09 — Decision Log

Status: complete

Deliverables:

- web-accessible, read-only UI generated from the repository ADRs
- previous/next navigation between records
- overview of all ADRs linking to their rendered Markdown view
- filters and search by status, tags, category, keywords, and search-hit excerpt
- dedicated configurable docs subdomain (`docs.crazykok.local` locally and
  `docs.crazykok.com` in production)
- validated ADR metadata with unique identifiers, categories, and tags
- local-only filesystem-backed authoring API that allocates immutable IDs,
  validates structured proposals, and never commits to Git
- frontend, indexer, routing, and deployment tests

Implementation plan: `milestones/milestone-09-codex-prompt.md`.

## Milestone 10 – Venue Management

Status: complete

Deliverables:

- Full venue data model
- Venue CRUD screens
- Contact management
- Document attachment support
- Photo gallery
- Map location picker
- Duplicate detection (to avoid creating the same venue twice)
- Opportunity history for each venue
- Venue detail page with tabs (Overview, Contacts, Documents, Photos, Opportunities, Notes, Statistics)

Implementation plan: `milestones/milestone-10-codex-prompt.md`.

## Milestone 11 – API Docs

Deliverables:

- Document the apis with an open standard like openAPI / swagger
- Add a docker container for redoc to render the spec, redoc.host subdomain
- Update docs. subdomain to be a portal to both decision log and redoc
- Add contract tests to compare against the spec so that changes to entities will fail on non backward compatible changes.
- Modify redoc UI to surface actionable buttons for leveraging HATEOAS links.
- Update agent instructions to verify documentation is up to date after code changes.

## Milestone 12 – End to End UI Testing

Deliverables:

- Incorporate playwright into the project
- Add the core UI use cases to execute through a headless browser
- Update test plan to run these after deployment as the last layer of testing

## Milestone 13 – Open Telemetry / Observability & Monitoring

The goal of this milestone is to gather log entries from the systen, monitor endpoints on recurring intervals, perhaps schedule synthetic testing, and leverage open telemetry.

Deliverables:

- Research opensource tools similar to Checkly, Graylog, Datadog. Define broad config as env variables for simple shift to other vendors on cloud environmens.
- Add docker containers for respective tools
- Create status.hostname portal for health check statuses across subdomains and services. Link through to monitoring and observability tools
- Follow open telemetry best practices
