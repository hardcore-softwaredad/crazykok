# Milestone Roadmap

## Milestone 01 — Foundation Documentation

Status: prepared

Includes domain model, architecture, ADRs, and milestone prompts.

## Milestone 02 — Backend Skeleton

Implement the updated opportunity/engagement domain model.

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
- engagement status UI
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

Status: complete

Deliverables:

- Leaflet map view
- FullCalendar planning view
- clickable opportunity markers/events
- application deadline display
- committed engagement display

Implementation includes shared date, straight-line distance, status, and profit
score filters plus explicit missing-coordinate and missing-date warnings.

## Milestone 06 — Calendar Feeds & Engagements Calendar

Deliverables:

- read-only ICS feeds
- subscribable Apple/Google/Outlook calendar feeds
- all opportunities feed
- filtered opportunities feeds
- committed engagements feed
- application deadlines feed
- engagement tasks feed

## Milestone 07 — Engagements & Results

Status: complete

Deliverables:

- engagement planning
- setup/teardown details
- staffing/equipment notes
- engagement actuals
- year-over-year comparisons
- revenue/cost/profit tracking

Implementation includes normalized opportunity-series assignment, opportunity
actions to create/attach/detach series, detailed setup/teardown and operational
notes, inline engagement actuals, server-derived profit, and year-over-year
comparisons by series, venue, organizer, and municipality.

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

Status: complete

Deliverables:

- Publish canonical OpenAPI 3.1 JSON, YAML, and standalone JSON Schemas through
  discoverable versioned resources.
- Render it with a pinned, self-hosted Scalar container at the configurable
  `api-docs` subdomain; keep the OpenAPI renderer replaceable.
- Make the `docs` subdomain a portal to the decision log and API reference.
- Enforce generated-spec drift, backward compatibility with oasdiff, and live
  implementation conformance with Schemathesis as separate fitness gates.
- Surface safe, actionable GET traversal from live HAL `_links` without forking
  the documentation renderer.
- Require coding agents to verify and intentionally review contract changes.

Implementation and operating notes: `docs/api/README.md`. Architectural
decision: ADR 0030.

## Milestone 12 – End to End UI Testing

Status: complete

Deliverables:

- Incorporate playwright into the project
- Add the core UI use cases to execute through a headless browser
- Update test plan to run these after deployment as the last layer of testing

Implementation includes isolated Chromium journeys for opportunity lifecycle,
venue lifecycle, reviewed venue import, and primary navigation. CI runs the
full mutating suite before deployment; a reusable/manual GitHub Actions
workflow runs only read-only smoke coverage against a deployed URL.

## Milestone 13 – Open Telemetry / Observability & Monitoring

Goal: Gather log entries from the systen for debugging, monitor endpoints on recurring intervals for uptime, perhaps execte synthetic testing, and leverage open telemetry.

Deliverables:

- Research opensource tools similar to Checkly, Graylog, Datadog. Define broad config as env variables for simple shift to other vendors on cloud environmens.
- Add docker containers for respective tools
- Create status.hostname portal for health check statuses across subdomains and services. Link through to monitoring and observability tools
- Follow open telemetry best practices

## Milestone 13A – Authentication & Authorization

Status: in progress

Goal: Require SSO authentication to use the app and some of the other web accessible interfaces. Ideally all related sub systems would work via SSO.

Deliverables:

- Use authentik as the first self-hosted Auth0 alternative, with Keycloak as the
  heavyweight fallback.
- Add an `auth.crazykok` service and Docker topology for authentik, Postgres,
  and Redis.
- Add Nginx forward-auth hooks for the app, API, and database console.
- Add API identity extraction, `/v1/me`, write-role enforcement scaffolding, and
  an internal service bearer token path.
- Configure Google SSO and authentik proxy providers/outposts before enabling
  gateway enforcement in production.
- Require authentication to access operational and database-management surfaces
  once the auth provider is configured.

Implementation decision: ADR 0031.

## Milestone 14 – Expand on Health Check

Goal: To see health status on subsystems, not just the api returning 200OK

Deliverables:

- Decide on subsystems to report on like any event brokers, 3rd party integrations (any auth problems), database connections (thinking beyond a local env), micro services (again, future), redis connections, etc
- Update the endpoint to break down all the things. Keep a overall status (OK, Degraded, Down?)

## Milestone 15 – Bulk Import for Opportunities & Series

Goal: expand import from venue research into the actual marketable work CrazyKok
evaluates: opportunity series and dated opportunities tied to physical venues.

Deliverables:

- CSV import for opportunity series and opportunities.
- Upsert behavior that groups recurring market/event names into
  `OpportunitySeries` records.
- Venue matching by stable venue ID, with the UI eventually using a venue
  typeahead instead of free-text place entry.
- Clear separation between the physical location (`Venue`), the recurring
  concept (`OpportunitySeries`), and the specific dated vending chance
  (`Opportunity`).
- Source, confidence, status, and notes preservation so researched rows can be
  reviewed before action.
- Regression-data cleanup path for old test rows such as duplicate
  `Winter Market` records.

Starter implementation:

- `templates/opportunities_import_template.csv` defines the import columns.
- `templates/opportunities_local_seed.csv` seeds a small local research set
  focused on Emmen market occurrences and TT Circuit Assen race opportunities.
- `scripts/import_local_opportunities.py` imports the seed CSV, can create
  minimal physical venues, and can delete known regression junk.

## Future Initiative – Trail Capture & Review

Goal: split public documentation from private knowledge capture. Keep
`docs.crazykok` as the safe, mostly read-only publication surface, and introduce
`trail.crazykok` as the authenticated prototype for the future Trail app where
writes, uploads, review workflows, the canonical capture API, and the internal
ADR knowledge base live.

Deliverables:

- Keep `docs.crazykok` focused on public-safe, end-user documentation: the API
  reference, a future pedestrian knowledge base, and other explicitly approved
  read-only outputs. Do not publish internal architecture or operational detail
  there.
- Put `trail.crazykok` behind authentication and authorization as the
  write-capable workbench for capture, triage, review, promotion, and internal
  system knowledge.
- As the first Trail surface, port the existing rendered ADR interface to
  `trail.crazykok` behind the auth wall, then remove ADR publication from
  `docs.crazykok`. Preserve repository-backed ADR files and their asset trail;
  this is a presentation and access-boundary move, not a content migration.
- Add an upload/capture surface on `trail.crazykok` for conversation exports,
  curated summaries, supporting files, source links, and metadata.
- Add a canonical capture API, likely `POST /trail/captures`, that stores
  submitted material as reviewable drafts rather than immediately publishing
  docs.
- Add an intake agent that can unpack submitted conversations and files,
  summarize durable context, detect likely ADR candidates, propose links to
  existing ADRs, and organize outputs into `docs/context/`, `docs/requests/`,
  `docs/policies/`, or ADR resources.
- Add a promotion workflow from Trail drafts into repository-backed docs,
  policies, requests, context notes, and ADR resource links.
- Preserve explicit user consent and provenance for every imported AI-chat
  context package.
- Support later integrations from Custom GPT Actions, ChatGPT Apps/MCP,
  bookmarklets, Slack exports, manual uploads, and Codex handoffs.

Related request: `docs/requests/2026-07-13-trail-input-capture.md`.
