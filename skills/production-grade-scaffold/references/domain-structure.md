# Domain & Project Structure Reference

## Strategic design (decide this before writing any code)
- Establish a **Ubiquitous Language** - one vocabulary shared by developers and domain experts, used consistently in code, docs, and conversation. A mismatch here (devs saying "user", business saying "member") is a recurring source of translation bugs.
- Partition the system into **Bounded Contexts** aligned to business capabilities (e.g. "Billing", "Fulfillment"), not to technical layers ("the database team's stuff"). This is the top-level module or service boundary, decided before any monolith-vs-microservice conversation.
- Use an **Anti-Corruption Layer** at any boundary where your clean domain model meets a legacy system or third-party API - an adapter/facade that translates their model into yours, so external mess doesn't leak inward.

## Tactical building blocks (inside a bounded context)
- **Entities** - objects with identity that persists across state changes.
- **Value Objects** - immutable, defined entirely by their attributes, no identity. Default to this unless the object genuinely needs identity - most "small" domain concepts should be value objects, not entities.
- **Aggregates** - a cluster of entities/value objects with a single **Aggregate Root** as the only external entry point and the transactional/consistency boundary. Keep aggregates small; a large aggregate becomes a concurrency bottleneck (see database.md on lock contention).
- **Domain Events** - immutable, past-tense-named records of something that happened (`OrderPlaced`, not `PlaceOrder`), dispatched via the Unit of Work after a successful commit, used to decouple cross-aggregate side effects instead of reaching directly into another aggregate.

## Monolith vs. microservices
- Default to a **Modular Monolith**: single deployable, single database, but strict module isolation enforced in code - no cross-module foreign keys, communication only through defined interfaces or in-process events. This is the easiest architecture to operate correctly and the easiest to later split.
- Treat the decision to go to microservices as primarily **organizational** (Conway's Law, independent team scaling) rather than purely technical. Only split out a service when independent deployability or independent scaling is a real, current need - microservices inherit distributed-systems complexity for free: no cross-service joins, eventual consistency, network partition handling.
- Distributed transactions across services: use the **Saga** pattern with explicit compensating actions (choreography for 2-3 simple steps, orchestration for complex/branching workflows) instead of two-phase commit, which doesn't hold up well under partial failure at scale.
- Migrate from monolith to services via the **Strangler Fig** pattern: identify a seam -> intercept at the gateway -> build the new service -> sync data via CDC -> cut traffic over behind a feature flag -> retire the old code path. Never attempt a big-bang rewrite.
- An API Gateway / BFF sits at the boundary between external clients and internal bounded contexts, acting as an outward-facing Anti-Corruption Layer as well as the auth/rate-limit enforcement point (see api-layer.md, auth.md).

## Folder structure mapping (layer -> module, stack-agnostic)
```
presentation/      # UI components, client state, frontend security controls
api/                # Route/controller definitions, request/response DTOs, auth middleware, rate limiting
domain/             # Entities, value objects, aggregates, domain events, business rules - no framework imports
data-access/        # Repositories, Unit of Work, ORM/query code, caching
database/           # Migrations, schema definitions, seed data
infrastructure/      # Docker, CI/CD config, IaC, observability wiring, config/secrets loading
```
The critical rule: dependencies point inward only. `domain/` never imports a specific web framework or ORM class; `api/` and `data-access/` depend on `domain/`'s interfaces, not the reverse. This is what makes the domain layer testable in isolation and swappable at the edges (change ORMs, change web frameworks, without touching business logic).

## Minimum bar before calling project structure "production grade"
1. Business logic (`domain/`) has zero imports from a web framework or ORM.
2. Module/bounded-context boundaries are enforced (no cross-module direct DB access; communicate through interfaces or events).
3. A new engineer can name which bounded context owns a given piece of business logic without asking.
4. There is an explicit, written decision (even one paragraph) for monolith-vs-microservices, not an implicit default nobody chose.
