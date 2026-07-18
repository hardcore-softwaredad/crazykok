# Google SSO Enablement

## Purpose

Enable Google as the upstream identity provider for browser users. authentik
remains the authentication and authorization broker; it stores only the
federated identifier and profile data needed to map a verified identity to
CrazyKok access policy.

## Google Cloud Handoff

Create a Google OAuth **Web application** client and supply its client ID and
secret only through deployment secrets. Register this exact redirect URI:

```text
https://auth.crazykok.com/source/oauth/callback/google/
```

The `auth.crazykok.com` domain must be reachable over trusted HTTPS and
registered as an authorized Google domain. `.local` hostnames are not valid
Google production redirect hosts; use the production host or `localhost` for
isolated OAuth testing.

Request only `openid`, `email`, and `profile`. Choose one access policy before
rollout: allowlisted individual emails, a Google Workspace domain, or explicitly
approved external users. The default recommendation is an allowlist until a
Workspace-domain policy is needed.

## Authentik Configuration

1. Create the local-only Authentik recovery administrator and store its
   recovery path separately from ordinary user access.
2. Set `AUTHENTIK_GOOGLE_CLIENT_ID` and
   `AUTHENTIK_GOOGLE_CLIENT_SECRET` in deployment secrets.
3. Import `authentik/blueprints/crazykok-google-sso.template.yaml` as a
   blueprint instance, then add the Google source to the browser authentication
   flow. The blueprint configures source-enrolled users as authentik `internal`
   users so they can access the user-facing Application Dashboard; this does
   not make them administrators.
4. Remove local password stages from the browser-user flow; retain local admin
   access only for identity-service recovery.
5. Create forward-auth application/provider entries for the app, direct API,
   and database console, attach them to the embedded proxy outpost, and bind
   the chosen access policy. Give each application an explicit HTTPS launch URL
   and icon so authorized users can launch it from authentik's dashboard.
6. Verify unauthenticated redirect, Google sign-in, rejected-user behavior,
   logout, and forwarded identity headers before enabling the gateway.

## Local Federation Stub

The Compose stack includes `idp-stub`, a disposable Keycloak OpenID Connect
provider at `https://idp.crazykok.local`. It is local-only and exists solely to
exercise the same upstream federation boundary used by Google.

Add `idp.crazykok.local` to the local hosts file, regenerate the local
certificate with `./scripts/generate-local-cert.sh`, and restart the stack.
The seeded Keycloak realm is `crazykok-local`. Its local-only fixtures are:

| Purpose | Username | Password |
| --- | --- | --- |
| Authentik recovery administrator | `admin` | `local-authentik-admin` |
| Keycloak admin console | `admin` | `local-idp-admin` |
| Federated operator test user | `operator` | `local-operator` |
| Federated viewer test user | `viewer` | `local-viewer` |

These credentials are deliberately non-secret fixtures and must never be used
outside local development. Override the administrator values with
`IDP_STUB_ADMIN_USERNAME` and `IDP_STUB_ADMIN_PASSWORD` if a local environment
needs different values. The Authentik recovery administrator signs in at
`https://auth.crazykok.local/if/admin/`; it is for identity-service
administration only, never for normal app access.

The Compose configuration assigns `idp.crazykok.local` as an internal alias for
the web gateway and mounts the generated local certificate as a trusted CA in
Authentik. This lets Authentik securely retrieve the Keycloak discovery document
without weakening TLS verification.

Import `authentik/blueprints/crazykok-local-oidc-stub.template.yaml` to create
the authentik source. It uses the Keycloak discovery document and callback
`https://auth.crazykok.local/source/oauth/callback/local-oidc/`. Add that
source to the local browser authentication flow before enabling gateway auth.
Configure the flow's Identification stage with no username, email, or UPN user
fields and select only the `Local OIDC Stub` source. With one source, authentik
redirects browser users to Keycloak instead of offering its local-password
stages. Enter `operator` / `local-operator` on the Keycloak page, never in an
authentik password form. Keep authentik's `/if/admin/` route as the separate
local recovery-administrator entry point.

## Enablement

Set `AUTH_GATEWAY_MODE=auth-authentik` only after those checks pass. The current
Nginx configuration then redirects browser traffic to the authentik outpost and
forwards the verified identity headers to the app and API. Keep API machine
access on dedicated OIDC/service credentials; it is independent of browser SSO.

## References

- `docs/adr/0031-self-hosted-authentication-service.md`
- `docs/policies/2026-07-13-sso-only-browser-authentication.md`
- `docs/DEPLOYMENT.md#authentication-setup`
