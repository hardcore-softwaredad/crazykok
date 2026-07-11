# Project Journal

## Milestone 07 — Engagements And Results

### Date

2026-07-06

### Summary

Completed the business loop from a committed opportunity through engagement
planning, actual financial results, and year-over-year learning.

### Key Changes

- Expanded engagements with pitch, setup, teardown, arrival, staffing,
  equipment, inventory, travel, calendar visibility, and general notes.
- Added normalized opportunity-series assignment plus opportunity-level actions
  to create, attach, and detach series as recurrence becomes known.
- Folded result fields onto engagements instead of keeping a one-to-one outcome
  table; the backend calculates profit from revenue and costs on every write,
  with rating and attend-again reflections alongside qualitative notes.
- Added derived comparisons by series, venue, organizer, and municipality.
- Added a dedicated Engagements workspace plus API, migration, component/build,
  backend, contract, and browser-journey coverage.

### Why This Matters

CrazyKok can now compare what was expected with what actually happened without
mixing annual business results into static venue or discovery records.

## Milestone 12 — End-to-End UI Testing

### Date

2026-07-06

### Summary

Added Playwright as the final browser-level test layer, with isolated mutating
journeys before deployment and a read-only smoke journey after deployment.

### Key Changes

- Added Chromium coverage for primary navigation, the opportunity lifecycle,
  the venue lifecycle, and reviewed venue CSV import.
- Made local journeys use a disposable API container, database, attachment
  directory, ports, and HAL base URL so development data is never reused.
- Added a dedicated CI job with failure screenshots, video, traces, and an HTML
  report artifact.
- Added a reusable and manually runnable post-deployment workflow that accepts
  a deployment URL and runs only tests tagged `@smoke`.
- Documented the browser test commands and the post-deployment handoff in the
  testing and deployment guides.

### Why This Matters

Component and API tests can pass while navigation, forms, proxying, or browser
behavior is broken. The core workflows now run through the same UI/API boundary
as a person, while production verification remains deliberately read-only.

## Milestone 05 — Map And Calendar Planning Views

### Date

2026-07-05

### Summary

Added one planning desk for spatial and calendar decisions using Leaflet and
FullCalendar.

### Key Changes

- Added a filterable HAL planning projection joining opportunities, venue
  coordinates, application deadlines, and committed engagements.
- Added minimal committed-engagement records without pulling Milestone 07's
  detailed staffing, equipment, and result workflow forward.
- Added straight-line distance filtering from a configurable Schoonebeek home
  location and editable 0–100 profit scores.
- Added map markers, calendar entries, in-context detail, and visible warnings
  for missing coordinates or dates.
- Accepted ADR 0021 through the local authoring gatekeeper and added backend and
  frontend coverage for planning behavior.

### Why This Matters

Opportunity research can now be turned into a practical view of where work is,
when applications are due, and which dates are already committed.

## Milestone 11 — API Contract And Interactive Docs

### Date

2026-07-05

### Summary

Published one generated OpenAPI 3.1 authority for interactive documentation,
public JSON Schemas, compatibility review, and live API fitness testing.

### Key Changes

- Added HAL discovery for canonical JSON/YAML OpenAPI documents and standalone
  component schemas, while excluding internal ADR-authoring routes.
- Added a separate, pinned Scalar container at `api-docs.crazykok.local` with
  an upgrade-safe extension for following live HAL GET links.
- Turned `docs.crazykok.local` into a portal for decisions and API reference.
- Added a generated compatibility baseline under `docs/api/openapi`, oasdiff
  workflow, Schemathesis safe fitness profile, and contract coverage tests.
- Corrected public timestamps to unambiguous RFC 3339 UTC values and aligned
  optional query parameters with their actual wire representation.
- Recorded ADR 0030 so Scalar remains a replaceable renderer, not an API
  architecture dependency.

### Why This Matters

The reference, downloadable schemas, compatibility checks, and generated live
tests now derive from the API that actually runs. A route or entity change can
no longer drift quietly into undocumented or client-breaking behavior.

## Milestone 01 — Foundation Documentation Update

### Date

2026-07-03

### Summary

Updated the project language and model from an event/trading vocabulary to an opportunity/engagement vocabulary.

### Key Changes

- Replaced "event occurrence" as the central planning object with **Opportunity**.
- Replaced "trading commitment" with **Engagement**.
- Kept actual trading history/result fields on **Engagement** rather than a separate one-to-one outcome entity.
- Added calendar subscription feeds using ICS.
- Added a future milestone for calendar feed integration.
- Updated the ERD to separate relatively static venue data from year-over-year opportunities and engagements.
- Added ADRs for domain language, opportunity/engagement separation, and ICS feeds.

### Why This Matters

The application should distinguish:

1. possible places to vend,
2. the user's application/reservation process,
3. committed real-world engagements with actual results after attending.

This supports year-over-year comparisons without polluting static venue records or mixing operational data into opportunity discovery records.

### Next Milestone

Milestone 02 should implement the backend using the updated domain model.

## Milestone 09 — Decision Log

### Date

2026-07-03

### Summary

Added a filesystem-backed architecture decision log with a generated read-only
docs site and a local-only API that gatekeeps ADR creation and modification.

### Key Changes

- Migrated all ADRs to validated YAML metadata plus canonical Markdown.
- Consolidated the duplicate ADR 0022 and locked numbering behind server-side
  allocation, filesystem locking, atomic writes, and optimistic concurrency.
- Added category, tag, keyword, status, relationship, and required-section
  rules without introducing an ADR database table.
- Added searchable overview and rendered detail pages with URL-backed filters,
  highlighted excerpts, and previous/next navigation.
- Added `docs.crazykok.local` as an isolated static Nginx virtual host.
- Kept authoring routes loopback-only, blocked them at Nginx, and disabled them
  by configuration in production.
- Added backend, frontend, build-time index, security, and routing tests.

### Why This Matters

Decisions remain portable and reviewable as repository files while gaining
enough structure to act like searchable records. Coding agents cannot choose
or duplicate identifiers, and the public documentation view needs neither the
application database nor a runtime API.

### Authoring Workflow

Inspect and submit structured proposals through the internal ADR API, review
the generated file at `https://docs.crazykok.local`, and commit it through Git
outside the API.

## Milestone 08 — HATEOAS API Navigation

### Date

2026-07-04

### Summary

Added a versioned HAL API that clients can discover and navigate without
constructing resource URLs from record identifiers.

### Key Changes

- Added `/v1` discovery with links to implemented public resources and an RFC
  6570 opportunity-search template.
- Added HAL resource and paginated collection representations for
  opportunities, organizers, and venues.
- Added centralized proxy-aware link construction, problem responses,
  deterministic pagination, create `Location` headers, and deprecated legacy
  route headers.
- Migrated the React opportunity workspace to discover and follow API links,
  including server-side previous/next navigation.
- Added a fail-closed migration bootstrap for recognized databases created
  before Alembic revision tracking, preserving the existing SQLite volume.
- Recorded the representation decision as accepted ADR 0028 through the local
  authoring gatekeeper.
- Added backend and frontend contract tests for discovery, link relations,
  pagination, proxy prefixes, errors, compatibility, and migration recovery.

### Verification

- 29 backend tests pass in the freshly rebuilt API image.
- 13 frontend tests pass.
- The production frontend build succeeds and contains 29 generated ADRs.
- The persisted SQLite volume migrates successfully and the live `/v1`
  endpoint returns `application/hal+json` discovery links.
