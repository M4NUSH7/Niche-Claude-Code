# Repositories

Scoped to an Aggregate Root, not a raw table. Return domain entities/value objects only - never
leak an `sqlx::query!` result type or `Row` through a repository's public trait. See references/database.md.
