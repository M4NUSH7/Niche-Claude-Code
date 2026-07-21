# Route Handlers (the "API layer" in a Next.js app)

In this archetype, Presentation and API physically merge (see
references/architecture-archetypes.md). Route Handlers / Server Actions live under app/,
colocated with the routes that use them, but must still call into src/domain and
src/data-access rather than embedding business logic or raw queries inline.
