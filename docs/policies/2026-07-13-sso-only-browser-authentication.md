# SSO-Only Browser Authentication

Date: 2026-07-13
Source: Product direction from project owner

## Policy

Every browser-facing CrazyKok surface that requires access must authenticate
people through an upstream single sign-on provider. CrazyKok must not issue or
operate routine end-user usernames and passwords, password policies, password
reset flows, or local-password onboarding.

authentik remains the identity broker and gateway, not the end-user account
system. It retains only the federated subject, verified identity attributes,
and authorization assignments needed to support SSO. Google is the first
intended upstream provider, with other enterprise SSO providers added when
needed.

## Exceptions And Service Access

- Keep one tightly controlled local authentik administrator only as a
  break-glass recovery path for the identity service. It is not a normal user
  login and must not be assigned ordinary application access.
- Use dedicated service identities for machine-to-machine and API access:
  OAuth/OIDC client credentials where available, or the scoped internal service
  token during the initial transition. Never use a shared human administrator
  account for service traffic.
- Interactive API users authenticate with an authentik-issued OIDC bearer token
  after completing SSO.

## Operational Follow-Up

Before gateway enforcement is enabled, configure the upstream SSO source,
provider/application/outpost assignments for each protected host, the
break-glass recovery procedure, and service credentials with rotation rules.

## Related Decisions

- `docs/adr/0031-self-hosted-authentication-service.md`
- `docs/GOOGLE_SSO_ENABLEMENT.md`
