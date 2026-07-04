# Codex Prompt — Milestone 08 HATEOAS API Navigation

Read `docs/AI_INSTRUCTIONS.md`, `docs/API_SPEC.md`, `docs/DOMAIN_MODEL.md`,
`docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, the accepted ADRs, and the
current backend, frontend API client, proxy configuration, and API tests before
coding.

## Goal

Make the application API discoverable and navigable through links returned in
its responses. A client that starts at the API root must be able to discover
collections, follow a resource's related records, and move through paginated
results without constructing application URLs from record IDs.

Use HATEOAS (Hypermedia as the Engine of Application State) consistently. The
roadmap's earlier `HATEOS` spelling refers to HATEOAS.

## Intended Outcome

- The API has a versioned root document that links to every public resource
  collection implemented at the time of this milestone.
- JSON resources use one documented HAL representation rather than bespoke
  link shapes per endpoint.
- Collection responses contain pagination metadata and `first`, `last`,
  `prev`, and `next` links when those relations exist.
- Resource responses link to themselves, their collection, and related domain
  records such as opportunity series, venue, organiser, application,
  operation, and operation outcome.
- Links remain correct through the application's `/api/` reverse proxy and on
  the dedicated API host.
- The React client follows links returned by the API for traversal and
  pagination instead of rebuilding those URLs.
- OpenAPI and contract tests describe and protect the hypermedia format.

## Phase 0 — Align The Public Domain API

Do not add a new hypermedia contract to the legacy `/events` API. The accepted
domain language is Opportunity, Opportunity Series, Application, Operation,
and Operation Outcome. Complete the safe domain-language/data migration in
`milestones/domain-language-refactor-codex-prompt.md` first, or make it the
first implementation slice of this milestone if it is still outstanding.

The canonical public API described by this milestone starts at `/api/v1` from
the application origin. Backend-internal paths may omit the proxy's `/api`
prefix, but public links must never expose that deployment detail. Keep the
documented routes in `docs/API_SPEC.md` synchronized with the actual mounted
routers.

If existing clients still use `/events`, retain a small, explicitly deprecated
compatibility router for one documented transition window. It may preserve the
old bare JSON response shape, but it must call the same service layer. Do not
indefinitely maintain two implementations, add HAL fields to the old bare
array, or silently change its response shape. Add deprecation headers and a
removal condition, migrate the repository's frontend, and remove the legacy
router when that condition is met.

Before implementation, use the ADR authoring API described in
`docs/ADR_AUTHORING.md` to record the public representation and versioning
decision. The ADR should cover HAL, media types, link base URL handling,
pagination, compatibility, and alternatives considered.

## Representation Contract

Use HAL's standard `_links` and `_embedded` properties and serve successful
hypermedia representations as `application/hal+json`. Clients should send
`Accept: application/hal+json`. Ordinary JSON request bodies continue to use
`application/json`.

Do not create a private parallel convention such as `links: [{ rel, url }]`.
Use registered IANA relation names where they fit (`self`, `collection`,
`first`, `last`, `prev`, `next`) and stable project relation names for domain
relationships. Document project relation names at the API root. Relation names
are API contract and must not depend on translated UI labels.

Every link object has at least an `href`. Use HAL's `templated: true` only for
an actual RFC 6570 URI template. Omit unavailable optional relations instead
of returning `null`, an empty string, or a link that is known to 404.

### Resource Example

```json
{
  "id": 42,
  "name": "TT Festival 2027",
  "start_date": "2027-06-20",
  "end_date": "2027-06-28",
  "_links": {
    "self": { "href": "https://api.crazykok.local/v1/opportunities/42" },
    "collection": { "href": "https://api.crazykok.local/v1/opportunities" },
    "opportunity-series": { "href": "https://api.crazykok.local/v1/opportunity-series/7" },
    "venue": { "href": "https://api.crazykok.local/v1/venues/12" },
    "applications": { "href": "https://api.crazykok.local/v1/applications?opportunity_id=42" },
    "operations": { "href": "https://api.crazykok.local/v1/operations?opportunity_id=42" }
  }
}
```

This is illustrative, not permission to rename fields that have already been
settled in the canonical schemas.

### Collection Example

```json
{
  "_links": {
    "self": { "href": "https://api.crazykok.local/v1/opportunities?status=open&page=2&page_size=25" },
    "first": { "href": "https://api.crazykok.local/v1/opportunities?status=open&page=1&page_size=25" },
    "last": { "href": "https://api.crazykok.local/v1/opportunities?status=open&page=4&page_size=25" },
    "prev": { "href": "https://api.crazykok.local/v1/opportunities?status=open&page=1&page_size=25" },
    "next": { "href": "https://api.crazykok.local/v1/opportunities?status=open&page=3&page_size=25" }
  },
  "page": {
    "number": 2,
    "size": 25,
    "total_elements": 82,
    "total_pages": 4
  },
  "_embedded": {
    "opportunities": []
  }
}
```

Embedded records use the same schema and link-building code as their detail
representation. Do not maintain a second hand-written embedded resource shape.
An empty result still returns the collection envelope, `self`, pagination
metadata, and an empty embedded array.

## API Root And Discovery

Add `GET /v1` at the backend mount (publicly `/api/v1` through the application
host). It returns:

- `self`;
- links to all implemented public collections;
- a link to the OpenAPI document;
- URI-template links for supported search/filter entry points where useful;
- a `curies` or equivalent documented mechanism for project-specific link
  relations; and
- the API version as data, without requiring clients to parse it from a URL.

Only advertise implemented, reachable endpoints. Health checks, the
loopback-only ADR authoring API, and other operational/internal endpoints are
not public domain resources and must not be linked from the public API root.

The API root is the one URL the frontend may receive from configuration. From
there it should discover collection entry points by relation.

## Link Construction

Create one typed link model and one small link-building layer used by every
router/serializer. Keep business queries in services and link construction at
the HTTP representation boundary. Resource models must not know hostnames,
proxy prefixes, or FastAPI request objects.

Build links from named routes and request context; never concatenate resource
paths in individual handlers. Configure Nginx and FastAPI so forwarded scheme,
host, port, and the `/api` prefix are interpreted only from trusted proxies.
Define and document a `PUBLIC_API_BASE_URL` fallback/override for deployments
where proxy-derived URLs are unavailable or intentionally canonicalized.

The chosen policy must produce usable links in all supported paths:

- `https://crazykok.local/api/v1/...` through the application proxy;
- `https://api.crazykok.local/v1/...` on the dedicated API host;
- Vite's local `/api` proxy;
- direct `TestClient` requests with a deterministic test base URL; and
- production HTTPS without leaking container hosts, `http`, or port 8000.

