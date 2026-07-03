# Codex Prompt — Milestone 06 Calendar Feeds

## Goal

Add read-only ICS calendar feeds managed by the app.

## Required Deliverables

- calendar_feeds table
- CRUD endpoints for calendar feeds
- ICS endpoint such as `/calendar/{token}.ics`
- Feed types:
  - all_opportunities
  - filtered_opportunities
  - application_deadlines
  - committed_operations
  - operation_tasks
- Tests for ICS output
- Documentation update

## Requirements

- Use standard iCalendar format.
- Feeds must be read-only.
- Feeds should be subscribable by Apple Calendar, Google Calendar, Outlook, and similar apps.
- Filter definitions should be stored as JSON.
- Committed operations should appear in the operations calendar feed.
- Application deadlines should appear in the deadlines feed.

## Non-Goals

- No two-way sync.
- No Google Calendar API integration.
- No remote hosting requirement.

## Suggested Commit Message

`Add read only calendar feeds`
