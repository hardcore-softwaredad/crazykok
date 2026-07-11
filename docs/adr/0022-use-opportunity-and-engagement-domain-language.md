---
schema_version: 1
id: '0022'
slug: use-opportunity-and-engagement-domain-language
title: Use Opportunity And Engagement Domain Language
status: accepted
date: '2026-07-03'
category: domain
tags:
  - application
  - engagement
  - opportunity
keywords:
  - domain language
  - event terminology
  - trading terminology
supersedes: []
superseded_by: []
---

# ADR 0022: Use Opportunity And Engagement Domain Language


## Context

The terms event and trading are ambiguous. The product needs cleaner domain language that distinguishes possible vending chances from real committed business activity while staying coherent across API, database, UI, and documentation.

## Decision

Use Opportunity, Application, Engagement, and Calendar Feed as core terms.

- Opportunity: a possible vending opportunity.
- Application: the process of applying or reserving.
- Engagement: a committed real-world appearance or job, including planning details and actual results after attending.

## Consequences

- API, database, UI, and docs should use this language.
- Existing event/trading terms should be refactored where practical.
- Public-facing event names may still contain “event” when that is their official name.
- The model aligns with how the business is actually planned and executed.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.
