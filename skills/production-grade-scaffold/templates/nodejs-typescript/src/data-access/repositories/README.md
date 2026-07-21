# Repositories

Scoped to an Aggregate Root, not to a raw table. Never leak Prisma's query-builder types through
a repository's public interface - return domain entities/value objects only. Use a Specification
object if callers need flexible filtering. See references/database.md.
