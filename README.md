# CrazyKok

[![CI](https://github.com/hardcore-softwaredad/crazykok/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hardcore-softwaredad/crazykok/actions/workflows/ci.yml?query=branch%3Amain)

CrazyKok is a local-first business intelligence and operations tool for a
mobile food vendor. It brings opportunity research, venue knowledge,
applications, operational planning, and results into one durable system so the
business can decide where to trade and learn from what happened.

The current application covers opportunity discovery, opportunity series,
engagement planning, a reusable venue registry, and map/calendar planning. Venue
research includes CSV import/export, contacts, notes, photos, and documents;
planning combines opportunity locations, application deadlines, profit scores,
and committed engagements. The engagements workspace captures setup, staffing,
equipment, actual revenue and costs, qualitative notes, and year-over-year
comparisons. Calendar feeds remain on the [roadmap](docs/ROADMAP.md).

In business terms, an opportunity is a possible chance to work on a particular
date or date range, while an engagement is the work CrazyKok has actually
committed to doing. A recurring market such as the Emmen weekly market can be
stored as an opportunity series, with each Saturday market represented by its
own dated opportunity underneath it; when CrazyKok decides to attend one of
those Saturdays, that commitment becomes an engagement with pitch, setup,
staffing, revenue, costs, and lessons learned on the same record.

One-off work fits the same model without forcing it to become recurring. A
wedding reception or office party can start as a single opportunity and become a
single engagement when accepted. If that customer later becomes repeat business,
the opportunity can be attached to a new or existing opportunity series from the
opportunity screen, letting the history grow naturally instead of depending on
everything being known at import time.

## Public resources

The deployment is designed around these HTTPS hosts. The `.com` addresses are
the production hostname contract; whether they are publicly reachable depends
on the active deployment and DNS configuration.

| Resource | Production | Local | Purpose |
| --- | --- | --- | --- |
| Public website | [www.crazykok.nl](https://www.crazykok.nl) | [www.crazykok.local](https://www.crazykok.local) | Bilingual public pre-launch website supplied by the sibling `crazykok-web` project. |
| Web application | [crazykok.com](https://crazykok.com) / [app.crazykok.com](https://app.crazykok.com) | [crazykok.local](https://crazykok.local) / [app.crazykok.local](https://app.crazykok.local) | Browser application for day-to-day work. |
| API | [api.crazykok.com](https://api.crazykok.com/v1) | [api.crazykok.local](https://api.crazykok.local/v1) | Versioned HAL/JSON API and OpenAPI contract. |
| Decision log | [docs.crazykok.com](https://docs.crazykok.com) | [docs.crazykok.local](https://docs.crazykok.local) | Read-only, searchable architecture decision records. |
| API reference | [api-docs.crazykok.com](https://api-docs.crazykok.com) | [api-docs.crazykok.local](https://api-docs.crazykok.local) | Interactive, self-hosted API documentation. |
| Database console | [db.crazykok.com](https://db.crazykok.com) | [db.crazykok.local](https://db.crazykok.local) | Private database inspection and editing surface. |
| Authentication | [auth.crazykok.com](https://auth.crazykok.com) | [auth.crazykok.local](https://auth.crazykok.local) | Self-hosted SSO, login flows, and gateway authorization. |

## How the system fits together

```text
Browser / API client
        |
        v
Nginx HTTPS gateway (:80/:443)
   |          |           |             |             |
   v          v           v             v             v
React app   FastAPI    API reference   sqlite-web   authentik
               |                         |             |
               v                         v             v
       SQLite + attachments       SQLite data editor  Postgres + Redis
       (api-data volume)          (api-data volume)   (auth volumes)
```

Docker Compose builds four services:

- `web` builds the React/TypeScript application and serves it through Nginx.
  The same gateway terminates local TLS, routes each hostname, and proxies
  `/api` to the backend.
- `api` runs FastAPI with Uvicorn, applies Alembic migrations at startup, and
  stores SQLite data and venue attachments in the persistent `api-data` volume.
- `api-docs` serves a pinned, self-hosted Scalar API Reference. It reads the
  public OpenAPI contract from the API rather than maintaining a second API
  description.
- `db` runs sqlite-web against the same persistent SQLite volume for local data
  inspection and editing. It is exposed only through the Nginx gateway at the
  configured database console hostname.
- `auth-server` and `auth-worker` run authentik with dedicated Postgres and
  Redis services. Nginx exposes it at the configured auth hostname and includes
  switchable forward-auth hooks for app, API, and database-console protection.

The app and the separate `crazykok-web` Compose project join the stable,
project-agnostic `sites-gateway` Docker network. The shared local gateway owns
host ports 80/443 and forwards Crazy Kok traffic to this app Nginx, which routes
`www.crazykok.local` to its `crazykok-public-web` alias and resolves that alias
at request time, so this app stack can still start when the public site is off.

The architecture is intentionally local-first and portable. Production can
replace SQLite through `DATABASE_URL`, but the application does not require a
cloud service to run. See [Architecture](docs/ARCHITECTURE.md) and
[Deployment](docs/DEPLOYMENT.md) for the deeper operational model.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Leaflet, FullCalendar, Vitest, Testing Library, Playwright |
| Backend | Python 3.13, FastAPI, Pydantic, SQLAlchemy, Alembic, Uvicorn |
| Data | SQLite by default; filesystem-backed venue attachments |
| API | Versioned HAL/JSON, RFC 9457 problem details, generated OpenAPI 3.1 |
| API quality | Pytest, snapshot drift checks, oasdiff, Schemathesis |
| Edge and packaging | Docker Compose, multi-stage images, Nginx, local HTTPS |
| API reference | Self-hosted Scalar |
| Continuous integration | GitHub Actions, including isolated browser journeys and reusable post-deployment smoke tests |

## Modules and decisions

| Module | Responsibility | Key decisions |
| --- | --- | --- |
| [`frontend/`](frontend/) | Opportunity, series, venue, planning, engagement, import, and generated decision-log workspaces. | [React and TypeScript](docs/adr/0005-react-typescript-frontend.md), [map and calendar tools](docs/adr/0021-map-and-calendar-planning-tools.md) |
| [`backend/app/`](backend/app/) | HTTP routes, services, domain models, HAL links, uploads, and public contract generation. | [FastAPI](docs/adr/0004-fastapi-backend.md), [thin routes and services](docs/adr/0015-thin-routes-services.md), [HAL navigation](docs/adr/0028-use-hal-for-versioned-api-navigation.md) |
| [`backend/alembic/`](backend/alembic/) | Versioned relational database migrations. | [normalized model](docs/adr/0006-normalized-relational-model.md), [Alembic migrations](docs/adr/0014-alembic-migrations.md) |
| [`docker/`](docker/) and [`docker-compose.yml`](docker-compose.yml) | Reproducible service images, TLS gateway, virtual hosts, and persistent storage wiring. | [local-first application](docs/adr/0002-local-first-application.md), [private portable tool](docs/adr/0020-private-portable-tool.md) |
| [`docs/api/`](docs/api/) | Generated OpenAPI baseline and the replaceable interactive API-reference shell. | [generated API contract](docs/adr/0030-publish-a-generated-openapi-contract-with-replaceable-interactive-docs.md) |
| [`docs/`](docs/) | Engineering guidance, domain documentation, and filesystem-backed ADRs. | [record decisions](docs/adr/0001-record-architecture-decisions.md), [filesystem decision log](docs/adr/0027-filesystem-backed-decision-log.md) |
| [`schemas/`](schemas/) and [`templates/`](templates/) | Machine-readable venue import schema and CSV starter files. | [CSV as a first-class interface](docs/adr/0009-csv-import-export-first-class.md), [managed venue records](docs/adr/0026-venue-management.md) |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Backend, frontend, API-contract, and container verification for pushes and pull requests. | [tests for business logic](docs/adr/0018-tests-for-business-logic.md), [generated API contract](docs/adr/0030-publish-a-generated-openapi-contract-with-replaceable-interactive-docs.md) |

The main business entities and their boundaries are defined in the
[Domain Model](docs/DOMAIN_MODEL.md). Particularly relevant decisions are
[opportunity occurrences](docs/adr/0007-opportunity-occurrences.md),
[opportunities versus engagements](docs/adr/0023-separate-opportunities-from-engagements.md),
[venue management](docs/adr/0026-venue-management.md), and
[local venue attachments](docs/adr/0029-store-venue-attachments-in-local-application-data.md).

## Run locally

### Prerequisites

- Docker with Docker Compose
- `mkcert` (recommended) or OpenSSL for the local certificate
- permission to add local names to `/etc/hosts`

### Start the stack

```sh
cp .env.example .env
./scripts/generate-local-cert.sh
docker compose up --build
```

Add the virtual hosts to `/etc/hosts` so all local URLs resolve consistently:

```text
127.0.0.1 www.crazykok.local crazykok.local app.crazykok.local api.crazykok.local docs.crazykok.local api-docs.crazykok.local db.crazykok.local auth.crazykok.local
::1       www.crazykok.local crazykok.local app.crazykok.local api.crazykok.local docs.crazykok.local api-docs.crazykok.local db.crazykok.local auth.crazykok.local
```

On macOS, flush the resolver cache after changing the hosts file:

```sh
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Then open [https://crazykok.local](https://crazykok.local). If the certificate
was generated with OpenSSL instead of `mkcert`, the browser will show a local
certificate warning. API health is available at
[https://api.crazykok.local/health](https://api.crazykok.local/health).
The local database console is available at
[https://db.crazykok.local](https://db.crazykok.local).

Stop the containers with `docker compose down`. Add `--volumes` only when you
intentionally want to delete the local database and attachment store.

## Configuration

Copy [`.env.example`](.env.example) to `.env` for local overrides. Compose has
safe development defaults, so the file is optional unless a value needs to
change.

| Variable | Default | Used for |
| --- | --- | --- |
| `APP_ENV` | `development` | Runtime mode. Set explicitly in each deployment. |
| `PUBLIC_SITE_DOMAIN` | `www.crazykok.local` | Public-site virtual host proxied to the sibling `crazykok-web` container. |
| `APP_DOMAIN` | `crazykok.local` | Primary application hostname. |
| `APP_DOMAIN_ALIAS` | `app.crazykok.local` | Alternate application hostname. |
| `API_DOMAIN` | `api.crazykok.local` | Public API hostname and API-docs upstream. |
| `DOCS_DOMAIN` | `docs.crazykok.local` | Decision-log hostname. |
| `API_DOCS_DOMAIN` | `api-docs.crazykok.local` | Interactive API-reference hostname. |
| `DB_DOMAIN` | `db.crazykok.local` | Private sqlite-web database console hostname. |
| `AUTH_DOMAIN` | `auth.crazykok.local` | Self-hosted authentik hostname. |
| `AUTH_GATEWAY_MODE` | `auth-disabled` | Nginx auth snippet; switch to `auth-authentik` after authentik proxy providers are configured. |
| `AUTH_API_REQUIRED` | `false` | Requires API identity headers or service bearer token for protected API routes. |
| `AUTH_SERVICE_TOKEN` | empty | Internal service bearer token for machine-to-machine API calls. |
| `AUTH_WRITE_ROLES` | `admin,operator` | Roles allowed to mutate API resources when API auth is required. |
| `AUTH_OIDC_JWKS_URL` / `AUTH_OIDC_ISSUER` / `AUTH_OIDC_AUDIENCE` | empty | Optional OIDC bearer-token validation for external API clients. |
| `DOCS_ORIGIN` | `https://docs.crazykok.local` | Canonical decision-log URL returned after local ADR authoring. |
| `API_DOCS_ORIGIN` | `https://api-docs.crazykok.local` | Canonical API-reference link advertised by the API. |
| `CORS_ALLOWED_ORIGINS` | Local app and API-docs origins | Comma-separated browser origins allowed to call the API. |
| `API_PORT` | `8000` | Loopback-only backend debugging port. |
| `SITES_GATEWAY_NETWORK` | `sites-gateway` | Project-agnostic Docker network shared with the local gateway and public site. |
| `DATABASE_URL` | `sqlite:////data/app.db` | SQLAlchemy database connection. |
| `ATTACHMENT_ROOT` | `/data/attachments` | Venue attachment storage inside the persistent volume. |
| `MAX_ATTACHMENT_BYTES` | `20971520` | Maximum venue upload size in bytes (20 MiB by default). |
| `PLANNING_HOME_LATITUDE` / `PLANNING_HOME_LONGITUDE` | Schoonebeek (`52.6627`, `6.8847`) | Origin used for straight-line planning distance filters. |
| `TRUST_PROXY_HEADERS` | `true` | Build public links from trusted forwarded host, scheme, and prefix headers. |
| `PUBLIC_API_BASE_URL` | empty | Optional canonical `/v1` API root when proxy-derived links are unsuitable. |
| `ADR_AUTHORING_ENABLED` | `true` locally | Enables the loopback-only ADR authoring API; always disable in production. |
| `ADR_DIRECTORY` | `/app/docs/adr` | ADR directory mounted into the local API container. |

Never commit `.env`, certificates, database files, or attachment data. The full
production contract and backup considerations are in
[Deployment](docs/DEPLOYMENT.md).

## Development and verification

Backend setup and tests:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

The app includes an **Import opportunities** workspace for applying opportunity
CSV files. To run the same cleanup/import from the command line against the
default SQLite database:

```sh
DATABASE_URL=sqlite:///backend/data/app.db alembic -c backend/alembic.ini upgrade head
DATABASE_URL=sqlite:///backend/data/app.db python scripts/import_local_opportunities.py --seed-venues --clean-regression-junk
```

The seed import uses `templates/opportunities_local_seed.csv`: venues remain
physical places, while recurring markets and races become opportunity series
with dated opportunities underneath them.

Frontend setup and tests:

```sh
cd frontend
npm ci
npm test
npm run build
```

End-to-end browser tests use an isolated API and database. Install Chromium
once, then run the full local journey suite:

```sh
cd frontend
npx playwright install chromium
npm run test:e2e
```

The reusable `Post-deployment E2E` GitHub Actions workflow runs the read-only
`@smoke` journey against a supplied deployment URL. See
[Testing](docs/TESTING.md) for the test layers and deployment handoff.

HTTP route or public-model changes must also follow the
[API contract workflow](docs/api/README.md), including contract regeneration,
compatibility review, and fitness testing. See [Testing](docs/TESTING.md) for
the complete test matrix. The same core checks run in
[GitHub Actions](.github/workflows/ci.yml) on pushes and pull requests to
`main`; the badge at the top of this README reports the latest `main` result.

## Working on the project

Start with these documents:

1. [Vision](docs/VISION.md) and [Domain Model](docs/DOMAIN_MODEL.md)
2. [Roadmap](docs/ROADMAP.md) and [Project Journal](PROJECT_JOURNAL.md)
3. [Coding Standards](docs/CODING_STANDARDS.md) and [Contributing](docs/CONTRIBUTING.md)
4. [Architecture Decision Records](docs/adr/) and [ADR authoring rules](docs/ADR_AUTHORING.md)
5. [AI agent instructions](docs/AI_INSTRUCTIONS.md), when working with a coding agent

Use the project language—Opportunity, Opportunity Series, Application,
Engagement, and Calendar Feed—rather than the old event/trading terminology.
Architectural changes require an ADR, and ADR files
must be created or updated through the local authoring API described in the
authoring rules.

Security and data-handling expectations are documented in
[Security](docs/SECURITY.md), [Data Collection Policy](docs/DATA_COLLECTION_POLICY.md),
and [Research Guidelines](docs/RESEARCH_GUIDELINES.md).
