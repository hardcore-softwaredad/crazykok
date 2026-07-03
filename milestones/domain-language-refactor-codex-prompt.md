# Codex Prompt — Domain Language Refactor

Use this prompt if code already exists with older event/trading terminology.

## Goal

Refactor the project to use the updated domain model:

- Opportunity Series
- Opportunity
- Application
- Operation
- Operation Outcome
- Calendar Feed

## Required Changes

- Rename database models where practical.
- Rename API routes to `/api/opportunities`, `/api/operations`, etc.
- Update frontend labels and route names.
- Update tests.
- Update docs if implementation choices differ.
- Add or update migrations safely.

## Mapping

Old terms to new terms:

- event -> opportunity_series or opportunity depending on meaning
- event_occurrence -> opportunity
- trading_commitment -> operation
- trading_session -> operation_outcome
- trading_history -> operation_outcome / operation history

## Constraints

- Do not lose data.
- Prefer clear migration path over destructive rename.
- Do not change SQLite decision.
- Do not add cloud dependencies.

## Suggested Commit Message

`Refactor domain language to opportunities and operations`
