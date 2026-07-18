# Venue Research Import Workflow

## First Research Batch

1. Open **Import venues** in Crazy Kok.
2. Download the versioned research kit.
3. Give ChatGPT `RESEARCH_INSTRUCTIONS.md` and the relevant CSV templates.
4. Ask for a manageable batch and require CSV output with unchanged headers.
5. Upload the returned venues CSV. Contacts, documents, and aliases CSVs are
   optional and may be uploaded with the same batch.
6. Review the zero-write preview. Nothing has entered the database yet.
7. Correct validation errors and explicitly resolve duplicate or confidence
   conflicts.
8. Apply the reviewed batch and download its result report.

Unknown facts stay empty. A missing CSV column or empty update cell does not
erase an existing value. Clear a known value through the venue edit form.

## Refresh Existing Research

1. Open **Venues** and filter or select the records to refresh.
2. Export the research CSV.
3. Give the export to ChatGPT and tell it to preserve every
   `venue_external_id` exactly.
4. Upload the returned CSV in **Import venues**.
5. Review field-level changes and apply them.

An existing `venue_external_id` is an update, not a duplicate. A new ID is a
create candidate and runs through duplicate detection. If an incoming ID is
manually mapped to an existing venue, that mapping is retained as an import-ID
alias so future refreshes continue to find the same record.

Research exports omit private `internal_notes` values by default while keeping
the canonical column present. A full administrative export may include them
only when explicitly requested.

## Confidence

- **A** — confirmed by the venue or organiser directly
- **B** — official website or document
- **C** — reliable secondary source
- **D** — estimate or inference
- **E** — unknown or placeholder

Lower-confidence data cannot silently replace stronger existing data. The
preview requires an explicit reviewed override or a skip decision.

## Attachments

Research CSVs may contain remote document or gallery URLs. They cannot set
local filesystem paths or make the server download remote content. Upload
local PDFs and images from the venue's Documents or Photos tab.

SQLite data and the configured attachment directory must be backed up and
restored together.
