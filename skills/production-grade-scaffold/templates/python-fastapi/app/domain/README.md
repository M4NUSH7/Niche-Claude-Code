# Domain layer

No imports from FastAPI, SQLAlchemy, or any other framework/ORM. Contains only:
- entities/       identity-bearing objects
- value_objects/  immutable, identity-free objects (default choice - see references/domain-structure.md)
- events/         past-tense DomainEvent records, dispatched by the Unit of Work after commit
