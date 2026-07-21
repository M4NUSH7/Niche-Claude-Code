# Repositories

Scoped to an Aggregate Root, not a raw table. Never leak a SQLAlchemy `Select`/`Query` object
through a repository's public interface - return domain entities/value objects only.
See references/database.md.
