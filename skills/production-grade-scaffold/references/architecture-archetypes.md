# Architecture Archetypes - how the six-layer model bends per project type

The six layers (Presentation / API / Domain Logic / Data Access / Database / Infrastructure) are
a **default lens**, not a law. Different project shapes keep all six, collapse some together, or
drop others entirely. Decide the archetype *before* picking a template or applying a checklist -
applying the wrong archetype's assumptions is how a "production grade" scaffold ends up wrong
(e.g. wiring a connection pool into a serverless function, or forcing REST conventions onto a
raw TCP protocol service).

Decide the archetype by answering: does this project (a) render UI, (b) run as a long-lived
process, and (c) speak an application-level request/response protocol (REST/GraphQL/RPC)?

## 1. Layered Web App / API service (the original default)
Persistent server process, exposes REST/GraphQL/gRPC, owns a database. All six layers apply
mostly unchanged. Templates: `nodejs-typescript/`, `python-fastapi/`, `rust-axum/`.

## 2. Full-stack SSR framework (Next.js, Nuxt, Remix, SvelteKit)
Presentation and API layers **physically merge** - Route Handlers / Server Actions / loaders live
next to the components that call them, in the same framework. Don't force a separate `api/`
top-level folder; instead keep API/data-fetching code colocated per-route but still import from
a shared `domain/` and `data-access/` that stays framework-free. The framework layer itself
becomes part of "Presentation," not a new layer. CSRF/CORS defaults differ: same-origin Server
Actions get built-in CSRF protection in most of these frameworks - verify the framework's
specific guarantee rather than assuming Express-style CORS rules apply. See `templates/nextjs-fullstack/`.

## 3. Serverless API (Lambda, Cloud Functions, Vercel/Cloudflare Functions)
- **No persistent process** - every "connection pool" assumption breaks. Never open a raw
  connection pool per invocation; use a serverless-aware pooler (RDS Proxy, PgBouncer in front,
  or a driver built for edge/serverless like Neon's or PlanetScale's HTTP-based drivers) - see
  `references/database.md`'s pooling section, but treat pool *lifetime* as per-container-reuse,
  not per-app.
- **Infrastructure layer changes shape**: no Dockerfile/docker-compose for the app itself (the
  platform supplies the runtime); IaC becomes the serverless framework's own config (SAM template,
  `serverless.yml`, or CDK/Terraform provider for the specific platform) rather than generic
  Terraform+Kubernetes.
- **Cold start is a first-class concern**: keep the dependency graph small, initialize expensive
  clients (DB, HTTP) lazily and outside the handler body so they survive container reuse.
  Structured logging still applies; tracing needs the platform's own OTel integration (most
  don't support a sidecar).
- **Observability**: no long-lived process to attach a metrics scraper to - rely on the
  platform's native metrics/logs export plus OpenTelemetry where supported, rather than
  self-hosted Prometheus.
- Auth/security/API-layer checklists (`references/security.md`, `auth.md`, `api-layer.md`)
  apply unchanged - a serverless function is still an API endpoint. See `templates/serverless-api/`.

## 4. Networking / systems service (raw sockets, custom protocols, proxies, IoT gateways)
This archetype does **not** fit the REST/DB layered model at all - don't force it.
- There is usually no "API layer" in the REST sense; replace it with a **protocol/transport
  layer** (framing, serialization, connection lifecycle) and a **session/state layer** in place
  of a traditional database-backed domain layer, if state is kept at all.
- Security checklist shifts entirely: mutual TLS (mTLS) or protocol-level auth instead of
  OAuth2/JWT bearer tokens; connection-level rate limiting and backpressure instead of
  HTTP-request rate limiting; strict input framing/length-prefixing to prevent
  buffer-overrun-style parsing bugs takes the place of "sanitize HTML output."
  Domain-Driven Design's Entities/Aggregates still apply if there's meaningful business state,
  but there frequently isn't - many networking services are closer to a pure protocol
  implementation than a domain model.
- CI/CD, observability, and IaC checklists from `references/infrastructure-delivery.md` still
  apply close to unchanged (fuzz testing is worth adding to the CI pipeline here specifically,
  given the parser-bug risk above).
- There is no single "right" folder structure here the way there is for a REST service - see
  `templates/networking-service/` for a skeleton and read its README, but expect to hand-adapt
  more than with the other archetypes.

## Choosing within an archetype
Once the archetype is fixed, still detect the concrete stack (Node/TS, Python, Rust, Go, ...) the
same way as before - package.json / pyproject.toml / Cargo.toml / go.mod - and use the matching
concrete template if one exists, or `templates/generic-layered/` adapted by hand if not.