Normalize path joining and percent-encode path and query values with standard
URL utilities. Preserve repeated query parameters and blank values when they
are meaningful. Do not reflect arbitrary untrusted forwarded headers when the
request did not come from a trusted proxy.

## Pagination And Query Preservation

Paginate every database-backed collection using common `page` and `page_size`
parameters. Start page numbering at 1, choose and document a modest default,
and enforce a maximum of 100. Invalid values return a structured 422 response.

Every paginated query must have a deterministic database ordering with a
unique ID as the final tie-breaker. Apply filters before both the page query
and total count. Pagination links preserve the complete normalized filter,
search, and sort query, changing only `page`. They must not include parameters
that the endpoint ignored.

Define boundary behaviour once and test it:

- `prev` is absent on the first page;
- `next` is absent on the last page;
- `first` and `last` remain available when at least one page exists;
- an empty collection reports zero elements and zero pages without producing
  page zero or negative links; and
- an out-of-range positive page returns an empty valid page rather than a
  misleading `next` link.

Use offset/page pagination for this milestone unless measurement demonstrates
a real need for cursor pagination. Keep the shared pagination service narrow
enough to replace later without changing every route.

## Domain Link Map

Implement relations only when the corresponding endpoint and relationship
exist. At minimum, cover the resources available after Milestones 02–07:

