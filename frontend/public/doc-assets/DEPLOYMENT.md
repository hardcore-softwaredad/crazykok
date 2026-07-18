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
| `API_DOCS_DOMAIN` | `api-docs.crazykok.local` | Interactive API-reference virtual host. |
| `DB_DOMAIN` | `db.crazykok.local` | Private database console virtual host. |
| `AUTH_DOMAIN` | `auth.crazykok.local` | Self-hosted authentik virtual host. |
| `IDP_STUB_DOMAIN` | `idp.crazykok.local` | Local-only Keycloak OIDC federation stub. |
| `AUTHENTIK_IMAGE` | `ghcr.io/goauthentik/server:latest` | Authentik server and worker image. Pin in production. |
| `AUTHENTIK_SECRET_KEY` | placeholder | Authentik signing/encryption secret; must be random and private. |
| `AUTHENTIK_BOOTSTRAP_*` | empty | Optional first-admin email, password, and token for initial authentik setup. |
| `AUTH_POSTGRES_*` | local placeholders | Dedicated authentik Postgres database credentials. |
| `AUTH_GATEWAY_MODE` | `auth-disabled` | Nginx auth snippet; use `auth-authentik` after proxy providers/outposts are configured. |
| `FULL_LOGOUT_URL` | local Keycloak logout chain | Gateway destination used by `/logout`; set to the application-host Authentik sign-out URL when Google is upstream. |
| `AUTH_API_REQUIRED` | `false` | Requires gateway identity headers or the internal service token on protected API routes. |
| `AUTH_SERVICE_TOKEN` | empty | Internal bearer token for service-to-service API calls. |
| `AUTH_WRITE_ROLES` | `admin,operator` | Roles allowed to mutate API resources when API auth is required. |
| `AUTH_OIDC_JWKS_URL` | empty | Optional JWKS URL for validating external OIDC bearer tokens. |
| `AUTH_OIDC_ISSUER` | empty | Optional expected issuer for OIDC bearer tokens. |
| `AUTH_OIDC_AUDIENCE` | empty | Optional expected audience for OIDC bearer tokens. |
| `API_DOCS_ORIGIN` | `https://api-docs.crazykok.local` | Canonical link advertised by API discovery and legacy docs redirects. |
| `CORS_ALLOWED_ORIGINS` | app and API-docs origins | Comma-separated origins allowed to call the API. Do not use `*` in production. |
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
log and documentation portal are at `https://docs.crazykok.local`; the
interactive API reference is at `https://api-docs.crazykok.local`. API health is
available at `https://api.crazykok.local/health`. The local SQLite browser
is at `https://db.crazykok.local`. Authentik is exposed at
`https://auth.crazykok.local`. HTTP requests for any configured hostname receive
a permanent 308 redirect to HTTPS. Requests sent to the gateway with any other
hostname receive HTTP 421.

The certificate generator uses `mkcert` when it is installed, which provides a
locally trusted certificate after `mkcert -install`. Otherwise it uses OpenSSL
and the browser will display a certificate trust warning. Generated certificates
and private keys under `docker/certs/` are ignored by Git.

Because `.local` is also used by multicast DNS on macOS, add explicit hosts-file
entries for consistent local resolution:

```text
127.0.0.1 crazykok.local app.crazykok.local api.crazykok.local docs.crazykok.local api-docs.crazykok.local db.crazykok.local auth.crazykok.local idp.crazykok.local
::1       crazykok.local app.crazykok.local api.crazykok.local docs.crazykok.local api-docs.crazykok.local db.crazykok.local auth.crazykok.local idp.crazykok.local
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
API_DOCS_DOMAIN=api-docs.crazykok.com
DB_DOMAIN=db.crazykok.com
AUTH_DOMAIN=auth.crazykok.com
API_DOCS_ORIGIN=https://api-docs.crazykok.com
TRUST_PROXY_HEADERS=true
PUBLIC_API_BASE_URL=https://api.crazykok.com/v1
CORS_ALLOWED_ORIGINS=https://crazykok.com,https://app.crazykok.com,https://api-docs.crazykok.com
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
ADR_AUTHORING_ENABLED=false
DOCS_ORIGIN=https://docs.crazykok.com
AUTHENTIK_SECRET_KEY=GENERATED_LONG_RANDOM_VALUE
AUTH_POSTGRES_PASSWORD=GENERATED_LONG_RANDOM_VALUE
AUTH_GATEWAY_MODE=auth-authentik
FULL_LOGOUT_URL=https://crazykok.com/outpost.goauthentik.io/sign_out
AUTH_API_REQUIRED=true
AUTH_SERVICE_TOKEN=GENERATED_LONG_RANDOM_VALUE
AUTH_OIDC_JWKS_URL=https://auth.crazykok.com/application/o/crazykok-api/jwks/
AUTH_OIDC_ISSUER=https://auth.crazykok.com/application/o/crazykok-api/
AUTH_OIDC_AUDIENCE=crazykok-api
```

