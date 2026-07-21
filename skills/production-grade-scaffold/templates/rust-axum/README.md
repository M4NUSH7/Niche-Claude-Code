# Rust / Axum Production Scaffold

Generated from the `production-grade-scaffold` skill. Layer mapping:

- src/api/           - routes, DTOs, auth + rate-limit tower layers
- src/domain/        - entities, value objects, domain events - no axum/sqlx imports
- src/data_access/   - repositories, unit of work (sqlx transactions)
- migrations/        - sqlx migrations
- infra/             - Terraform/Pulumi
- .github/workflows/ - CI pipeline (clippy -> fmt -> test -> build+sign)

Before first deploy, walk the "Minimum bar" checklists in ../../references/*.md.

Setup:
1. `cp .env.example .env` and fill in real values (never commit `.env`).
2. `docker compose up -d db redis`
3. `cargo install sqlx-cli` then `sqlx migrate run`
4. `cargo run`
