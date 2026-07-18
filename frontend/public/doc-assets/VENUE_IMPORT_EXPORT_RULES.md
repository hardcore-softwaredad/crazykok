# Venue Import/Export Rules

## Stable External IDs

Use `venue_external_id` for upserts.

Database primary keys should not be required in CSV files.

## Upsert Rules

When importing:

1. Match by `venue_external_id`.
2. If missing, attempt duplicate detection by normalized name + town + municipality.
3. If duplicate is likely, do not automatically create a new venue.
4. Do not overwrite higher-confidence data with lower-confidence data unless explicitly requested.
5. Preserve unknown/null values rather than replacing them with guesses.

## Confidence Ratings

| Rating | Meaning |
|---|---|
| A | Confirmed by venue or organiser directly |
| B | Official website/document |
| C | Reliable secondary source |
| D | Estimate or inferred |
| E | Unknown/placeholder |

## Research Statuses

| Status | Meaning |
|---|---|
| discovered | Known to exist, barely researched |
| identified | Basic listing with a stable identity |
| researched | Address, source, and category mostly present |
| verified | Core fields checked against source |
| complete | Venue profile useful for planning |
| archived | Not active or merged |

## Boolean / Enum Import

Use lowercase strings:

- yes
- no
- limited
- restricted
- depends
- with_permission
- unknown
- true
- false

## Multi-Value Fields

Use semicolon-separated values in CSV.

Example:

```text
town_square;market_square;outdoor_event_space
```

## Dates

Use ISO format:

```text
YYYY-MM-DD
```

## Coordinates

Use WGS84 decimal coordinates.

Example:

```text
52.7831, 6.8972
```

## Source URLs

Use plain URLs in CSV cells.
