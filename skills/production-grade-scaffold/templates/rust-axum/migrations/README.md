# Migrations

Managed by `sqlx migrate` (or swap for your tool of choice) - imperative, checksummed,
roll-forward only. For destructive changes use Expand -> Dual-write -> Backfill -> Cutover -> Contract.
Run `sqlx migrate add <name>` to create the first migration. See references/database.md.
