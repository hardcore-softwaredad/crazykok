# Project Journal

## Milestone 01 — Foundation Documentation Update

### Date

2026-07-03

### Summary

Updated the project language and model from an event/trading vocabulary to an opportunity/operation vocabulary.

### Key Changes

- Replaced "event occurrence" as the central planning object with **Opportunity**.
- Replaced "trading commitment" with **Operation**.
- Replaced "trading history/session" with **Operation Outcome**.
- Added calendar subscription feeds using ICS.
- Added a future milestone for calendar feed integration.
- Updated the ERD to separate relatively static venue data from year-over-year opportunities and operations.
- Added ADRs for domain language, opportunity/operation separation, and ICS feeds.

### Why This Matters

The application should distinguish:

1. possible places to vend,
2. the user's application/reservation process,
3. committed real-world operations,
4. actual outcomes after attending.

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
