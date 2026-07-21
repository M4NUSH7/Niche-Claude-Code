# Unit of Work

The single transactional boundary - an `sqlx::Transaction` wrapped by a UoW type - spanning one
or more repository calls. Commit here, then dispatch collected domain events.
