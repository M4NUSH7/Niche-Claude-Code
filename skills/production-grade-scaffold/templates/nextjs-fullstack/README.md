# Next.js Full-Stack Production Scaffold

Generated from the `production-grade-scaffold` skill. See references/architecture-archetypes.md
section 2 for how Presentation+API merge in this archetype. Layer mapping:

- src/app/           - pages, layouts, Route Handlers/Server Actions (Presentation + API merged)
- src/domain/        - entities, value objects, domain events - framework-free
- src/data-access/   - repositories, unit of work
- src/database/      - migrations (Prisma Migrate by default)
- infra/             - supplemental infra (DB, Redis) not managed by the hosting platform

Before first deploy, walk the "Minimum bar" checklists in ../../references/*.md.

Setup:
1. `cp .env.example .env` and fill in real values (never commit `.env`).
2. `npx prisma init` then point it at src/database/migrations.
3. `npm install`
4. `npm run migrate:dev`
5. `npm run dev`
