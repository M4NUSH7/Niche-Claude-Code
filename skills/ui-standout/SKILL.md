---
name: ui-standout
description: >
  Pick STANDOUT, fit-for-purpose UI components per use-case instead of reusing
  the same mundane flows. A 3-layer method: query real component catalogs
  (astryx / shadcn / Aceternity) for candidates, reject AI-slop defaults with a
  46-rule taste gate (harvested from impeccable), and justify the pick with
  design principles (hierarchy, spacing, type, color, Von Restorff standout).
  Ships a use-case -> component map so a checkout, dashboard, hero, onboarding,
  or empty-state screen gets a standout component, not a stock grid. Use this
  BEFORE building or choosing any UI component, screen, page, layout, form, or
  design system; when the user says a UI is bland/generic/mundane/"looks like
  every other app" and wants it to stand out; when scaffolding the Presentation
  layer of a web/SSR/static app; or when reviewing a built UI for slop. Not for
  backend/serverless-API/networking services (no UI) - and not for charts
  specifically (the dataviz skill owns those).
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# UI Standout - pick fit-for-purpose components, not mundane defaults

The goal: each app's UI stands out because the agent went through real component
libraries and picked a standout component FOR THAT use-case - instead of reusing
the same three-column feature grid and Inter-on-white every time. Global design
tokens still carry across apps; the per-screen component choice is what varies.

This is a THREE-LAYER method. No single source does the whole job - each layer
answers one question, and the use-case -> component map (Layer 0) is this skill's
own contribution that none of the sources supply.

| Layer | Question | Reference (load on demand) |
|---|---|---|
| 0. Use-case -> component map | Which standout component fits THIS screen? | `references/component-map.md` |
| 1. Component catalog | What can I pick, and how do I get it as owned source? | `references/component-map.md` (Layer 1 section) |
| 2. Taste gate | Is this pick / build AI slop? | `references/taste-gate.md` (46 rules) |
| 3. Principles | Why this, for this use-case? | `references/design-principles.md` (17 principles) |

## When this skill engages (scope gate)

ONLY for UI-rendering archetypes: layered web app, SSR framework, static site.
SKIP for serverless-API and networking-service - they have no Presentation layer.
For charts/graphs/dashboed-metrics specifically, defer to the `dataviz` skill;
this skill covers the surrounding component choices, not the chart internals.

If the app has no design tokens yet, note that the GLOBAL layer (DESIGN.md /
tokens / shared elements) should be established once and carried across screens;
this skill's per-screen work sits on top of it.

## The workflow

Run these in order for each screen/component decision. Read a reference only when
its step is reached - do not open all three up front.

1. **Name the use-case.** Checkout, onboarding, dashboard, hero, settings, empty
   state, auth, pricing, data table, notification - or describe the screen's job
   in one sentence if it is not a common one.

2. **Map to a standout direction (Layer 0).** Read `references/component-map.md`.
   Find the use-case row for the standout direction (what to reach for) and the
   mundane default to AVOID. Not in the table? Use the long-tail fallback there:
   query the catalog CLIs by use-case keyword. The map is a fast default, never a
   ceiling.

3. **Get candidates from a catalog (Layer 1).** Same reference, Layer 1 section.
   Query one catalog for concrete components matching the direction:
   - `npm run astryx -- component --list` (Meta astryx - 150+ accessible, themed)
   - `shadcn search <keyword>` / `shadcn view <item>` (owned source into repo)
   - Aceternity blocks via the shadcn CLI once its registry is added.
   Pick, then `npx shadcn add <item>` or astryx `swizzle` so the component lands
   as OWNED, editable source - no black-box dependency.

4. **Run the taste gate (Layer 2).** Read `references/taste-gate.md`. Before
   accepting the built UI, check it against the 46 anti-slop rules. Reject the AI
   defaults the gate names: purple->blue gradients, Inter/Roboto everywhere,
   glassmorphism, pseudo-3D, bounce easing, gray-on-color text, nested cards,
   tiny touch targets, bad line-length. If it trips a rule, fix in that
   direction (the file lists the transform vocabulary: bolder / quieter / distill
   / typeset / colorize / polish). A UI is not production-grade if it trips the
   slop detector.

5. **Justify with principles (Layer 3).** Read `references/design-principles.md`.
   Confirm the pick against the load-bearing principles - especially Von Restorff
   (make the ONE important element stand out), visual hierarchy, spacing scale
   (4/8px), type scale, readable measure (45-75 chars), and contrast (4.5:1 body,
   3:1 large/UI). These turn "it looks nice" into a reason you can defend.

6. **Record the decision.** Note which component was picked for which use-case and
   why (one line), so the choice is auditable and the map can be refreshed as
   libraries change.

## Global vs per-app (keep them distinct)

- **Global** (carries across apps): DESIGN.md, tokens, shared elements - consistency.
- **Per-app / per-screen** (makes each app stand out): the Layer 0->3 selection above.

Do not let global consistency flatten every screen into the same component, and do
not let per-screen novelty break the shared token system. Both, not one at the
other's expense.

## How this folds into production-grade-scaffold

This skill is the UI/Presentation-layer method for `production-grade-scaffold`. When
that skill scaffolds a UI-rendering archetype, it routes here for component selection
(its Presentation "minimum bar" includes passing this taste gate). For non-UI
archetypes it skips this entirely. See `references/component-map.md` scope gate.

## Maintenance

The use-case -> component map is a hand-curated fast path; component libraries
change, so treat the table as periodically refreshed, not permanent. The taste-gate
rules and principles are harvested snapshots (impeccable Apache-2.0, designer-skills
MIT) - re-harvest if the upstreams change materially. This is noted maintenance, not
silent drift.
