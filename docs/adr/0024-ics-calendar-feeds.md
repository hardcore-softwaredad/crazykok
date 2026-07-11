---
schema_version: 1
id: '0024'
slug: ics-calendar-feeds
title: Provide Read-Only ICS Calendar Feeds
status: proposed
date: '2026-07-03'
category: architecture
tags:
  - calendar
  - ics
keywords:
  - iCalendar feed
  - calendar subscription
supersedes: []
superseded_by: []
---

# ADR 0024: Provide Read-Only ICS Calendar Feeds


## Context

This project is a private, local-first operating system for discovering opportunities and planning operations for a food vending business in and around Drenthe. It will likely be implemented over multiple sessions with help from AI coding agents. Decisions must be explicit so the project stays coherent.

## Decision

Provide subscribable read-only iCalendar feeds for opportunities, filtered opportunities, deadlines, engagements, and tasks.

## Consequences

Lets Apple Calendar, Google Calendar, and Outlook subscribe without two-way sync complexity.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.
