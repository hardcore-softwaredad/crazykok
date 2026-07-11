# API Specification

## Updated API Language

Use opportunity/engagement terminology in public API routes.

## Version And Hypermedia Contract

The canonical API starts at `GET /api/v1` on the application host and
`GET /v1` on the dedicated API host. Successful canonical representations use
`application/hal+json`; errors use `application/problem+json`.

Resources contain HAL `_links`, including `self`, `collection`, and links to
available related records. Collections contain `_links`, `page`, and
`_embedded`. Database collections accept 1-based `page` and `page_size`
(default 25, maximum 100). Page links preserve search, filters, and sorting.
Unavailable `prev`, `next`, and nullable to-one relations are omitted.

The API root links to an `api-description` resource. That resource is the
discovery point for the canonical OpenAPI 3.1 JSON and YAML documents, the
public component-schema catalog, and the interactive reference. The OpenAPI
document is generated from public FastAPI routes; internal authoring routes are
excluded. Individual components are also available as standalone JSON Schema
documents whose references resolve through local `$defs`.

The API root advertises opportunity search as an RFC 6570 URI template with
`q`, `status`, `category`, `location`, `organizer`, `venue_id`, `series_id`, `active`,
`sort`, `direction`, `page`, and `page_size` parameters.

Venue search is also advertised as a URI template with `q`, `town`,
`municipality`, `category`, `research_status`, `confidence`, `active`,
`missing_coordinates`, `page`, and `page_size`. Canonical venue detail and
embedded collection records contain the complete venue field representation
plus `_links`. Detail responses include every one of the 111 venue fields,
using `null` for unknown values; embedded collection records may omit null
fields to keep paginated responses compact.

Creates return a linked resource and a `Location` header equal to its `self`
link. Updates return the linked resource; deletes return an empty `204`.
Unversioned event/opportunity routes temporarily retain their bare-JSON shape
for compatibility and are deprecated. Remove them at the next API-changing
milestone after the repository frontend uses only `/api/v1`, its contract tests
pass, and the user confirms that no local scripts still consume the old shape.

## Core Endpoints

### Health

- `GET /api/health`

### Discovery

- `GET /api/v1`
- `GET /api/v1/api-description`
- `GET /api/v1/openapi.json`
- `GET /api/v1/openapi.yaml`
- `GET /api/v1/schemas`
- `GET /api/v1/schemas/{schema_name}`

### Opportunity Series

- `GET /api/v1/opportunity-series`
- `POST /api/v1/opportunity-series`
- `GET /api/v1/opportunity-series/{id}`
- `PATCH /api/v1/opportunity-series/{id}`
- `DELETE /api/v1/opportunity-series/{id}`

Opportunity series resources are implemented. They group recurring or named
business sources such as a weekly market, annual festival, or repeat private
client. Opportunities can be attached to a series from either side of the
relationship.

### Opportunities

- `GET /api/v1/opportunities`
- `POST /api/v1/opportunities`
- `GET /api/v1/opportunities/{id}`
- `PATCH /api/v1/opportunities/{id}`
- `DELETE /api/v1/opportunities/{id}`
- `PUT /api/v1/opportunities/{id}/series`
- `POST /api/v1/opportunities/{id}/series`
- `DELETE /api/v1/opportunities/{id}/series`

The series-assignment endpoints attach an opportunity to an existing series,
create/find a series by name from the opportunity, or detach it. This supports
discovering recurrence after an opportunity already exists.

### Search

- Follow `opportunity-search` from `GET /api/v1`.

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

- `GET /api/v1/applications`
- `POST /api/v1/applications`
- `GET /api/v1/applications/{id}`
- `PATCH /api/v1/applications/{id}`

Advertise these links only after the resource is implemented.

### Engagements

- `GET /api/v1/engagements`
- `POST /api/v1/engagements`
- `GET /api/v1/engagements/{id}`
- `PATCH /api/v1/engagements/{id}`
- `DELETE /api/v1/engagements/{id}`
- `GET /api/v1/engagements/comparisons{?group_by}`

Engagement resources expose commitment and pitch details, setup and teardown
times, arrival, staffing, equipment, inventory, travel and general notes,
calendar visibility, and actual result fields such as attendance, revenue,
costs, profit, weather, best sellers, customer notes, rating, attend-again
judgment, and lessons learned. Profit is always calculated by the server as
revenue minus costs. Comparisons accept `series`, `venue`, `organizer`, or
`municipality` and derive annual totals from completed dated engagements.

### Planning

- `GET /api/v1/planning`

The HAL planning projection joins active opportunities to venues and committed
engagements. It accepts `date_from`, `date_to`, `max_distance_km`, `status`, and
`min_score`, and returns visible warnings for opportunities missing coordinates
or dates.

### Organizers

- `GET /api/v1/organizers`
- `GET /api/v1/organizers/{id}`

### Venues

- `GET /api/v1/venues`
- `GET /api/v1/venues/{id}`

The venue-management application API additionally exposes full CRUD, semantic
schema discovery, related records, attachments, duplicate review, and CSV
research workflows under `/api/venues` and `/api/venue-imports`. These routes
remain framework-neutral HTTP contracts; the React application is one client.
Promote them into the canonical versioned HAL surface after their Milestone 10
contract stabilizes.

### Calendar Feeds

- `GET /api/v1/calendar-feeds`
- `POST /api/v1/calendar-feeds`
- `GET /api/v1/calendar-feeds/{id}`
- `PATCH /api/v1/calendar-feeds/{id}`
- `GET /calendar/{token}.ics`

Advertise calendar-feed resource links only after they are implemented.

## Calendar Feed Types

Suggested feed types:

- all_opportunities
- filtered_opportunities
- application_deadlines
- committed_engagements
- engagement_tasks
