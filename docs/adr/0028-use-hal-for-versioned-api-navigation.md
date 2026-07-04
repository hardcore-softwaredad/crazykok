---
schema_version: 1
id: 0028
slug: use-hal-for-versioned-api-navigation
title: Use HAL For Versioned API Navigation
status: accepted
date: '2026-07-04'
category: backend
tags:
- api
- hal
- hateoas
- versioning
keywords:
- api discovery
- application/hal+json
- hypermedia
- pagination
supersedes: []
superseded_by: []
---

# ADR 0028: Use HAL For Versioned API Navigation

## Context

API clients currently construct unversioned resource URLs and collection responses are bare arrays. This couples clients to route layout, prevents runtime discovery, and provides no standard navigation through paginated or related records. The API is reached both through the application host's /api proxy and through a dedicated API host, so generated links must also represent the public request topology correctly.

## Decision

Expose the canonical public API under /v1 and use HAL with the application/hal+json media type. Provide a versioned API root whose links advertise only implemented public resources and an RFC 6570 opportunity-search template. Resources contain _links with self, collection, and available domain relations. Database collections contain _links, page metadata, and _embedded resources, using deterministic 1-based offset pagination with a maximum page size of 100. Build URLs centrally from trusted forwarded request context, with PUBLIC_API_BASE_URL as an explicit deployment override. Use application/problem+json for canonical API errors. Keep the existing bare-JSON event and unversioned opportunity routes only as a deprecated compatibility layer until the repository frontend has migrated and the user confirms no local scripts depend on them.

## Consequences

Clients can start at one API root, discover collections, follow related resources, and traverse pages without assembling detail URLs from IDs. The React client must retain and follow returned links. Proxy configuration, content types, pagination boundaries, query preservation, Location headers, and relation names become tested API contract. Plain HAL does not describe mutation methods or forms, so updates continue to use documented HTTP methods against discovered self or collection links rather than advertising action links.

## Alternatives Considered

Keep bespoke JSON link arrays, change existing bare arrays in place, use content negotiation on unversioned routes, adopt JSON:API, Siren, HAL-FORMS, GraphQL, or use cursor pagination immediately. Bespoke links provide no shared convention; changing old arrays silently breaks clients; a separate version gives a clear migration boundary; richer action formats and cursor pagination add complexity not justified by the current local data scale.

## Review Trigger

Review when permission-dependent actions must be advertised, offset pagination becomes measurably inadequate, a second public API representation is required, or deployment can no longer derive safe canonical links from trusted proxy context or the configured public API base URL.