| Resource | Required relations in addition to `self` and `collection` |
|---|---|
| Opportunity Series | filtered `opportunities` collection |
| Opportunity | `opportunity-series` and `venue` when assigned; filtered `applications` and `operations` collections |
| Venue | filtered `opportunities` collection; implemented venue child collections |
| Organiser | filtered `opportunities` collection |
| Application | its `opportunity`; its `operation` only when one exists |
| Operation | its `opportunity`, `application` when applicable, and `operation-outcome` when one exists |
| Operation Outcome | its `operation` |
| Calendar Feed | `self`; its read-only ICS feed URL when issued |

To-many relationships link to filtered collection endpoints even when their
current result is empty. To-one relationships are omitted when the foreign key
is null. A dangling non-null foreign key is a data-integrity error; do not hide
it by emitting a broken link or silently omitting the relation.

Link generation must not issue per-record existence queries. Use declared
foreign keys and already-loaded identifiers, batch loading where the
representation genuinely needs related data, and query-count tests on
collection serialization to prevent N+1 regressions.

HAL links are navigation controls, not authorization or existence guarantees.
Continue to return correct 404/410 responses when a followed target is no
longer available.

## Mutations, Errors, And Caching

- A successful create returns `201`, the HAL resource body, and a `Location`
  header equal to its `self` link.
- Reads and updates return the same linked resource representation.
- A `204` delete has no response body; do not invent links for it.
- Keep mutation methods documented in OpenAPI. Plain HAL links do not describe
  forms or HTTP methods, so action affordances such as archive/restore are out
  of scope unless a later ADR adopts HAL-FORMS or another control format.
- Use `application/problem+json` for errors with a stable problem `type`,
  `title`, HTTP `status`, `detail`, and request-instance URI. Validation errors
  may add an `errors` extension. Do not wrap errors in a success HAL envelope.
- Correct `Vary: Accept` and content-type headers are part of contract tests.
  Add ETags or conditional requests only if they can be implemented
  consistently; they are not required for this milestone.

## Backend Structure

Keep this cross-cutting feature out of a growing `main.py`. Organize the code
around:

- versioned FastAPI routers with stable route names;
- reusable Pydantic HAL link, resource, collection, and page models;
- one request-aware URL/link builder;
- one pagination/query-parameter utility;
- domain serializers/presenters that attach the appropriate relations; and
- thin route handlers calling domain services.

Favor explicit typed schemas over mutating `model_dump()` dictionaries after
validation. Ensure the generated OpenAPI schema shows actual `_links`,
`_embedded`, pagination metadata, media types, and examples.

Do not add a database table for links. Links are derived representation data.

## Frontend Migration

Create a typed API client boundary rather than spreading HAL parsing through
React components. It should:

- load the configured API root once and resolve relations by name;
- request and validate the HAL media type;
- expose embedded records and page metadata to components;
- retain returned link objects for detail and related-resource navigation;
- follow `next`, `prev`, and related links verbatim after applying the normal
  same-origin/allowed-API-origin policy;
- send mutations to discovered collection/resource URLs; and
- turn problem responses into useful UI errors.

The API client may use a small tested relation lookup helper; a broad third-
party HAL framework is unnecessary unless it materially reduces code and is
actively maintained.

Update list UI controls for server-side pagination. Do not calculate global
totals or business summaries from only the current page and present them as
whole-result totals. Use `page.total_elements` for the filtered total; label
page-local values clearly or move true aggregate values to a separately
specified server response.

Clients must not infer related URLs from IDs once a relation is present. IDs
remain domain identifiers and display/debug data, not URL templates.

## Work Plan

### 1. Record And Document The Contract

- Reconcile the domain-language migration and current endpoint inventory.
- Record the HAL/versioning/base-URL/pagination ADR through the authoring API.
- Add the precise media types, envelopes, relation vocabulary, pagination
  rules, and compatibility window to `docs/API_SPEC.md`.
- Add representative success, empty-page, and problem examples.

### 2. Build Shared Hypermedia Infrastructure

- Add typed HAL and pagination schemas.
- Implement named-route URL construction with trusted proxy/prefix handling
  and `PUBLIC_API_BASE_URL` override semantics.
- Add focused unit tests for URL encoding, proxy variants, relation omission,
  query preservation, empty pages, and page boundaries.

### 3. Expose The Versioned API Root

