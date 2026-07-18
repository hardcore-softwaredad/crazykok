---
schema_version: 1
id: '0009'
slug: csv-import-export-first-class
title: Make CSV Import And Export First-Class
status: accepted
date: '2026-07-03'
category: data
tags:
  - csv
  - portability
keywords:
  - import export
  - spreadsheet
supersedes: []
superseded_by: []
---

# ADR 0009: Make CSV Import And Export First-Class


## Context

This project is a private, local-first operating system for discovering opportunities and planning operations for a food vending business in and around Drenthe. It will likely be implemented over multiple sessions with help from AI coding agents. Decisions must be explicit so the project stays coherent.

## Decision

Support CSV import/export as core functionality, with validation and duplicate detection.

## Consequences

Keeps data portable and compatible with spreadsheets and AI-assisted workflows.

## Alternatives Considered

- Leave the decision implicit in chat history.
- Let the coding agent infer the design.
- Choose a broader or more complex option earlier than needed.

## Review Trigger

Review this ADR if the project scope, deployment model, data model, or primary workflow changes materially.

## Resources

- [Venue import template snapshot](assets/0009-csv-import-export-first-class/venues_import_template.csv)
- [Venue import example snapshot](assets/0009-csv-import-export-first-class/venues_import_example.csv)
- [Venue contact import template snapshot](assets/0009-csv-import-export-first-class/venue_contacts_import_template.csv)
- [Venue document import template snapshot](assets/0009-csv-import-export-first-class/venue_documents_import_template.csv)
- [Venue alias import template snapshot](assets/0009-csv-import-export-first-class/venue_aliases_import_template.csv)
- [Opportunity import template snapshot](assets/0009-csv-import-export-first-class/opportunities_import_template.csv)
- [Opportunity local seed snapshot](assets/0009-csv-import-export-first-class/opportunities_local_seed.csv)
- [Venue import JSON schema snapshot](assets/0009-csv-import-export-first-class/venue_import_schema.json)
- [Import/export specification](../IMPORT_EXPORT_SPEC.md)
- [Venue import/export rules](../VENUE_IMPORT_EXPORT_RULES.md)
- [Venue research import workflow](../VENUE_RESEARCH_IMPORT_WORKFLOW.md)
