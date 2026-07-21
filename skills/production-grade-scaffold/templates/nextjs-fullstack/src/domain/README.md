# Domain layer

No `next/*`, no Prisma imports. Contains only:
- entities/       identity-bearing objects
- value-objects/  immutable, identity-free objects (default choice - see references/domain-structure.md)
- events/         past-tense DomainEvent records, dispatched by the Unit of Work after commit
