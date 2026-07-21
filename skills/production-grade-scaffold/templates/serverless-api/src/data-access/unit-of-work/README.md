# Unit of Work

Still the single transactional boundary per-invocation, but there's no persistent process to
hold a long-lived transaction across - scope it to the lifetime of one handler invocation.
