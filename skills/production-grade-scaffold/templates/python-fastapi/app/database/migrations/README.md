# Migrations

Managed by Alembic - imperative, checksummed, roll-forward only. For destructive changes use
Expand -> Dual-write -> Backfill -> Cutover -> Contract. See references/database.md.
Run `alembic init app/database/migrations` after installing dependencies to scaffold Alembic itself.
