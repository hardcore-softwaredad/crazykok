---
schema_version: 1
id: 0029
slug: store-venue-attachments-in-local-application-data
title: Store Venue Attachments In Local Application Data
status: accepted
date: '2026-07-04'
category: architecture
tags:
- attachments
- local-storage
- venue
keywords:
- attachment backup
- document uploads
- photo storage
supersedes: []
superseded_by: []
---

# ADR 0029: Store Venue Attachments In Local Application Data

## Context

Venue records need uploaded documents and photos while the application remains local-first and portable. Storing large binary payloads inside SQLite would complicate database maintenance, while repository or frontend-bundle storage would mix runtime data with source code and deployments.

## Decision

Store venue attachment bytes beneath a configured application-data root and store their metadata, generated relative path, MIME type, size, and SHA-256 digest in SQLite. Treat remote URLs as references rather than downloading them automatically. Back up and restore the database and attachment root as one logical dataset.

## Consequences

- The SQLite database stays compact and queryable while attachment bytes remain portable on the local data volume.
- Upload and download endpoints must enforce size, type, content-signature, and path boundaries.
- Database and attachment backups must be coordinated.
- Archiving metadata does not immediately delete bytes, allowing reviewed cleanup and recovery.

## Alternatives Considered

- Store attachment bytes as SQLite BLOBs.
- Put runtime uploads in the Git repository or frontend bundle.
- Require cloud object storage.
- Download every remote document or photo URL automatically.

## Review Trigger

Review this decision if the application runs across multiple API instances, adopts cloud object storage, needs content-addressed deduplication, or requires transactional backup guarantees across storage systems.
