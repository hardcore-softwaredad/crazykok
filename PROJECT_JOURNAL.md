# Project Journal

## Milestone 01 — Foundation Documentation Update

### Date

2026-07-03

### Summary

Updated the project language and model from an event/trading vocabulary to an opportunity/operation vocabulary.

### Key Changes

- Replaced "event occurrence" as the central planning object with **Opportunity**.
- Replaced "trading commitment" with **Operation**.
- Replaced "trading history/session" with **Operation Outcome**.
- Added calendar subscription feeds using ICS.
- Added a future milestone for calendar feed integration.
- Updated the ERD to separate relatively static venue data from year-over-year opportunities and operations.
- Added ADRs for domain language, opportunity/operation separation, and ICS feeds.

### Why This Matters

The application should distinguish:

1. possible places to vend,
2. the user's application/reservation process,
3. committed real-world operations,
4. actual outcomes after attending.

This supports year-over-year comparisons without polluting static venue records or mixing operational data into opportunity discovery records.

### Next Milestone

Milestone 02 should implement the backend using the updated domain model.
