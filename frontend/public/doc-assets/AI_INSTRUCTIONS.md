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

## Twelve-Factor Decision Check

When proposing infrastructure, integrations, configuration, or deployment
changes, evaluate the design against the Twelve-Factor App principles. Prefer
replaceable backing services, explicit environment configuration, separate
build/release/run concerns, disposable processes, and parity between local and
upstream environments.

Use local stubs for external dependencies when they exercise the same protocol
and boundary as the intended upstream service. Keep stubs isolated, disposable,
and clearly non-production; do not couple application code to a particular
vendor because the local substitute differs from production.

If a meaningful trade-off departs from these principles, document the reason in
an ADR or Trail note rather than allowing the exception to become implicit.

## Point-in-Time Artifact Trail

Read `docs/PROJECT_TRAIL.md` before closing meaningful feature, policy,
research, or documentation work.

Before finishing work, ask whether any changed or generated artifact captures
decision-relevant state that future history, timeline, or audit tooling should
be able to find. Examples include Mermaid diagrams, ERDs, workflow sketches,
OpenAPI contract snapshots, import templates, sample CSVs, schema files,
research datasets, migration plans, and deployment topology notes.

If the artifact explains or freezes an architectural, data, product, security,
or process decision, tie it to the appropriate ADR through that ADR's
`## Resources` section and store stable copies under
`docs/adr/assets/{id}-{slug}/` when the exact point-in-time content matters.
Place reader-facing diagrams, ERDs, and workflow graphics beside the prose they
explain. Do not treat the `## Resources` section as a chart dump; it is for
supporting artifacts and provenance. Embed the rendered graphic at its relevant
point and avoid publishing maintenance-only source views unless they are useful
to the intended reader.
If it is unclear whether an artifact is important enough to preserve, ask the
human before discarding, overwriting, or leaving it only in an implementation
directory.

If the work includes meaningful feature discussion, policy discussion, research,
or change-request context that does not meet the ADR bar, add or update a
curated trail note under `docs/context/`, `docs/requests/`, or `docs/policies/`.
At milestone boundaries and during periodic review, scan those notes for
undocumented architectural decisions that should be promoted to ADRs.

## Development Closeout Routine

Before finalizing meaningful development work:

1. Verify code, tests, and generated artifacts relevant to the change.
2. Update user-facing and engineering docs affected by the change.
3. Apply the point-in-time artifact trail check.
4. Add or update trail notes for durable context that is below ADR scope.
5. Create or update ADR links when the trail reveals systemic decisions.
6. Regenerate generated docs indexes when ADRs or indexed docs change.

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
