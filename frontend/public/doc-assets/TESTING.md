# Testing

CrazyKok uses four layers of automated verification:

1. Backend tests run with `pytest`.
2. Frontend component tests run with `npm test` in `frontend/`.
3. API contract tests validate drift, compatibility, and live conformance.
4. Playwright drives the real UI through the API in Chromium.

## End-to-end UI tests

From `frontend/`, install the browser once and run the complete local suite:

```sh
npx playwright install chromium
npm run test:e2e
```

The local Playwright configuration builds a temporary API container, publishes
it on an isolated port, and points all HAL links back through the isolated Vite
proxy. The API uses a disposable SQLite database and attachment directory; it
does not use the normal Compose volume or development database. In CI, the same
suite starts FastAPI directly after migrations for a faster run.

The core journeys cover:

- loading every primary workspace;
- creating, editing, archiving, restoring, and deleting an opportunity;
- creating, editing, and archiving a venue;
- planning an engagement and recording its actuals; and
- previewing and applying a reviewed venue CSV import.

Screenshots, video, traces, and the HTML report are retained on failure and are
ignored by Git. CI uploads the HTML report for seven days when a journey fails.

## Post-deployment verification

The `Post-deployment E2E` workflow can be called by a deployment workflow or
started manually with a deployed application URL. It runs only tests tagged
`@smoke`; these are intentionally read-only and verify that the deployed UI,
API, and primary navigation work together.

The equivalent local command against a deployment is:

```sh
E2E_BASE_URL=https://crazykok.com npm run test:e2e:deployed
```

Run this workflow after deployment as the final test layer. Keep mutating
journeys in the isolated pre-deployment suite unless the target is a dedicated
ephemeral test environment.

## API contract gates

API changes have three independent contract gates:

- `python scripts/export_openapi.py --output docs/api/openapi/openapi.json --check`
  detects unreviewed drift from the generated compatibility baseline.
- `scripts/check_api_compatibility.sh` uses oasdiff 1.21.0 to reject breaking
  changes between a reviewed baseline and a candidate.
- `scripts/run_api_fitness.sh` uses Schemathesis 4.22.1 to generate requests and
  validate safe canonical responses against the live contract.

Install `requirements-dev.txt` for the Schemathesis CLI. Run generative tests
against an ephemeral database when mutation operations are added to the
fitness profile; the committed safe profile exercises read-only discovery and
collection operations.
