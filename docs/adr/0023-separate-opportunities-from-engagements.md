---
schema_version: 1
id: '0023'
slug: separate-opportunities-from-engagements
title: Separate Opportunities From Engagements
status: accepted
date: '2026-07-03'
category: domain
tags:
  - engagement
  - opportunity
keywords:
  - committed work
  - discovery record
supersedes: []
superseded_by: []
---

# ADR 0023: Separate Opportunities From Engagements


## Context

This project is a private, local-first operating system for discovering opportunities and planning engagements for a food vending business in and around Drenthe. It will likely be implemented over multiple sessions with help from AI coding agents. Decisions must be explicit so the project stays coherent.

## Decision

Keep possible vending chances separate from committed real-world engagements. Actual results live on the engagement because there is no current one-to-many outcome use case.

## Consequences

Keeps discovery, planning, and performance data cleanly separated.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.
