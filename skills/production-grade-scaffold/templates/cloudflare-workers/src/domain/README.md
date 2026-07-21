# Domain layer

No `hono`/Workers-runtime imports. entities/, value-objects/, events/ - same conventions as
references/domain-structure.md. Domain events here should be dispatched to a Queue (Cloudflare
Queues) rather than in-process, since there's no persistent Unit-of-Work process.
