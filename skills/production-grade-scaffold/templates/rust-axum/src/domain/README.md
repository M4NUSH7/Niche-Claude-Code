# Domain layer

No `use axum::...` or `use sqlx::...` here. Contains only:
- entities/       identity-bearing structs
- value_objects/  immutable, identity-free structs (default choice - see references/domain-structure.md)
- events/         past-tense DomainEvent structs, dispatched by the Unit of Work after commit
