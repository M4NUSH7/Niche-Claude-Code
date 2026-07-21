# Domain layer

No imports from Express, Prisma, or any other framework/ORM. This layer contains only:
- entities/       identity-bearing objects
- value-objects/  immutable, identity-free objects (default choice - see references/domain-structure.md)
- events/         past-tense DomainEvent records, dispatched by the Unit of Work after commit

Aggregates expose a single Aggregate Root as their only entry point; keep aggregates small.
