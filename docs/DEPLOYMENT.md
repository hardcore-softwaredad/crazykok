# Deployment

## Environment contract

Configuration follows the twelve-factor convention: deploy-specific values are
provided through environment variables. Copy `.env.example` to `.env` for local
overrides. Docker Compose also contains the same safe defaults, so running with
no `.env` file stays in development and only serves `.local` names.

| Variable | Safe default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | Runtime mode; set explicitly by each deployment. |
| `APP_DOMAIN` | `crazykok.local` | Primary browser application virtual host. |
| `APP_DOMAIN_ALIAS` | `app.crazykok.local` | Additional browser application virtual host. |
| `API_DOMAIN` | `api.crazykok.local` | Direct API virtual host. |
| `DOCS_DOMAIN` | `docs.crazykok.local` | Read-only static decision-log virtual host. |
| `CORS_ALLOWED_ORIGINS` | `https://crazykok.local,https://app.crazykok.local` | Comma-separated origins allowed to call the API. Do not use `*` in production. |
| `ADR_AUTHORING_ENABLED` | `true` in the local Compose environment | Enables the loopback-only ADR filesystem gatekeeper. Must be `false` in production. |
| `ADR_DIRECTORY` | `/app/docs/adr` | Canonical ADR directory mounted read-write into the local API only. |
| `DOCS_ORIGIN` | `https://docs.crazykok.local` | Base URL returned after an ADR file is created. |
| `TRUST_PROXY_HEADERS` | `true` locally | Allows API links to use forwarded scheme, host, and `/api` prefix. Set only when requests pass through a trusted proxy. |
| `PUBLIC_API_BASE_URL` | empty | Optional canonical versioned API root, such as `https://api.crazykok.com/v1`, when proxy-derived links are unsuitable. |
| `WEB_PORT` | `80` | HTTP port; valid app/API hosts redirect to HTTPS. |
| `HTTPS_PORT` | `443` | HTTPS port for the Nginx gateway. |
| `API_PORT` | `8000` | Loopback-only host port for direct API debugging. |
| `DATABASE_URL` | `sqlite:////data/app.db` | SQLAlchemy database URL. |
| `ATTACHMENT_ROOT` | `/data/attachments` | Local venue document/photo storage beneath the persistent API data volume. |
| `MAX_ATTACHMENT_BYTES` | `20971520` | Maximum accepted venue upload size in bytes. |

The frontend uses the same-origin `/api` route through Nginx. The API is also
available directly at `https://api.crazykok.local`; this keeps the frontend simple
while reserving a distinct API subdomain for clients and future deployment.

## Local Docker

```sh
cp .env.example .env
./scripts/generate-local-cert.sh
docker compose up --build
```

Open `https://crazykok.local` (or `https://app.crazykok.local`). The decision
log is at `https://docs.crazykok.local`. API health is
available at `https://api.crazykok.local/health`. HTTP requests for any configured hostname
receive a permanent 308 redirect to HTTPS. Requests sent to the gateway with
any other hostname receive HTTP 421.

The certificate generator uses `mkcert` when it is installed, which provides a
locally trusted certificate after `mkcert -install`. Otherwise it uses OpenSSL
and the browser will display a certificate trust warning. Generated certificates
and private keys under `docker/certs/` are ignored by Git.

Because `.local` is also used by multicast DNS on macOS, add explicit hosts-file
entries for consistent local resolution:

```text
127.0.0.1 crazykok.local app.crazykok.local api.crazykok.local docs.crazykok.local
::1       crazykok.local app.crazykok.local api.crazykok.local docs.crazykok.local
```

On macOS, flush resolver caches after editing `/etc/hosts`:

```sh
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

## Cloud example

Supply production values through the hosting platform rather than committing a
production `.env` file:

```dotenv
APP_ENV=production
APP_DOMAIN=crazykok.com
APP_DOMAIN_ALIAS=app.crazykok.com
API_DOMAIN=api.crazykok.com
DOCS_DOMAIN=docs.crazykok.com
TRUST_PROXY_HEADERS=true
PUBLIC_API_BASE_URL=https://api.crazykok.com/v1
CORS_ALLOWED_ORIGINS=https://crazykok.com,https://app.crazykok.com
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
ADR_AUTHORING_ENABLED=false
DOCS_ORIGIN=https://docs.crazykok.com
```

Create DNS records for the app, API, and docs subdomains pointing to the
gateway/load balancer.
Mount the deployment certificate and key at
`/etc/nginx/certs/localhost.crt` and `/etc/nginx/certs/localhost.key`, or adapt
the gateway configuration to the cloud provider's managed TLS termination.
Expose only ports 80 and 443; the Compose API debug port remains bound to
`127.0.0.1`.

The docs site is generated from `docs/adr/` during the web image build and has
no database or runtime API dependency. Rebuild and deploy the web image after
committed ADR changes. Do not mount the repository into the public web
container. The internal authoring endpoints are explicitly blocked by Nginx;
keep `ADR_AUTHORING_ENABLED=false` as an independent production safeguard.

The `api-data` volume contains both SQLite and venue attachments. Back up and
restore them together so attachment metadata and bytes remain consistent.
Archiving a venue or attachment record does not immediately delete its bytes;
orphan cleanup should run only after a verified backup.
