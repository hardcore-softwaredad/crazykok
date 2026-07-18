# Project Trail Memory Layer

Date: 2026-07-13
Source: Codex chat

## Summary

The project needs a documentation space below the ADR bar for context that
should survive chat history: policy changes, feature discussions, change
requests, research notes, and curated conversation summaries. ADRs remain the
systemic decision surface, but they should link to trail notes when those notes
explain why a decision exists.

## User Intent

Preserve the kind of historical context that would otherwise live in Slack,
chat, or meeting memory. Make it routine for development work to ask whether a
conversation or artifact deserves preservation, and periodically review the
trail for ADR candidates.

## Decisions Or Leaning

- Keep ADRs focused on durable architectural and systemic decisions.
- Add `docs/context/`, `docs/requests/`, and `docs/policies/` as lower-friction
  memory spaces.
- Prefer curated summaries over raw transcripts unless exact wording matters.
- Link trail notes from ADR `## Resources` sections when they motivate or
  explain an ADR.
- Review the trail at milestone boundaries and at least monthly while active.
- Keep `docs.crazykok` as the public-safe documentation surface and use
  `trail.crazykok` as the authenticated write/upload/review workbench.

## Open Questions

- Whether future tooling should index trail notes alongside ADRs in the docs UI.
- Whether raw transcript preservation needs a privacy policy before being used.
- Whether trail review should become a formal checklist item in roadmap
  milestone completion.
- Whether `trail.crazykok` should use a separate service boundary from the docs
  renderer or begin as an authenticated route within the existing docs app.

## Artifacts

- `docs/PROJECT_TRAIL.md`
- `docs/context/README.md`
- `docs/requests/README.md`
- `docs/policies/README.md`
- `docs/AI_INSTRUCTIONS.md`

## ADR Links

- `docs/adr/0019-ai-agent-doc-compliance.md`

## Follow-Up

- Consider adding project-trail indexing to the docs UI once the first few notes
  exist and the retrieval shape is clearer.
