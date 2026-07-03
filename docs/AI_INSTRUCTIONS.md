# AI Coding Agent Instructions

## Primary Rule

Use the updated domain language:

- Opportunity
- Opportunity Series
- Application
- Operation
- Operation Outcome
- Calendar Feed

Avoid reintroducing old event/trading terminology except where referring to external public event names.

## If Existing Code Uses Old Names

If code already contains `events`, `event_occurrences`, `trading_history`, or `trading_commitments`, refactor toward:

- `opportunity_series`
- `opportunities`
- `operation_outcomes`
- `operations`

Do this before adding major features.

## Implementation Priority

1. Updated database model
2. Opportunity CRUD
3. Search/filter
4. Application tracking
5. Operation tracking
6. Operation outcomes
7. CSV import/export
8. Map/calendar views
9. ICS calendar feeds

## Calendar Feed Rule

Calendar feeds should be read-only. Do not build two-way sync in the first calendar milestone.

## Avoid

- cloud dependency
- authentication before needed
- route optimization before map/calendar basics
- hiding uncertainty in researched data
