# ADR Authoring

Architecture decision records are canonical Markdown files in `docs/adr/`.
They are not application data and must never be copied into a database table.

## File Contract

Every ADR uses YAML front matter with schema version, immutable four-digit ID,
immutable slug, title, status, date, category, tags, keywords, and relationship
IDs. Its filename is `{id}-{slug}.md`, and its H1 is `ADR {id}: {title}`.

Allowed statuses are `proposed`, `accepted`, `rejected`, `deprecated`, and
`superseded`. Allowed categories are `architecture`, `backend`, `data`,
`deployment`, `domain`, `frontend`, `process`, `product`, and `security`. Tags
use lower-case kebab-case. Keywords are free-text search synonyms.

Required sections are:

1. Context
2. Decision
3. Consequences
4. Alternatives Considered
5. Review Trigger

## Twelve-Factor Review

For decisions affecting service boundaries, configuration, deployment, or
external integrations, state the relevant Twelve-Factor trade-off. Prefer
environment-provided configuration and replaceable backing services; a local
stub is appropriate when it preserves the production protocol boundary while
remaining isolated and disposable.

## Decision Resources

ADRs are the canonical surface for decision-adjacent diagrams, workflow
graphics, ERDs, schema snapshots, and sample import files. Store these assets
under `docs/adr/assets/{id}-{slug}/` and link them from the ADR under a
`## Resources` heading.

Place a diagram or graphic immediately after the paragraph, section, or
workflow it helps the reader understand. A visual is explanatory content, not
an appendix: do not collect it at the bottom merely because it is an ADR
resource. Use `## Resources` for supporting documents, point-in-time samples,
provenance, and other durable references. When a diagram is embedded in the
decision, do not repeat it there as a reader-facing source link. Keep editable
source files in the repository only when they are useful to maintainers.

Use `docs/PROJECT_TRAIL.md` for conversation context, policy notes, requests,
and other useful breadcrumbs that do not meet the ADR bar. Link those trail
notes from an ADR's `## Resources` section when they explain or motivate the
decision.

When an import scheme changes, copy the current template and at least one
representative sample CSV into the relevant ADR asset folder and link those
snapshots from the import decision. Supporting documents may also link to the
same assets, but the breadcrumb trail should start at the ADR so future history
and timeline tooling can discover what changed, when, and why.

## Gatekeeper Workflow

After the one-time schema migration, do not create or edit ADR files directly.
Start the local API and use its loopback-only endpoints:

```text
GET  http://127.0.0.1:8000/internal/adrs/schema
GET  http://127.0.0.1:8000/internal/adrs
GET  http://127.0.0.1:8000/internal/adrs/{id}
POST http://127.0.0.1:8000/internal/adrs/validate
POST http://127.0.0.1:8000/internal/adrs
PUT  http://127.0.0.1:8000/internal/adrs/{id}
```

Creation accepts structured metadata and named sections but no ID. The server
allocates the next ID while holding a filesystem lock and writes the canonical
file atomically. Updates require the latest `content_hash` and a
`change_summary`; a stale hash returns HTTP 409.

Accepted decisions cannot have their Decision section materially rewritten.
Create a new ADR with `supersedes` instead. There is intentionally no delete or
renumber endpoint.

The API writes files only. Review at `https://docs.crazykok.local`, inspect the
Git diff, run validation/tests, and commit outside the API.

## Safety Boundary

The internal routes are enabled only for local development, bound to the
loopback host port, and blocked by every Nginx virtual host. Production must set
`ADR_AUTHORING_ENABLED=false`. The API never stages, commits, or pushes files.
