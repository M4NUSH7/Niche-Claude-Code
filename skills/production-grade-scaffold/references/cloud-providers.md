# Cloud Provider Reference - personalize deployment, storage, and IaC per target

Read only the section matching the detected/chosen provider. Detect from repo signals:
`wrangler.toml` -> Cloudflare  `serverless.yml`/`template.yaml`/`.aws/` -> AWS  `host.json`/`azure-pipelines.yml`/`*.bicep` -> Azure  none of these + a static-only build -> plain site/CDN.

## AWS (largest market share; default for `templates/serverless-api/`)
- Compute: Lambda (serverless-api archetype) or ECS/Fargate/EC2 (layered web app archetype, containerized).
- Object storage: S3 - versioning + bucket policy least-privilege + block-public-access on by default; never rely on ACLs alone.
- Managed DB: RDS (Postgres/MySQL) for relational, DynamoDB for key-value/high-scale - DynamoDB needs access-pattern-first schema design (single-table design), not a relational mental model.
- IaC: Terraform (provider-agnostic) or CDK/SAM (AWS-native, faster iteration for Lambda-heavy stacks).
- Secrets: Secrets Manager or Parameter Store, never plaintext env vars in the Lambda console.
- Networking: API Gateway (REST/HTTP API) in front of Lambda; ALB in front of ECS/Fargate.
- Start from `templates/serverless-api/` (Lambda) or `templates/nodejs-typescript/` / `templates/python-fastapi/` / `templates/rust-axum/` (ECS/Fargate) and apply this section's IaC/storage specifics.

## Azure
- Compute: Azure Functions (serverless archetype) or App Service/Container Apps (layered web app archetype).
- Object storage: Blob Storage - private containers by default, SAS tokens scoped to minimum time/permission instead of account keys for client-facing access.
- Managed DB: Azure SQL or Cosmos DB (multi-model, partition-key design is the Cosmos equivalent of DynamoDB's access-pattern-first design).
- IaC: Bicep (Azure-native, terser than its ARM JSON predecessor) or Terraform.
- Secrets: Key Vault, referenced via managed identity - avoid connection strings in app settings where a managed identity binding exists instead.
- Start from `templates/serverless-api/` (adapt `serverless.yml` -> `host.json` + Azure Functions bindings) or the layered templates for App Service/Container Apps, applying this section's storage/secrets specifics.

## Cloudflare (edge-first; distinct runtime, not just a deployment target)
- Compute: Workers - V8 isolates, not Node.js; no persistent process, no native Node APIs unless using `nodejs_compat`. Cold start is near-zero (isolates, not containers) but the runtime API surface is smaller.
- Storage: R2 (S3-compatible object storage, no egress fees), D1 (SQLite at the edge - single-writer semantics, design for it), KV (eventually-consistent global key-value, good for config/cache not transactional data), Durable Objects (strongly-consistent single-instance state - the right tool when D1/KV's consistency model doesn't fit).
- IaC: `wrangler.toml` is both the deploy config and the closest thing to IaC here; Terraform's Cloudflare provider exists for account-level resources (DNS, zones) alongside it.
- Secrets: `wrangler secret put`, bound as runtime bindings - never inline in `wrangler.toml`.
- This is its own archetype, not a variant of `serverless-api/` - use `templates/cloudflare-workers/` directly; see references/architecture-archetypes.md if the project also has a Cloudflare Pages frontend (that pairs with the SSR-framework archetype, not this one).

## Plain website / static site (no backend, or backend fully decoupled)
- No API/Domain/Data-Access layers apply - see `templates/static-site/`.
- Security checklist shrinks to: CSP/security headers at the CDN/host config layer (not app code, since there's no app process), SRI on any third-party script, HTTPS-only with HSTS.
- Hosting: any CDN/static host - S3+CloudFront, Azure Static Web Apps, Cloudflare Pages, Netlify, Vercel. Pick based on where the rest of the org's infra already lives rather than on any technical difference between them for a pure static site.
- If the site later needs a backend (forms, auth, dynamic data), that's a *new* archetype decision (see references/architecture-archetypes.md) - usually serverless functions bolted onto the same CDN (Cloudflare Pages Functions, Netlify Functions, Vercel Functions), not a full server.
