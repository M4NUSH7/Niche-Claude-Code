# UI component selection (Presentation layer)

Load this ONLY for UI-rendering archetypes: layered web app, SSR framework
(`nextjs-fullstack`), static site. SKIP for `serverless-api` and
`networking-service` - they have no Presentation layer.

The Presentation layer is where apps most often ship mundane, interchangeable UI.
Scaffolding a working Presentation layer is necessary but not sufficient - the
component choices are what make an app stand out or look like every other app.

## Method: defer to the `ui-standout` skill

Component selection is a full 3-layer method (catalog query -> anti-slop taste
gate -> design-principle justification, plus a use-case -> standout-component
map). That method lives in the `ui-standout` skill - do not restate it here.

When this scaffold builds or audits a Presentation layer:

1. Invoke the `ui-standout` skill (or read its `SKILL.md` and follow it as if
   invoked). Run its workflow per screen/use-case.
2. Treat its **taste gate as part of this scaffold's Presentation "minimum bar"**:
   a UI is not production-grade if it trips the 46-rule slop detector. Add
   "passes the ui-standout taste gate" to the Presentation checklist alongside
   the accessibility and responsive bars.
3. Keep the **global vs per-app split**: DESIGN.md / tokens / shared elements are
   the global consistency layer (established once, carried across screens); the
   per-screen component pick is the standout layer. Both, not one at the other's
   expense.

If `ui-standout` is not installed, fall back to its principle summary: pick per
use-case (not a stock grid), reject AI-slop defaults (Inter-everywhere,
purple->blue gradients, glassmorphism, bounce easing, gray-on-color, tiny touch
targets), and justify with hierarchy / spacing / type / color / Von Restorff. But
the full skill is the intended path.

## Templates hook

The stack-native templates (`nextjs-fullstack/`, `nodejs-typescript/`, etc.) gain
a documented wiring point for the catalogs `ui-standout` uses - a `components.json`
plus a registry entry for astryx / shadcn / Aceternity - rather than new template
trees. Add that wiring when the archetype renders UI.
