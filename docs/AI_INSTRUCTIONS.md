# AI Coding Agent Instructions

## Primary Rule

Use the updated domain language:

- Opportunity
- Opportunity Series
- Application
- Engagement
- Calendar Feed

Avoid reintroducing old event/trading terminology except where referring to external public event names.

## If Existing Code Uses Old Names

If code already contains `events`, `event_occurrences`, `trading_history`, `trading_commitments`, `operations`, or `operation_outcomes`, refactor toward:

- `opportunity_series`
- `opportunities`
- `engagements`

Do this before adding major features.

## Implementation Priority

1. Updated database model
2. Opportunity CRUD
3. Search/filter
4. Application tracking
5. Engagement tracking
6. Engagement actuals and comparisons
7. CSV import/export
8. Map/calendar views
9. ICS calendar feeds

## Calendar Feed Rule

Calendar feeds should be read-only. Do not build two-way sync in the first calendar milestone.

## Avoid

- cloud dependency
- authentication before needed
- route optimization before map/calendar basics
- hiding uncertainty in researched data

## Architecture Decision Records

Read `docs/ADR_AUTHORING.md` before proposing an architectural change. Inspect,
validate, create, and update ADRs through the loopback-only internal authoring
API. Do not choose ADR numbers or edit `docs/adr/*.md` directly. The documented
bootstrap/recovery exception applies only while the gatekeeper itself is being
introduced or repaired. Git staging and commits remain separate from the API.

## API Contract Rule

Read `docs/api/README.md` before changing an HTTP route or public model. The
generated OpenAPI document is part of the feature, not cleanup for later.

After changing a path, method, parameter, request or response field, media
type, status code, error, or HAL relation:

1. run backend contract tests;
2. regenerate `docs/api/openapi/openapi.json` with the exporter;
3. inspect the diff and run the oasdiff compatibility gate;
4. run the safe Schemathesis fitness profile; and
5. verify the interactive reference and live HAL actions.

Never edit the generated baseline by hand, expose `/internal` routes, silently
accept a breaking diff, or customize Scalar/another renderer through a fork
when a standards-based local extension can keep the renderer replaceable.
