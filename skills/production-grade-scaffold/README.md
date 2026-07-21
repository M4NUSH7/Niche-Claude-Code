# production-grade-scaffold

**Production-grade scaffolding standards (security, auth, DB, structure) for any archetype/stack/cloud.**

## What it does

Governs what the codebase itself should look like to ship. It detects and applies, on demand:

1. **Archetype** - full-stack SSR / serverless API / edge (Cloudflare Workers) / static site / networking service / layered web app (default). Signals in the repo pick the row.
2. **Stack** - node/python/rust/generic (for the layered web app archetype).
3. **Cloud** - AWS / Azure / Cloudflare / self-host.
4. **Checklists** - security, auth, DB, api-layer, domain-structure, infrastructure - each ending in a "minimum bar" an empty-but-organized repo has not yet met.
5. **UI / Presentation layer** - for UI-rendering archetypes, routes to the `ui-standout` skill for component selection (and treats its 46-rule anti-slop taste gate as part of the Presentation minimum bar).

Ships layered templates per stack (`nextjs-fullstack`, `nodejs-typescript`, `python-fastapi`, `rust-axum`, `serverless-api`, `cloudflare-workers`, `static-site`, `networking-service`, `generic-layered`).

## Why it works

It governs a **different axis** than a build harness: init-harness answers "who builds and how are they coordinated"; this answers "what should the codebase look like to ship". Six layers with dependencies pointing inward, bent per archetype, so the boundaries that matter (security, auth, data access) are explicit rather than emergent. Progressive disclosure keeps it cheap - you read only the archetype/stack/checklist rows relevant to what you are building, never the whole reference set.

It embeds cleanly into init-harness's context-bootstrap (scaffold the app skeleton first, then wrap the control plane around it) with no file-ownership collision - this skill writes `src/`/CI/templates; the harness owns `.claude/`/hooks.

## How to use

Fires when scaffolding a new app/service, or auditing one before it ships. It reads the archetype/stack/cloud signals, then applies only the relevant checklists and templates.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | Detect archetype -> stack -> cloud -> checklists -> UI |
| `references/architecture-archetypes.md` | The archetype rows and where each bites |
| `references/{security,auth,database,api-layer,domain-structure,infrastructure-delivery}.md` | Per-concern minimum-bar checklists |
| `references/cloud-providers.md` | AWS / Azure / Cloudflare specifics |
| `references/ui-components.md` | Routes to the `ui-standout` skill for the Presentation layer |
| `templates/<archetype-or-stack>/` | Layered app skeletons per stack/archetype |

---

**Related:** embeds into [init-harness](../init-harness/)'s context-bootstrap for greenfield apps; routes to [ui-standout](../ui-standout/) for the UI/Presentation layer. See the [root README](../../README.md) for how the skills interlock and navigate.