Create DNS records for the app, API, docs, API-docs, auth, and private
DB-console subdomains pointing to the gateway/load balancer.
Mount the deployment certificate and key at
`/etc/nginx/certs/localhost.crt` and `/etc/nginx/certs/localhost.key`, or adapt
the gateway configuration to the cloud provider's managed TLS termination.
Expose only ports 80 and 443; the Compose API debug port remains bound to
`127.0.0.1`.

The database console is a local operational editing surface, not a public
product surface. The default sqlite-web service can write to the SQLite volume
and does not publish a host port; access still flows through the local gateway.
In production, do not expose sqlite-web directly and do not switch
`AUTH_GATEWAY_MODE` to `auth-authentik` until authentik has a proxy provider for
the database-console host. If the application later moves from SQLite to a cloud
database via `DATABASE_URL`, keep `DB_DOMAIN` as the stable admin entry point and
redirect or proxy it to the provider-specific console or connection path for
that database.

## Authentication setup

The Compose stack starts authentik by default, but Nginx gateway enforcement is
disabled by `AUTH_GATEWAY_MODE=auth-disabled` until the authentik application,
provider, and outpost are configured. This keeps first boot recoverable instead
of locking the app behind an unconfigured identity provider.

Health endpoints are an explicit exception to browser authentication. Keep
`/health` on the API host and `/healthz` on the gateway unauthenticated so
container orchestrators and external uptime monitors can use them without an
SSO session. These endpoints must expose only coarse availability state; keep
detailed dependency failures, metrics, logs, and administrative diagnostics
behind authentication.

Recommended local sequence:

1. Generate strong values for `AUTHENTIK_SECRET_KEY`, `AUTH_POSTGRES_PASSWORD`,
   and `AUTH_SERVICE_TOKEN` in `.env`.
2. Add `auth.crazykok.local` to `/etc/hosts` and regenerate the local TLS
   certificate.
3. Start the stack and create the initial authentik admin account at
   `https://auth.crazykok.local`.
4. Configure Google as an upstream SSO provider if desired.
5. Create proxy providers/applications for `crazykok.local`,
   `app.crazykok.local`, `api.crazykok.local`, and `db.crazykok.local`, assigning
   only the required users/groups.
6. Ensure the authentik outpost sends `X-authentik-username`,
   `X-authentik-email`, and `X-authentik-groups` headers.
   Configure the normal browser Identification stage as source-only by clearing
   its username/email/UPN user fields and selecting the upstream SSO source.
   Federated users must never enter upstream passwords into authentik.
   Configure `default-source-enrollment-write` to create `internal` users so
   they can enter authentik's user-facing Application Dashboard. Internal users
   do not receive administrator privileges unless those are granted separately.
   Existing federated `external` users must be converted to `internal` once.
7. Set `AUTH_GATEWAY_MODE=auth-authentik` and restart `web`.
8. Configure an OIDC provider/client for API clients and set
   `AUTH_OIDC_JWKS_URL`, `AUTH_OIDC_ISSUER`, and `AUTH_OIDC_AUDIENCE` if direct
   bearer-token API access is required.
9. Set `AUTH_API_REQUIRED=true` and restart `api` once browser and service
   clients have a valid path through the gateway, an OIDC bearer token, or an
   internal service token.

