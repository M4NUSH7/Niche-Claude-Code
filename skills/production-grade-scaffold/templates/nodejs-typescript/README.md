# Node.js / TypeScript Production Scaffold

Generated from the `production-grade-scaffold` skill. Layer mapping:

- src/presentation/  - if this is a full-stack app; otherwise omit for API-only services
- src/api/           - routes, DTOs, auth + rate-limit middleware
- src/domain/        - entities, value objects, domain events - no framework/ORM imports
- src/data-access/   - repositories, unit of work
- src/database/      - migrations (Prisma Migrate by default)
- infra/             - Terraform/Pulumi
- .github/workflows/ - CI pipeline (lint -> test -> SAST -> integration -> build+sign)

Before first deploy, walk the "Minimum bar" checklists in ../../references/*.md.

Setup:
1. `cp .env.example .env` and fill in real values (never commit `.env`).
2. `cp prisma-schema.prisma.example prisma/schema.prisma` after `npx prisma init`.
3. `npm install`
4. `docker compose up -d db redis`
5. `npm run migrate:dev`
6. `npm run dev`
