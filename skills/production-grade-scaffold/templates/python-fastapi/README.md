# Python / FastAPI Production Scaffold

Generated from the `production-grade-scaffold` skill. Layer mapping:

- app/presentation/    - omit for API-only services
- app/api/             - routes, schemas, auth + rate-limit middleware
- app/domain/          - entities, value objects, domain events - no framework/ORM imports
- app/data_access/     - repositories, unit of work
- app/database/        - migrations (Alembic by default)
- infra/               - Terraform/Pulumi
- .github/workflows/   - CI pipeline (lint -> type check -> SAST -> test -> build+sign)

Before first deploy, walk the "Minimum bar" checklists in ../../references/*.md.

Setup:
1. `cp .env.example .env` and fill in real values (never commit `.env`).
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install -e ".[dev]"`
4. `docker compose up -d db redis`
5. `alembic upgrade head`
6. `uvicorn app.api.server:app --reload`
