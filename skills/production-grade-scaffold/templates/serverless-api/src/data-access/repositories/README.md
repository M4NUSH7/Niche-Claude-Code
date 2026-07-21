# Repositories

Scoped to an Aggregate Root. Use a serverless/edge-compatible driver (HTTP-based, e.g. Neon's
or PlanetScale's) instead of a raw TCP pool - see references/architecture-archetypes.md #3.
Never leak the driver's raw query result type through the repository interface.
