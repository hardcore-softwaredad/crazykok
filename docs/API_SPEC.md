# API Specification

## Updated API Language

Use opportunity/operation terminology in public API routes.

## Core Endpoints

### Health

- `GET /api/health`

### Opportunity Series

- `GET /api/opportunity-series`
- `POST /api/opportunity-series`
- `GET /api/opportunity-series/{id}`
- `PATCH /api/opportunity-series/{id}`
- `DELETE /api/opportunity-series/{id}`

### Opportunities

- `GET /api/opportunities`
- `POST /api/opportunities`
- `GET /api/opportunities/{id}`
- `PATCH /api/opportunities/{id}`
- `DELETE /api/opportunities/{id}`

### Search

- `GET /api/search/opportunities`

Suggested filters:

- q
- date_from
- date_to
- town
- municipality
- max_distance_km
- opportunity_type
- research_status
- application_status
- electricity_available
- water_available
- max_booth_fee_eur
- min_estimated_attendance
- min_profit_score

### Applications

- `GET /api/applications`
- `POST /api/applications`
- `GET /api/applications/{id}`
- `PATCH /api/applications/{id}`

### Operations

- `GET /api/operations`
- `POST /api/operations`
- `GET /api/operations/{id}`
- `PATCH /api/operations/{id}`

### Operation Outcomes

- `GET /api/operation-outcomes`
- `POST /api/operation-outcomes`
- `GET /api/operation-outcomes/{id}`
- `PATCH /api/operation-outcomes/{id}`

### Calendar Feeds

- `GET /api/calendar-feeds`
- `POST /api/calendar-feeds`
- `GET /api/calendar-feeds/{id}`
- `PATCH /api/calendar-feeds/{id}`
- `GET /calendar/{token}.ics`

## Calendar Feed Types

Suggested feed types:

- all_opportunities
- filtered_opportunities
- application_deadlines
- committed_operations
- operation_tasks
