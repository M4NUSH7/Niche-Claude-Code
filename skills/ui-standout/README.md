# ui-standout

**Pick standout, fit-for-purpose UI components per use-case instead of reusing the same mundane flows.**

## What it does

A three-layer method, plus a use-case -> component map that no single source supplies:

- **Layer 0 - use-case -> standout-component map** (this skill's own contribution): a hand-curated table (checkout, onboarding, dashboard, hero, settings, empty-state, auth, pricing, data-table, notification) giving the standout direction and the mundane default to avoid, with a live catalog-query fallback for the long tail.
- **Layer 1 - component catalog:** query real, agent-queryable registries (astryx, shadcn/ui, Aceternity) for candidates and scaffold the pick as owned source.
- **Layer 2 - taste gate:** 46 deterministic anti-slop rules harvested from `impeccable` - reject the AI defaults (Inter everywhere, purple->blue gradients, glassmorphism, pseudo-3D, bounce easing, gray-on-color, nested cards, tiny touch targets, bad measure).
- **Layer 3 - principles:** 17 design-principle references (harvested from designer-skills) - visual hierarchy, spacing scale, type scale, readable measure, contrast, and Von Restorff ("make one element stand out") to justify the pick.

## Why it works

Coding agents left to themselves reuse the same three-column feature grid and Inter-on-white for every app, so every product looks the same. No existing tool closes the gap alone: catalogs give options, `impeccable` rejects slop, principles justify - but the mapping from "this screen's job" to a specific standout component is the missing piece this skill authors. The taste gate is a *negative* filter (rule out slop) which is far more reliable than trying to positively define "good"; the principle layer turns "it looks nice" into a defensible reason.

Global consistency (DESIGN.md / tokens) is kept distinct from the per-screen standout choice, so apps stay coherent AND stand out.

## How to use

Fires before you build or choose any UI component/screen/layout/form, when a UI is called bland/generic, or when scaffolding a web/SSR/static Presentation layer. Not for backend/serverless/networking (no UI) and not for charts (the `dataviz` skill owns those). Folds into `production-grade-scaffold` as its Presentation-layer method.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The 3-layer workflow + scope gate |
| `references/component-map.md` | The use-case -> component map + catalog (Layers 0-1) |
| `references/taste-gate.md` | The 46 anti-slop rules + transform vocabulary (Layer 2) |
| `references/design-principles.md` | The 17 principle references incl. Von Restorff (Layer 3) |

---

**Related:** folds into [production-grade-scaffold](../production-grade-scaffold/) as its Presentation-layer method; its taste gate is part of that scaffold's minimum bar. See the [root README](../../README.md) for how the skills interlock and navigate.
