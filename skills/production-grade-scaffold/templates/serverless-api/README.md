# Serverless API Production Scaffold

Generated from the `production-grade-scaffold` skill. Read references/architecture-archetypes.md
section 3 first - this archetype breaks the "persistent connection pool" and "Dockerfile"
assumptions the other templates make. Layer mapping:

- src/handlers/      - one entry point per function (the "API layer," minus the persistent server)
- src/domain/        - entities, value objects, domain events - framework-free
- src/data-access/   - repositories, unit of work (per-invocation scoped)
- serverless.yml     - IaC for this archetype (swap for SAM/CDK if preferred)
- infra/             - supplemental infra notes

Before first deploy, walk the "Minimum bar" checklists in ../../references/*.md, and specifically
re-check the database pooling guidance in architecture-archetypes.md #3 - this is the most common
mistake when adapting a traditional-server scaffold to serverless.

Setup:
1. `cp .env.example .env` and fill in real values (never commit `.env`).
2. `npm install`
3. `npm run build`
4. `npm run deploy` (requires AWS credentials configured, or swap the provider block in serverless.yml)
