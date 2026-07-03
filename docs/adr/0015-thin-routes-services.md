# ADR 0015: Keep API Routes Thin And Put Workflows In Services

- Status: Accepted
- Date: 2026-07-03

## Context

This project is a private, local-first operating system for discovering opportunities and planning operations for a food vending business in and around Drenthe. It will likely be implemented over multiple sessions with help from AI coding agents. Decisions must be explicit so the project stays coherent.

## Decision

Keep route handlers thin and place business workflows in service modules.

## Consequences

Improves testability and maintainability.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.
