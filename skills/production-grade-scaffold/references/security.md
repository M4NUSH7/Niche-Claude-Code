# Security Reference

Defense-in-depth: assume every layer can fail independently and stack controls so no single miss is fatal.

## Output handling & injection
- Sanitize untrusted output with allowlisting (DOMPurify-style: allowed tags/attrs, not a blocklist).
- Never trust framework auto-escaping alone as the sole control on user-generated content that gets rendered as HTML.
- Centralize any raw-HTML-rendering sink into one vetted component/module; forbid ad-hoc use elsewhere in application code - this makes the one sink auditable.

## Content Security Policy & headers
- Server-rendered apps: nonce-based CSP (`script-src 'nonce-<random-per-request>' 'strict-dynamic'`). Never reuse a static/global nonce.
- Static/pre-rendered output: SHA-256 hash-based CSP for known script content.
- Clickjacking: CSP `frame-ancestors` directive (modern browsers) plus `X-Frame-Options: DENY/SAMEORIGIN` as legacy fallback.
- Sandbox any third-party/untrusted embedded iframe content (`sandbox` attribute with minimal allowed permissions).

## CSRF & CORS
- Prefer `SameSite=Lax` or `Strict` cookies plus a mandatory custom header (e.g. `X-Requested-With` or a custom token header) over legacy stateful synchronizer-token CSRF defenses for API-driven SPAs - the custom header forces a CORS preflight, which a cross-site form post cannot trigger.
- CORS: never dynamically reflect the `Origin` header when `Access-Control-Allow-Credentials: true` is set. Maintain a static, centrally-audited allowlist of origins, enforced at the gateway/edge layer, not scattered per-service.

## Supply chain
- Subresource Integrity (SRI) hashes on any CDN-hosted script/stylesheet.
- Automated dependency vulnerability scanning wired into CI (npm audit/Snyk/Dependabot or the language-appropriate equivalent) - fail the build on high/critical findings.
- Build artifacts: generate an SBOM, sign images with Cosign/Sigstore (keyless), attach SLSA provenance metadata. Treat the signed artifact as immutable and promote the same one across environments rather than rebuilding per-environment.

## Secrets & token handling
- Never persist access/refresh tokens in `localStorage` or `sessionStorage` - both are readable by any script, so one XSS bug becomes full account takeover.
- Preferred pattern: Backend-for-Frontend (BFF) holds OAuth tokens server-side (in a cache like Redis) and issues only an HttpOnly + Secure + SameSite session cookie to the browser. This removes the entire "token exfiltration via XSS" risk category regardless of frontend framework.
- Native/mobile clients: store tokens in OS-backed secure storage (Keychain on iOS, Keystore on Android), never in app-readable plain storage.
- Secrets at the infrastructure layer: mount via tmpfs, not baked into disk/image layers; rotate regularly; never commit to version control (enforce with a pre-commit secret scanner).

## Request integrity
- HMAC-sign webhook payloads and other high-value server-to-server calls: include a timestamp and nonce, verify with constant-time comparison, reject requests outside a tight time window to block replay.
- Rate limiting is also a security control against volumetric and application-layer DDoS: coarse IP-based limits at the edge/WAF, fine-grained identity-based limits at the API gateway (see `api-layer.md`).

## Container & platform hardening
- Run containers as a non-root user; drop all Linux capabilities by default and re-add only the minimum required.
- Read-only root filesystem where the runtime allows it; write only to explicitly mounted volumes/tmpfs.
- Apply seccomp/AppArmor profiles rather than running unconfined.
- Pin image references to a digest (`image@sha256:...`), never a mutable tag like `latest`.
- Static analysis on infrastructure-as-code (Checkov/TFLint or equivalent) gating CI merges; run infra integration tests in a sandboxed environment, not against shared/live infra.

## Minimum bar before calling something "production grade"
1. All user-facing input is validated server-side (never trust client-side validation as the only gate).
2. CSP, CORS, and CSRF controls above are configured, not left at framework defaults.
3. Dependency scanning and secret scanning both run in CI and block merge on failure.
4. No long-lived secret or token lives in browser storage or a public repo.
5. Containers/images meet the hardening bullets above before first production deploy.
