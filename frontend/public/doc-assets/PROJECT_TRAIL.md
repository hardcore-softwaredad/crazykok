# Project Trail

The project trail is the lightweight memory layer around CrazyKok. ADRs remain
the canonical record for durable architectural decisions, but not every useful
conversation, policy choice, research note, or feature prompt needs to clear the
ADR bar.

Use the trail to preserve context that a future human or agent would otherwise
have to reconstruct from chat history.

## Documentation Layers

- `docs/adr/`: durable architectural, systemic, data, security, deployment, and
  process decisions.
- `docs/adr/assets/`: point-in-time artifacts directly tied to ADR decisions.
- `docs/context/`: curated conversation summaries, research notes, feature
  exploration notes, and implementation context that may later inspire ADRs.
- `docs/requests/`: feature briefs, change requests, open product questions, and
  pre-ADR proposals.
- `docs/policies/`: operating policies and rules that guide behavior without
  necessarily changing architecture.

Existing top-level documentation can stay where it is. Add a trail entry when
the extra historical breadcrumb is useful.

## Conversation Capture

Create a context note when a chat changes direction, explains why a feature
matters, records a tradeoff, or would be painful to rediscover later.

Use `docs/context/YYYY-MM-DD-short-topic.md` and keep it curated by default:

```markdown
# Short Topic

Date: YYYY-MM-DD
Source: Codex chat, Slack, meeting, research session, or manual note

## Summary

## User Intent

## Decisions Or Leaning

## Open Questions

## Artifacts

## ADR Links

## Follow-Up
```

Do not paste raw private chat transcripts by default. Summarize the useful
context. Preserve raw transcript excerpts only when the exact wording is itself
important and safe to keep in the repository.

## Change Request Capture

Use `docs/requests/YYYY-MM-DD-short-topic.md` when the work is not yet ready to
be a roadmap milestone or ADR. A request can link to context notes, prototypes,
research, sample files, or ADRs it may affect.

## Policy Capture

Use `docs/policies/` for rules of operation: research ethics, data collection,
review cadence, deployment posture, documentation standards, and similar
behavioral commitments.

Policies can cite ADRs when they are constrained by architecture. ADRs can cite
policies when a decision depends on an operating rule.

## ADR Escalation Check

When adding or reviewing a trail entry, ask:

- Does this change system shape, data contracts, deployment topology, security,
  persistence, integration boundaries, or long-lived process?
- Would future work be unsafe or confusing without knowing why this choice was
  made?
- Is there a point-in-time artifact that should be frozen under
  `docs/adr/assets/{id}-{slug}/`?

If yes, create or update an ADR and link the trail entry from that ADR's
`## Resources` section.

## Development Routine

At the end of meaningful development work:

1. Update code and tests.
2. Update current docs affected by behavior or workflows.
3. Ask whether the work produced point-in-time artifacts.
4. Add or update a context, request, or policy note when conversation history
   carries useful intent or tradeoffs.
5. Create or update an ADR when the trail reveals an undocumented systemic
   decision.
6. Regenerate generated docs indexes and run the relevant validation.

## Periodic Review

Review the project trail at milestone boundaries and at least monthly while the
project is active.

During review:

- Promote context or request notes into ADRs when architectural decisions have
  emerged.
- Link orphaned notes to roadmap items, policies, ADRs, or follow-up work.
- Archive or mark stale requests so they do not look like active intent.
- Check ADR resources for missing diagrams, schemas, import samples, or contract
  snapshots.
