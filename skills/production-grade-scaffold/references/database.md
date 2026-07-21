# Database Reference

## Transactions & isolation
- ACID is the contract: Atomicity (undo/rollback), Consistency (constraints + app invariants), Isolation (configurable level), Durability (WAL + fsync).
- Default to **Read Committed** for general OLTP traffic. Escalate to **Serializable** only where strict invariants matter (financial balances, inventory counts), and pair it with app-level retry-with-backoff on serialization failures - Serializable transactions are expected to abort under contention, that's not a bug.
- Design against known anomalies rather than picking an isolation level by habit: dirty read, non-repeatable read, phantom read, serialization anomaly. Choose the level based on which of these the specific operation can tolerate.
- Deadlocks are inevitable in any concurrent system. Mitigate structurally: consistent lock ordering across code paths, short transactions (don't hold a transaction open across a network call or user think-time), row-level locking over table-level, and a generic retry-with-backoff wrapper around the transaction/repository boundary.

## Migrations
- Use imperative, checksummed, ordered migration scripts (Flyway/Liquibase-style with a migration-history table) rather than state-based schema diffing - more predictable and auditable in production.
- Migrations are append-only forward evolution: never edit a script that has already been applied to any environment. If a change is wrong, write a new corrective migration.
- Prefer roll-forward only. "Down" migrations are frequently logically impossible once data has been transformed or deleted - don't rely on them as a safety net; a tested corrective forward migration is the real rollback plan.
- Separate DDL (fast, metadata-only) from DML/data backfills (slow, lock-heavy). Never run a large data transformation in the same pipeline step as a schema change - run backfills out-of-band in throttled batches.
- For any destructive/breaking schema change (column rename, drop, type change), use the **Expand -> Dual-write -> Backfill -> Cutover reads -> Contract** sequence, coordinated with app deploy ordering so no deployed version reads/writes a shape that doesn't exist yet.

## Connection management
- Connection pooling is mandatory for any non-trivial-throughput service - establishing a raw connection per request incurs TCP + TLS + auth handshake overhead that saturates DB CPU/memory well before query load does.
- App-level pools (HikariCP-style) suit monoliths with a small, stable number of instances. Middleware poolers (PgBouncer in transaction-pooling mode) suit microservices/serverless, where N service instances  per-instance pool size would otherwise explode the database's real connection count.
- Size pools with Little's Law (`L =   W`) rather than guessing - oversized pools cause CPU context-switching and lock contention, not more throughput. Rough starting point for Postgres: `(core_count * 2) + effective_spindle_count`, then tune from observed queueing.
- Configure a full timeout matrix, not just "the pool exists": connection-acquire timeout (fail fast, ~2s), socket/read timeout (mandatory - prevents indefinite hangs on a stuck query), idle timeout, and max connection lifetime (rotate periodically to avoid stale/leaked state). Enable TCP keepalives so dead peers are detected rather than silently held.
- Prevent connection leaks structurally, using whatever resource-scoping idiom the language provides (context managers, `using`, try-with-resources) wrapped by the Repository/Unit-of-Work layer - don't rely on every call site remembering to close a connection manually.

## Repository pattern & Unit of Work
- A repository is a collection-like persistence abstraction scoped to an **Aggregate Root**, not a 1:1 wrapper around a database table.
- Never leak the ORM's query builder (`IQueryable`-equivalent) through the repository interface - that's a leaky abstraction that defeats the point of having one. Use the Specification pattern to express query criteria if callers need flexible filtering.
- Unit of Work is the single transactional boundary spanning possibly multiple repository operations, and is the natural place to collect and dispatch domain events after a successful commit.

## Indexing
- B-Tree is the default index type for equality/range queries.
- Composite indexes: order equality-filtered columns first, range-filtered columns last (the leftmost-prefix rule) - a common source of "why isn't my index being used" bugs.
- Covering/`INCLUDE` indexes for hot read paths to avoid a table lookup after the index scan.
- Partial indexes for filtered hot queries (e.g. `WHERE status = 'active'`) instead of indexing the whole table.
- Always validate with `EXPLAIN ANALYZE` before adding an index - every index has a write-side cost on every INSERT/UPDATE/DELETE. "Rows Removed by Filter" in a query plan is the signal that an index is missing, not a guess.

## Backup, replication, read scaling
- Choose synchronous vs asynchronous replication deliberately - it's a CAP-theorem trade-off between consistency guarantees and availability/latency, not a default to leave unexamined.
- Route analytics/reporting queries to read replicas, isolated from the primary that serves transactional traffic.
- WAL (write-ahead log) is the mechanism underlying both durability guarantees and physical replication - understanding it explains why replication lag and crash recovery behave the way they do.

## Minimum bar before calling the database layer "production grade"
1. Every schema change goes through a checksummed migration tool, never a manual `ALTER TABLE` against production.
2. A connection pool with a full timeout matrix is configured - no unbounded/default connection behavior.
3. Every write path that matters for money/inventory/uniqueness has an explicit isolation-level decision, not the framework default left unexamined.
4. Repository interfaces don't leak ORM-specific query types to calling code.
5. Every index existing in the schema is justified by an observed query plan, and every hot query has been checked against one.
