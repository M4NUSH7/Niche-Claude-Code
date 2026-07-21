# Cloudflare Workers Production Scaffold

Generated from the `production-grade-scaffold` skill. Read references/cloud-providers.md's
Cloudflare section first - this is a distinct edge runtime (V8 isolates), not a Node.js server.

- src/api/       - Hono routes (the API layer; no separate presentation layer for an API-only worker)
- src/domain/    - entities, value objects, domain events - no Workers-runtime imports
- src/data-access/ - D1/R2/KV-backed repositories
- wrangler.toml  - deploy config + bindings (closest thing to IaC for this archetype)

Setup:
1. `npx wrangler d1 create app-db` and `npx wrangler kv namespace create CACHE`, then fill in the
   IDs in `wrangler.toml`.
2. `wrangler secret put OAUTH_CLIENT_SECRET` (and any other real secrets).
3. `npm install && npm run dev`
