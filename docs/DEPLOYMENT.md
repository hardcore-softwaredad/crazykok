# Deployment

## Environment contract

Configuration follows the twelve-factor convention: deploy-specific values are
provided through environment variables. Copy `.env.example` to `.env` for local
overrides. Docker Compose also contains the same safe defaults, so running with
no `.env` file stays in development and only serves `.localhost` names.

| Variable | Safe default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | Runtime mode; set explicitly by each deployment. |
| `APP_DOMAIN` | `app.localhost` | Browser application virtual host. |
| `API_DOMAIN` | `api.localhost` | Direct API virtual host. |
| `CORS_ALLOWED_ORIGINS` | `https://app.localhost` | Comma-separated origins allowed to call the API. Do not use `*` in production. |
| `WEB_PORT` | `80` | HTTP port; valid app/API hosts redirect to HTTPS. |
| `HTTPS_PORT` | `443` | HTTPS port for the Nginx gateway. |
| `API_PORT` | `8000` | Loopback-only host port for direct API debugging. |
| `DATABASE_URL` | `sqlite:////data/app.db` | SQLAlchemy database URL. |

The frontend uses the same-origin `/api` route through Nginx. The API is also
available directly at `https://api.localhost`; this keeps the frontend simple
while reserving a distinct API subdomain for clients and future deployment.

## Local Docker

```sh
cp .env.example .env
./scripts/generate-local-cert.sh
docker compose up --build
```

Open `https://app.localhost`. API health is available at
`https://api.localhost/health`. HTTP requests for either configured hostname
receive a permanent 308 redirect to HTTPS. Requests sent to the gateway with
any other hostname receive HTTP 421.

The certificate generator uses `mkcert` when it is installed, which provides a
locally trusted certificate after `mkcert -install`. Otherwise it uses OpenSSL
and the browser will display a certificate trust warning. Generated certificates
and private keys under `docker/certs/` are ignored by Git.

`.localhost` and its subdomains are reserved for loopback use. The local hosts
file may additionally contain these explicit entries for consistent resolver
behavior:

```text
127.0.0.1 app.localhost api.localhost
::1       app.localhost api.localhost
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
APP_DOMAIN=app.crazykok.com
API_DOMAIN=api.crazykok.com
CORS_ALLOWED_ORIGINS=https://app.crazykok.com
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

Create DNS records for both subdomains pointing to the gateway/load balancer.
Mount the deployment certificate and key at
`/etc/nginx/certs/localhost.crt` and `/etc/nginx/certs/localhost.key`, or adapt
the gateway configuration to the cloud provider's managed TLS termination.
Expose only ports 80 and 443; the Compose API debug port remains bound to
`127.0.0.1`.
