---
name: production-grade-scaffold
description: Production-grade scaffolding standards (security, auth, DB, structure) for any archetype/stack/cloud. Use when scaffolding a new app/service, or auditing one, before it ships.
---

# Production-Grade Application Scaffold

Six layers by default - Presentation -> API -> Domain Logic -> Data Access -> Database ->
Infrastructure, dependencies pointing inward only - bent per archetype (see step 1).

**Read only what step 1-3 point to. Never open all of `references/` or `templates/` up front -
each file below is self-contained and loaded on demand, not as background reading.**

## 1. Detect archetype (read `references/architecture-archetypes.md` section matching row only)

| Signal in repo | Archetype | Template |
|---|---|---|
| `next.config.*`, `nuxt.config.*` | Full-stack SSR framework | `templates/nextjs-fullstack/` |
| `wrangler.toml` | Cloudflare Workers (edge) | `templates/cloudflare-workers/` |
| `serverless.yml`, `template.yaml`, `host.json` | Serverless API | `templates/serverless-api/` |
| Static build only, no server code | Plain website | `templates/static-site/` |
| Raw sockets/custom protocol, no HTTP framework | Networking/systems service | `templates/networking-service/` |
| None of the above / persistent server + DB | Layered web app (default) | stack table below |
| Nothing exists yet | - | ask the user |

## 2. Detect stack (layered web app only - other archetypes are language-fixed above)

`package.json`->`templates/nodejs-typescript/`  `pyproject.toml`/`requirements.txt`->`templates/python-fastapi/`  `Cargo.toml`->`templates/rust-axum/`  anything else->`templates/generic-layered/` (hand-adapt; boundaries matter more than folder names).

## 3. Detect cloud target, if any (read only the matching subsection of `references/cloud-providers.md`)

`.aws/`, SAM/CDK files -> AWS  `*.bicep`, `azure-pipelines.yml` -> Azure  `wrangler.toml` -> Cloudflare (already implies the archetype in step 1)  none -> self-hosted/no specific provider, skip this file.

## 4. Apply checklists - read only the ones relevant to what you're building/auditing

`references/security.md`  `references/auth.md` (skip for `static-site`)  `references/database.md` (skip for `static-site`, `cloudflare-workers` uses D1 notes in cloud-providers.md instead)  `references/api-layer.md` (skip for `static-site`, `networking-service`)  `references/domain-structure.md`  `references/infrastructure-delivery.md`. Each ends in a "minimum bar" checklist - treat an empty-but-organized repo as incomplete until that bar is met.

## 4a. UI / Presentation layer - only if the archetype renders UI

For UI-rendering archetypes (layered web app, SSR `nextjs-fullstack`, `static-site`), read
`references/ui-components.md` and run the `ui-standout` skill for component selection: pick a
standout component per use-case (not a stock grid), pass the 46-rule anti-slop taste gate, and
justify with design principles. The taste gate is part of the Presentation minimum bar - a UI that
trips the slop detector is not production-grade. SKIP entirely for `serverless-api` and
`networking-service` (no Presentation layer). Charts/dashboards defer to the `dataviz` skill.

> **Harness / init-harness integration.** When init-harness runs its section 0.5 context-bootstrap on a
> greenfield UI app, it hands off to this scaffold to lay the app skeleton first, then wraps the
> control plane around it. The harness "Production-grade bar" MCQ (Solid small tool / Multi-user
> product / High-scale) selects which of these checklists apply and how strict the bars are - and,
> for UI archetypes, whether the ui-standout taste gate is advisory or enforced. Ownership stays
> clean: this scaffold writes `src/`/CI/templates; init-harness owns `.claude/`/`harness/`/hooks.

## 5. Re-classify on change, don't patch

Archetype/stack/cloud change (e.g. Next.js -> Rust, monolith -> serverless) -> redo steps 1-3 for
the new shape; don't carry old assumptions (connection pools, Dockerfiles, OAuth2 bearer tokens)
into an archetype where they don't apply - `architecture-archetypes.md` and `cloud-providers.md`
both flag where this bites.

## Files in this skill

`references/`: architecture-archetypes.md, cloud-providers.md, security.md, auth.md, database.md, api-layer.md, domain-structure.md, infrastructure-delivery.md.

`templates/`: nodejs-typescript, python-fastapi, rust-axum, generic-layered (layered web app)  nextjs-fullstack (SSR)  serverless-api (AWS/Azure serverless)  cloudflare-workers (edge)  static-site (no backend)  networking-service (protocol/systems).
