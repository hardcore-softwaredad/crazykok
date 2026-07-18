# Venue Schema

## Purpose

Venue records capture relatively static physical, logistical, and vendor-relevant information about places where opportunities may happen.

Venues should not store derived analytics such as average revenue, average profit, average attendance, or trend metrics. Those belong in a later observability/OLAP layer.

## Design Principles

- Venues are mostly static.
- Opportunities reference venues.
- Engagements reference opportunities.
- Engagement actuals provide facts for later analytics.
- Venue data should support planning, import/export, research, and deduplication.
- Unknown values should remain explicit rather than guessed.

## Core Tables

### venues

The primary venue table. Contains identity, address, geocoding, access, utilities, suitability, documents-as-URLs, research state, and notes.

### venue_contacts

Optional related table for contacts that belong to the venue rather than a specific organiser or opportunity.

Examples:

- venue manager
- booking office
- site access contact
- emergency contact

### venue_documents

Optional related table for documents that belong to the venue.

Examples:

- site map
- vendor map
- parking map
- utility map
- fire regulations
- emergency plan

### venue_aliases

Optional related table for alternate names, historic names, local names, or source-specific names.

## Import Strategy

Use `venue_external_id` as the stable import key.

Recommended format:

```text
VEN-{COUNTRY}-{PROVINCE}-{TOWN}-{SLUG}
```

Example:

```text
VEN-NL-DR-EMMEN-MARKTPLEIN
```

This avoids relying on database IDs during CSV import/export.

## Required Fields For Import

Minimum useful venue import:

- venue_external_id
- venue_name
- town
- municipality
- province
- country
- research_status
- confidence_rating
- active

## Source Tracking

Every researched venue should have at least one source URL if possible:

- source_url_primary
- source_title_primary
- last_researched_at
- last_verified_at
- confidence_rating

## No Venue Statistics Entity

Do not add a venue statistics table in the OLTP schema.

Analytics should be derived later from:

- opportunities
- applications
- engagements

A future observability/OLAP layer can use views, denormalized tables, DuckDB, or another analytical store.
