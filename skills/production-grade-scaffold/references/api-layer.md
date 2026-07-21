# API Layer Reference

## Resource design
- Nouns, not verbs; plural resource names; kebab-case paths; nesting no more than two levels deep (`/orders/{id}/items`, not four levels down).
- Use HTTP verbs with their correct safety/idempotency semantics: GET, PUT, DELETE are idempotent; POST is not - design retry behavior around this.
- Require an `Idempotency-Key` header on POST endpoints that create financial or otherwise critical, hard-to-undo mutations, so client retries under network partition don't double-execute.

## Status codes & versioning
- 201 + `Location` header on resource creation; 202 for accepted-async work; 204 for empty success bodies; 409 for conflicts/optimistic-lock failures; 429 for rate limiting. Consistent status-code discipline is itself part of the API's contract.
- Version via URI (`/v1/...`) rather than header/media-type/query-param versioning - less "pure" REST in theory, but meaningfully better tooling, caching, debugging, and ecosystem fit in practice.
- Publish an OpenAPI spec as the design-first source of truth, not generated after the fact - it enables parallel frontend/backend work and generated docs/SDKs.

## Pagination & payload shape
- Prefer cursor-based pagination over offset/limit once a resource can grow large - offset pagination degrades in performance and correctness under concurrent writes (page drift).
- Support field-selection / partial responses for large resources to avoid over-fetching on constrained clients.

## Rate limiting & throttling
- Algorithm choice depends on traffic shape:
  - **Token Bucket** - best for public APIs that should tolerate legitimate bursts; memory-light.
  - **Leaky Bucket** - best for smoothing into async queues/workers.
  - **Sliding Window Counter** - the general-purpose default; near-log-scale accuracy with fixed-window-like memory cost. Use this unless a specific traffic shape argues for one of the others.
- Reject over-limit requests with 429 for synchronous APIs; only queue/throttle (rather than reject) for internal async work.
- Distributed rate limiting needs centralized state - Redis with atomic Lua scripts, not per-instance in-memory counters (which under-enforce limits once there's more than one replica) and not distributed locks (too slow for this).
- Standard response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. Client SDKs should implement exponential backoff with jitter on 429s, not naive immediate retry (which causes thundering-herd retry storms).
- For multi-tenant SaaS, apply layered limits: global -> tenant -> user -> endpoint, so one noisy tenant can't exhaust the global budget.

## Minimum bar before calling the API layer "production grade"
1. An OpenAPI spec exists and is kept in sync with the actual implementation (ideally generated from or validated against code).
2. Status codes are used consistently per the table above, not ad hoc per endpoint.
3. Rate limiting is enforced centrally (not per-instance) and returns the standard headers.
4. Pagination is cursor-based for any resource expected to grow past a few thousand rows.
5. Idempotency keys are required on critical financial/mutating POST endpoints.
