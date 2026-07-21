# Auth Reference

## First principle: separate AuthN from AuthZ
Authentication (who is this) and authorization (what can they do) are different concerns with different failure modes. OAuth2 by itself is an *authorization* framework; OIDC layers *identity* (authentication) on top of it. Conflating the two - e.g. treating "has a valid token" as "is allowed to do this specific thing" - is a recurring root cause of access-control vulnerabilities.

## Flow selection by client type
| Client type | Flow | Notes |
|---|---|---|
| Browser SPA / native / mobile app | Authorization Code + PKCE | The only flow that should be used for public clients. Deprecate the Implicit grant entirely - tokens leak via URL fragments, browser history, and referrer headers. |
| Service-to-service (backend to backend) | Client Credentials | Scope the issued token narrowly. Do not treat "inside the private network" as an authorization boundary by itself. |
| Multi-hop call chains (service A -> B -> C) | Token Exchange (RFC 8693) | Re-scope/re-issue a token at each hop rather than forwarding the original caller's token unchanged - this bounds the blast radius if one downstream service is compromised. |
| First-party trusted server rendering pages | Session cookie via BFF | See below - the browser never sees the OAuth token at all. |

## Token architecture
- Prefer asymmetric signing (RS256 with a JWKS endpoint) over shared-secret HS256 once more than one service needs to verify tokens - HS256 requires distributing the same secret everywhere, which doesn't scale securely.
- JWS (signed) is not the same as JWE (encrypted) - a signed JWT's payload is base64, not secret, and can be read by anyone who has the token. Use JWE only when the payload itself must stay confidential across an untrusted intermediary.
- Validate signature, `exp`, and `aud` (audience) at the API gateway edge, before a request reaches internal services - don't let every microservice re-implement token validation slightly differently.
- Backend-for-Frontend (BFF) pattern: hold OAuth access/refresh tokens server-side (e.g. in Redis), issue the browser only an HttpOnly + Secure + SameSite session cookie. Removes XSS-driven token theft as a risk category, independent of what frontend framework is used.

## Authorization model
- Claim/scope-based RBAC or ABAC, expressed either as JWT claims or gateway-enforced scopes - pick one source of truth and enforce it consistently rather than re-deriving permissions ad hoc in each service.
- API keys identify a caller (useful for metering / rate-limit tiering) but are not authentication or authorization - never gate user-level data access on an API key alone, and never embed API keys in client-side or mobile app code where they can be extracted.
- MFA is a cross-cutting concern best enforced at the identity provider / BFF layer, not duplicated per service.

## Minimum bar before calling auth "production grade"
1. No Implicit grant anywhere in the codebase; PKCE is present on every public-client Authorization Code flow.
2. Tokens are never stored in `localStorage`/`sessionStorage` in the browser.
3. Every service validates `exp`/`aud`/signature on tokens it accepts - token validation is not "trust the gateway already checked it" without an explicit contract.
4. Scopes/roles are defined and enforced per-endpoint, not just per-service.
5. Service-to-service calls carry their own scoped credentials, not a forwarded end-user token, once more than two hops are involved.