Assign `default-provider-invalidation-flow` as the proxy provider's invalidation
flow and bind the existing `default-invalidation-logout` User Logout stage to
that flow. The application's **Log out** action opens
the gateway's public `/logout` route. In local development, `FULL_LOGOUT_URL`
first ends the disposable Keycloak upstream session and returns to
`/outpost.goauthentik.io/sign_out`, which terminates both the proxy session and
the main authentik session. For another upstream identity provider, configure
`FULL_LOGOUT_URL` with its supported logout chain. Verify that revisiting the
app requires authentication again.

Set `AUTHENTIK_PORTAL_LOGOUT_URL` to the public application `/logout` URL and
apply `authentik/blueprints/crazykok-portal-logout.yaml` to the Authentik
tenant as well. It replaces the brand's dashboard-only invalidation action with a
redirect through the same public `/logout` route, so **Log out** in the
Application Dashboard does not leave the local upstream IdP session alive and
immediately sign the user back in. The blueprint's local route deliberately
delegates the provider-specific behavior to `FULL_LOGOUT_URL`.

The bundled Keycloak stub uses the `crazykok` login theme to auto-submit its
OIDC logout confirmation form. This local-only behavior is needed because the
dashboard redirect cannot provide Keycloak's ID-token hint; it must not be
copied to a production identity provider. Production Google logout continues
to end only the CrazyKok and Authentik sessions as described below.

For Google federation, use the application-host Authentik sign-out URL shown in
the production example. This clears CrazyKok and authentik without attempting
to terminate the user's wider Google browser session. A subsequent login can
therefore reuse Google SSO without asking for the Google password again; use a
private browser session when a test must begin without any upstream identity
session.

Brand the authentik tenant for the authentication domain with the CrazyKok
title, logo, and favicon, and title the browser authentication flow **Sign in to
CrazyKok**. The gateway exposes `/crazykok-logo.png` without authentication so
the cross-origin authentik login screen can load the existing application logo;
do not expose other application assets as part of this exception.

Use authentik's User Interface at `https://auth.crazykok.local/if/user/` as the
application portal. Keep the brand's default application unset so the overview
opens the dashboard, and give each published application an explicit HTTPS
launch URL and icon. CrazyKok uses `https://crazykok.local` as its launch URL.
The dashboard tile starts the application's normal service-provider flow; do
not weaken OAuth callback validation to accept unsolicited upstream responses.

Apply `authentik/blueprints/crazykok-db-admin.yaml` to publish the database
administrator as a separate proxy application. Set `AUTHENTIK_DB_PUBLIC_URL`
to its public HTTPS origin and assign database administrators to the
`CrazyKok Operators` group. The application's group binding both hides its
library tile from other users and denies direct access to the DB host. Do not
reuse the main CrazyKok proxy provider: Authentik selects forward-auth
providers by external host, and an unregistered host makes the Nginx auth
subrequest fail.

The docs site is generated from `docs/adr/` during the web image build and has
no database or runtime API dependency. Rebuild and deploy the web image after
committed ADR changes. Do not mount the repository into the public web
container. The internal authoring endpoints are explicitly blocked by Nginx;
keep `ADR_AUTHORING_ENABLED=false` as an independent production safeguard.

The `api-data` volume contains both SQLite and venue attachments. Back up and
restore them together so attachment metadata and bytes remain consistent.
Archiving a venue or attachment record does not immediately delete its bytes;
orphan cleanup should run only after a verified backup.

The API-reference image is separate from both the application frontend and the
API. It vendors the pinned Scalar browser assets at build time and fetches the
canonical OpenAPI document through its own narrow Nginx proxy. Browser "try it"
requests go directly to the advertised API server, so the API-docs origin must
remain in the explicit CORS allowlist.

## Post-deployment verification

After the application URL is serving the new release, invoke
`.github/workflows/post-deploy-e2e.yml` with that URL. The workflow runs the
read-only Playwright `@smoke` journey as the final deployment layer and uploads
its browser report when it fails. Deployment workflows can call it as a
reusable workflow; operators can also run it manually from GitHub Actions.

Do not point the full mutating E2E suite at production. Create/edit/archive and
CSV-import journeys run before deployment against Playwright's disposable API
and SQLite database.
