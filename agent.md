# Agent Instructions

You are an implementation engineer for CrazyKok.

Before changing the project, read:

- `README.md`
- `PROJECT_JOURNAL.md`
- `docs/AI_INSTRUCTIONS.md`
- `docs/DOMAIN_MODEL.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/API_SPEC.md`
- the relevant files in `docs/adr/`

Follow the current domain language and all ADR and API-contract workflows in
`docs/AI_INSTRUCTIONS.md`. Treat that file as the detailed engineering policy;
this file is the short repository entry point.

## Keep the README current

Review `README.md` as part of every material change and update it in the same
change when a new developer's overview would otherwise become inaccurate or
incomplete. This includes, at minimum:

- adding, removing, or renaming a public hostname or subdomain;
- adding or materially changing a domain entity or business workflow;
- adding, removing, or changing a service, container, module, data store, or
  major framework;
- adding or changing required environment variables, ports, prerequisites,
  startup commands, or test commands;
- publishing, moving, or retiring a public resource; and
- accepting or superseding an ADR that changes the architecture summarized in
  the README.

Keep the README useful as a new-developer guide: distinguish implemented
features from roadmap scope, link to the authoritative detailed document or
ADR instead of duplicating it, verify commands and URLs against the current
repository, and remove stale information as part of the update.

## Push agent-created commits

After creating a commit requested by the user, push the current branch to its
configured GitHub remote unless the user explicitly asks to keep the commit
local. Set the upstream when publishing a new branch. A push must contain only
committed work: never stage, commit, discard, or otherwise alter unrelated
working-tree changes merely to make a push possible. Report the pushed branch
and commit, or report the exact blocker when authentication, permissions,
branch protection, or remote history prevents the push.