- Mount canonical versioned routers.
- Implement the root discovery document and relation documentation.
- Verify only implemented public resources are advertised.

### 4. Convert Read Endpoints Resource By Resource

- Start with opportunities and their directly related collections.
- Add linked detail representations and paginated HAL collection envelopes.
- Continue through series, venues, organisers, applications, operations,
  outcomes, and calendar feeds that exist.
- Add integration and query-count tests with null, present, archived, and
  dangling relationship cases.

### 5. Align Mutations And Errors

- Return linked resources and `Location` after creates.
- Standardize problem responses without changing successful HAL envelopes.
- Verify content negotiation, status codes, and empty `204` responses.

### 6. Migrate The React Client

- Introduce the typed discovery/HAL client.
- Replace constructed traversal URLs with followed relations.
- Add server-side page controls and correct total/summary semantics.
- Retire the compatibility router when its documented removal condition is
  satisfied.

### 7. Verify Deployment And Documentation

- Test the app proxy, dedicated API host, Vite proxy, TestClient, and
  production-style HTTPS link generation.
- Validate OpenAPI examples and generated schemas.
- Run backend, frontend, build, proxy/configuration, and end-to-end navigation
  tests.
- Update the project journal and mark the milestone complete only after every
  acceptance criterion passes.

## Test Matrix

Cover at least:

- API-root discovery from each supported host/path arrangement;
- correct `Content-Type`, `Accept`, `Vary`, and create `Location` headers;
- resource `self`, `collection`, nullable to-one, and filtered to-many links;
- URL encoding for spaces, Unicode, reserved characters, and repeated filters;
- first, middle, last, empty, single-page, and out-of-range pages;
- stable ordering when primary sort values tie;
- filter/search/sort preservation across every page link;
- resources archived or deleted between link emission and traversal;
- no public link to `/internal`, container hostnames, or plain HTTP in the
  production configuration;
- no N+1 query growth while serializing a page;
- OpenAPI representation of HAL envelopes and problem responses;
- frontend discovery, page traversal, related navigation, error states, and
  direct refresh; and
- temporary legacy-route shape and deprecation headers, if that route exists.

Do not assert only complete JSON snapshots. Combine a few readable contract
fixtures with relation-specific assertions so adding a legitimate optional
relation does not require rewriting every test.

## Acceptance Criteria

- Starting from the public API root, a generic client can discover every
  implemented public collection without hard-coded collection paths.
- All canonical detail and collection reads return documented
  `application/hal+json` representations.
- Every resource has correct `self` and `collection` links and every available
  relationship in the domain link map is navigable.
- Collection links preserve active filters and sorting and have correct page
  boundary behaviour with deterministic results.
- Empty collections and nullable relationships have valid, unambiguous
  representations.
- Creates return a `Location` header matching the returned `self` link;
  deletes return an empty `204`.
- Public URLs are correct through both Nginx entry points and never expose an
  internal hostname, wrong scheme, or stripped proxy prefix.
- Link building is centralized, typed, based on named routes, and causes no
  N+1 queries.
- OpenAPI documents the real HAL, pagination, and problem contracts.
- The frontend follows discovery, pagination, and related-resource links
  rather than reconstructing them from IDs.
- Any legacy compatibility route is isolated, deprecated, tested, and governed
  by a documented removal condition.
- Backend tests, frontend tests, production builds, and end-to-end navigation
  checks pass.

## Non-Goals

- Authentication or permission-dependent links
- HAL-FORMS, Siren actions, JSON:API, GraphQL, or a second hypermedia format
- Embedding complete related graphs in every response
- Persisting links in the database
- Cursor pagination without demonstrated scale requirements
- Two-way calendar synchronization
- Adding domain resources solely so the API root has more links
- Treating OpenAPI as a substitute for runtime navigation

## Suggested Commit Sequence

1. `Document the versioned HAL API contract`
2. `Add shared hypermedia and pagination infrastructure`
3. `Expose API discovery and linked opportunity resources`
4. `Add links across related domain resources`
5. `Migrate the frontend to hypermedia navigation`
6. `Verify proxy URLs and document milestone 08`
