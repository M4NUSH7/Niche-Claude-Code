# Data access layer

Repository implementations wrap D1 (`c.env.DB.prepare(...)`) or R2/KV bindings - never leak the
raw D1 `PreparedStatement` type through a repository interface. See references/database.md for
the repository/UoW pattern and references/cloud-providers.md for D1's single-writer constraints.
