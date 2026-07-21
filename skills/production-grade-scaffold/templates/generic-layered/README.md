# Generic Layered Template (stack-agnostic)

Use this as the reference model when no concrete template exists for your language (Go, Java, Rust, etc.).
Folder *names* below are conventions - adapt to the idioms of your language/framework - but the
*boundaries* and dependency direction must hold regardless of stack. See ../../references/domain-structure.md.

```
presentation/     UI/rendering, client-side state, frontend security controls
api/              Route/controller definitions, DTOs, auth middleware, rate limiting
domain/           Entities, value objects, aggregates, domain events - NO framework/ORM imports
data-access/       Repositories, Unit of Work, ORM/query code, caching
database/         Migrations, schema definitions, seed data
infrastructure/   Docker, CI/CD config, IaC, observability wiring, config/secrets loading
```

Rule: dependencies point inward only. `domain/` must never import a web framework or ORM class.
