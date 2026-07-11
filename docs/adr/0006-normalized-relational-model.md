---
schema_version: 1
id: '0006'
slug: normalized-relational-model
title: Use A Normalized Relational Model
status: accepted
date: '2026-07-03'
category: data
tags:
  - data-model
  - normalization
keywords:
  - relational model
  - database design
supersedes: []
superseded_by: []
---

# ADR 0006: Use A Normalized Relational Model


## Context

This project is a private, local-first operating system for discovering opportunities and planning operations for a food vending business in and around Drenthe. It will likely be implemented over multiple sessions with help from AI coding agents. Decisions must be explicit so the project stays coherent.

## Decision

Separate opportunity series, opportunities, venues, organisers, applications, engagements, documents, and sources.

## Consequences

Avoids duplication and supports year-over-year comparisons.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.
