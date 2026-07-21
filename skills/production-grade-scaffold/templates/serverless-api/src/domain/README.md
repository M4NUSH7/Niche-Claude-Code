# Domain layer

No AWS SDK / handler imports. Contains only:
- entities/       identity-bearing objects
- value-objects/  immutable, identity-free objects (default choice - see references/domain-structure.md)
- events/         past-tense DomainEvent records - dispatch via an async queue (SQS/EventBridge)
  since there's no long-lived Unit of Work process to dispatch them from after commit.
