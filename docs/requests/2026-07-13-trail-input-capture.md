# Trail Input Capture

Date: 2026-07-13
Source: Codex chat

## Summary

ChatGPT Web conversations, Codex sessions, Slack-style discussions, uploaded
files, and other external context should be easy to bring into CrazyKok's
project trail. The future Trail app should treat these as first-class captured
inputs that can be summarized, linked, reviewed, and promoted into ADRs,
policies, requests, or context notes.

## User Intent

Reduce the gap between ChatGPT Web context and Codex/repository context.
Encourage important external conversations to be brought into the project so
they can inspire implementation, ADRs, and future timeline/history views.

## Proposed Direction

Split publication from capture. Keep `docs.crazykok` safe to show, and make
`trail.crazykok` the authenticated mini prototype of the future Trail app.

Build a canonical capture API as the stable boundary:

- Accept curated conversation summaries, raw transcript excerpts when approved,
  uploaded files, links, source metadata, tags, and suggested destination.
- Store incoming material as reviewable draft trail entries before publishing
  them into `docs/context/`, `docs/requests/`, `docs/policies/`, or ADR
  resources.
- Host an authenticated upload/capture UI on `trail.crazykok` so humans can
  bring over exports and files from ChatGPT Web or any other AI chat surface.
- Keep `docs.crazykok` focused on approved, public-safe, read-only
  documentation; keep writes, uploads, triage, and review on `trail.crazykok`.
- Add a receiving intake agent that unpacks submissions, extracts durable
  context, proposes organization, and flags ADR candidates instead of requiring
  the human to manually sort every imported package.
- Promote reviewed Trail drafts into repository-backed documentation, ADR
  resources, policies, requests, or context notes.
- Support later integrations from a Custom GPT action, ChatGPT app/MCP server,
  browser bookmarklet, Slack export, manual upload, or Codex command.
- Require explicit user intent before sending ChatGPT Web context or files into
  CrazyKok.

## Open Questions

- Whether the first integration should be a Custom GPT action or manual upload
  form on `trail.crazykok`.
- Whether raw transcripts should ever be stored, or only summaries plus
  selected excerpts.
- How files from ChatGPT sessions should be represented: original binary,
  normalized text extract, metadata record, or all three.
- Whether capture drafts belong in SQLite first, then exported to Markdown, or
  directly in repository files.
- How much authority the intake agent should have: propose-only, create draft
  files, or submit changes through the ADR/document authoring workflow.

## Potential ADR Links

- `docs/adr/0019-ai-agent-doc-compliance.md`
- `docs/adr/0031-self-hosted-authentication-service.md`

## Follow-Up

- Create a Trail capture architecture decision when implementation begins.
- Prototype `POST /trail/captures` before building the full Trail app UI.
- Add a `trail.crazykok` upload prototype once authenticated write privileges
  exist.
