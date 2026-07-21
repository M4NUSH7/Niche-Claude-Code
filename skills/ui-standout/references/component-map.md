# Layer 1 (catalog) + the use-case -> component MAP  [DRAFT - main-authored core]

This is the skill's ORIGINAL contribution: the component-catalog query layer plus the
use-case -> standout-component map that no source supplies (confirmed in ui-research-notes.md
and design-skills-notes.md). Assembled into the final skill once the impeccable taste-gate and
designer-skills principle harvests land.

## Layer 1 - component catalog (what can I pick?)

Three agent-queryable catalogs, chosen so the agent scaffolds OWNED source (no lock-in):

| Catalog | Query / invoke | Distribution | Role |
|---|---|---|---|
| astryx (Meta) | `npm run astryx -- component --list`; `swizzle` to eject source | npm `@astryxdesign/core`+`cli`+`theme-*` (7 themes) | ANCHOR - 150+ accessible components, agent-ready, built on StyleX |
| shadcn/ui | `shadcn search` / `list` / `view`; `npx shadcn add <item>` | registry.json + CLI, source into repo | The distribution MODEL; components as owned source |
| Aceternity UI | register registry URL in components.json -> `npx shadcn add <block>` | shadcn-CLI-compatible registry | High-visual-impact "standout" blocks (free core) |

StyleX is the styling ENGINE beneath astryx, not a component source - do not query it for components.

**How the agent uses Layer 1:** read the use-case -> map (below) for candidate component types,
query the catalog CLI for concrete matches, `add`/`swizzle` the chosen source into the repo (owned,
editable), then run the Layer-2 taste gate and justify via Layer-3 principles.

## Layer 0 - use-case -> standout-component MAP (the skill's own logic)

HYBRID (owner-decided): a hand-curated static table for common use-cases (fast default) +
a live registry query fallback for anything not in the table (always-current on the long tail).
The table needs periodic refresh as libraries change - flagged as maintenance, not silent drift.

| Use-case / screen | Standout component direction (not the mundane default) | Catalog candidates | Why (principle hook) |
|---|---|---|---|
| Hero / landing | One bold focal element (oversized type or a single motion accent), NOT a stock 3-column feature grid | Aceternity hero blocks; astryx display type | von-Restorff: one element stands out; hierarchy top-loaded |
| Checkout / payment | Trust-forward single-column flow with an explicit review step, NOT a multi-step wizard that hides cost | shadcn form + card; astryx form | Reduce anxiety at money-movement; one clear primary action |
| Onboarding | Progressive one-thing-per-screen with a visible finish line, NOT a dense settings dump | astryx stepper; shadcn progress | Cognitive load; completion signal |
| Dashboard | A single primary metric that dominates, supporting metrics recede, NOT a uniform grid of equal tiles | shadcn card + chart; dataviz skill for the charts | Hierarchy; von-Restorff for the headline metric |
| Data table / list | Density-appropriate table with one scannable key column, NOT a card-per-row wall | shadcn data-table; astryx table | Measure/scan-ability; density fits the task |
| Empty state | A purposeful next-action + one illustration, NOT a bare "no data" line | Aceternity empty/CTA; astryx | Guide the user; standout the action |
| Settings | Grouped sections with sane defaults visible, NOT every toggle at once | shadcn tabs + form | Progressive disclosure; reduce choice overload |
| Auth (login/signup) | Minimal single-purpose form, social-first if it fits, NOT a marketing page bolted to a form | shadcn form; astryx | One job per screen; friction-minimal |
| Pricing | One recommended tier visually elevated, NOT three identical columns | Aceternity pricing; shadcn card | von-Restorff: elevate the intended pick |
| Notification / feedback | Inline, contextual, dismissible - NOT a modal for non-blocking info | shadcn toast/alert | Match interruption level to importance |

**Long-tail fallback (not in table):** query the catalog CLIs (`astryx component --list`,
`shadcn search <use-case-keyword>`) for candidates, then apply the SAME gate: Layer-2 rejects slop,
Layer-3 justifies the pick. The map is a fast default, never a ceiling.

## Global vs per-app split (owner's point)

- GLOBAL layer (carries across apps): DESIGN.md / tokens / shared elements - consistency.
- PER-APP layer (makes each app stand out): the use-case -> component selection above - run per screen.
The skill keeps both distinct: global consistency + per-use-case standout, not one at the other's expense.

## Scope gate (when this skill engages)

Only for UI-rendering archetypes (layered web app, SSR, static-site). SKIPPED for serverless-API
and networking-service (no Presentation layer). This mirrors production-grade-scaffold's
progressive-disclosure rule - load the UI reference on demand, only when the archetype renders UI.
