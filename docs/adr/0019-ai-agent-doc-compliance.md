---
schema_version: 1
id: '0019'
slug: ai-agent-doc-compliance
title: Require AI Coding Agents To Follow Documentation
status: accepted
date: '2026-07-03'
category: process
tags:
  - ai-agents
  - documentation
keywords:
  - coding agent rules
  - documentation compliance
supersedes: []
superseded_by: []
---

# ADR 0019: Require AI Coding Agents To Follow Documentation


## Context

This project is a private, local-first operating system for discovering opportunities and planning operations for a food vending business in and around Drenthe. It will likely be implemented over multiple sessions with help from AI coding agents. Decisions must be explicit so the project stays coherent.

## Decision

AI coding agents must follow docs and ADRs; architectural changes require new or updated ADRs. Agents must also consider whether point-in-time artifacts such as diagrams, ERDs, workflows, schemas, contract snapshots, and import samples should be preserved as ADR resources before finishing work. Durable feature, policy, research, and change-request context that does not meet the ADR bar belongs in the project trail and must be reviewed periodically for ADR candidates.

## Consequences

Prevents the agent from inventing architecture or expanding scope unexpectedly.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.

## Resources

- [AI coding agent instructions](../AI_INSTRUCTIONS.md)
- [ADR authoring rules](../ADR_AUTHORING.md)
- [Project trail convention](../PROJECT_TRAIL.md)
