# API Contract And Interactive Reference

The live FastAPI routes are the source of truth. `backend/app/openapi_contract.py`
generates a public OpenAPI 3.1 description from intentionally public routes;
internal ADR authoring never enters the document.

## Public Resources

- `GET /v1/api-description` — HAL discovery resource
- `GET /v1/openapi.json` — canonical OpenAPI JSON
- `GET /v1/openapi.yaml` — equivalent OpenAPI YAML
- `GET /v1/schemas` — public component-schema catalog
- `GET /v1/schemas/{name}` — standalone JSON Schema with local `$defs`

The framework compatibility endpoint `/openapi.json` redirects to the canonical
versioned resource. `/docs` and `/redoc` redirect to the interactive reference.

## Files In This Directory

- `index.html`, `api-docs.js`, and `api-docs.css` are the small branded shell
  around Scalar. The HAL explorer observes standard responses and deliberately
  uses no Scalar internals.
- `package.json` pins Scalar; its lockfile makes the container build repeatable.
- `openapi/openapi.json` is a generated compatibility baseline. Never edit it
  by hand and never treat it as a second specification source.

## Contract Workflow

After changing a route, request model, response model, media type, status code,
or link relation:

1. run the backend contract tests;
2. regenerate the baseline with
   `python scripts/export_openapi.py --output docs/api/openapi/openapi.json`;
3. inspect the diff and run `scripts/check_api_compatibility.sh` before accepting
   it; by default it compares the generated candidate with the baseline in
   `HEAD`, so regenerating the working file cannot hide a breaking change;
4. run `scripts/run_api_fitness.sh` against an ephemeral or local test API; and
5. verify the engagement and its live HAL links in the interactive reference.

These gates answer different questions: drift checks whether code and the
reviewed artifact agree, oasdiff checks client compatibility, and Schemathesis
checks whether the running implementation obeys the description.
