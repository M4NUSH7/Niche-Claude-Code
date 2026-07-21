# Unit of Work

The single transactional boundary (an async context manager wrapping an SQLAlchemy AsyncSession)
across one or more repository calls. Commit here, then dispatch collected domain events.
