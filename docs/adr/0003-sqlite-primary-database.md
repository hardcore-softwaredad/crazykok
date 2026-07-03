# ADR 0003: Use SQLite As The Primary Database

- Status: Accepted
- Date: 2026-07-03

## Context

This project is a private, local-first operating system for discovering opportunities and planning operations for a food vending business in and around Drenthe. It will likely be implemented over multiple sessions with help from AI coding agents. Decisions must be explicit so the project stays coherent.

## Decision

Use SQLite through SQLAlchemy, with Alembic migrations.

## Consequences

Provides a portable relational database without server administration.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.
