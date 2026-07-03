# ADR 0022: Use Opportunity And Operation Domain Language

- Status: Accepted
- Date: 2026-07-03

## Context

The terms event and trading are ambiguous. The product needs cleaner domain language that distinguishes possible vending chances from real committed business activity.

## Decision

Use Opportunity and Operation as core domain terms.

- Opportunity: possible vending opportunity.
- Application: process of applying or reserving.
- Operation: committed real-world plan to attend.
- Operation Outcome: actual results after attending.

## Consequences

- API, database, UI, and docs should use this language.
- Existing event/trading terms should be refactored where practical.
- Public-facing event names can still contain the word event when that is the official name.
