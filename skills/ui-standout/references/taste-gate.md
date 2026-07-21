# Impeccable Taste Gate

## What this is

This is a NEGATIVE taste gate: a set of deterministic checks for rejecting "AI
slop" in UI/UX output, plus a vocabulary of transform commands for fixing what
the gate catches. It is a harvest of content from the `impeccable` project
(https://github.com/pbakaus/impeccable), an AI-agent skill and CLI that
detects and fixes AI-generated-interface anti-patterns.

- License: Apache-2.0 (see upstream `LICENSE` file; confirmed at commit below)
- Source repo: https://github.com/pbakaus/impeccable
- Commit cloned: `4d849eb75f216109ea7053ed21530a11fafcc786` (branch `main`, dated
  2026-07-21)
- This file is CONTENT ACQUISITION only. It does not run, install, or vendor
  the impeccable installer, CLI, or skill files  -  it only extracts the rule
  data and command vocabulary as reference material.

## The 46 rules

All 46 rules below were extracted verbatim (id, name, description condensed)
from the canonical rule registry:

`cli/engine/registry/antipatterns.mjs` (515 lines, `ANTIPATTERNS` array,
lines 1-447), commit `4d849eb75f216109ea7053ed21530a11fafcc786`.

This is the single source of truth in the repo  -  the same array is re-exported
into every provider-specific copy under `.claude/skills/`, `.cursor/skills/`,
`plugin/skills/`, etc. (all identical content, generated via `bun run build`).
The pure detection logic that implements many of these checks lives alongside
in `cli/engine/rules/checks.mjs` (2704 lines)  -  representative line numbers
for a few rules are cited in the table below where useful for verification.

Count found: exactly 46 (`grep -c "id: '" cli/engine/registry/antipatterns.mjs`
= 46). Not padded or invented  -  every row below traces to a specific `id:`
entry in that file.

Categories used by the registry: `slop` (AI-generation tells) and `quality`
(general design/a11y issues, not necessarily AI-specific). Rules tagged
`gated: 'gpt'` or `gated: 'gemini'` are provider-specific tells, off by
default, opt-in via `--gpt` / `--gemini` CLI flags. Rules tagged
`severity: 'advisory'` are softer signals, not hard fails.

| # | Rule ID | Category | What it detects (the slop pattern) | Fix / direction |
|---|---|---|---|---|
| 1 | `side-tab` | slop | Thick colored border on one side of a card  -  the single most recognizable AI-UI tell. | Use a subtler accent or remove the border entirely. |
| 2 | `border-accent-on-rounded` | slop | Thick accent border on a rounded card; the hard border clashes with rounded corners. | Remove the border or the border-radius. |
| 3 | `overused-font` | slop (type) | Inter, Roboto, Fraunces, Geist, Plus Jakarta Sans, Space Grotesk  -  used so widely they read as generic/AI-default. | Choose a face that gives the interface personality. |
| 4 | `single-font` | slop (type) | Only one font family used for the entire page. | Pair a distinctive display font with a refined body font for hierarchy. |
| 5 | `flat-type-hierarchy` | slop (type) | Font sizes too close together; no clear visual hierarchy. | Use fewer sizes with more contrast (>=1.25 ratio between steps). |
| 6 | `gradient-text` | slop | Gradient-filled text (background-clip: text + gradient), decorative not meaningful. | Use solid colors for text. |
| 7 | `ai-color-palette` | slop | Purple/violet gradients and cyan-on-dark  -  the most recognizable AI palette tell. | Choose a distinctive, intentional palette. |
| 8 | `cream-palette` | slop | Warm cream/beige page background reached for as the default "tasteful" AI surface. | Choose a background from a deliberate palette, not the safe warm off-white. |
| 9 | `nested-cards` | slop (layout) | Cards inside cards; excessive visual depth and noise. | Flatten the hierarchy using spacing, typography, and dividers instead of nesting containers. |
| 10 | `monotonous-spacing` | slop (layout) | The same spacing value used everywhere; no rhythm or variation. | Use tight groupings for related items, generous separation between sections. |
| 11 | `bounce-easing` | slop | Bounce/elastic/wobble/spring easing on animations or overshoot cubic-bezier curves. | Use exponential easing (ease-out-quart/quint/expo) instead. |
| 12 | `dark-glow` | slop | Dark backgrounds with colored box-shadow glows  -  the default "cool" AI look. | Use subtle, purposeful lighting, or skip dark theme entirely. |
| 13 | `icon-tile-stack` | slop (layout) | Small rounded-square icon container stacked above a heading  -  the universal AI feature-card template. | Try a side-by-side icon and heading, or let the icon sit in flow unboxed. |
| 14 | `italic-serif-display` | slop (type) | Oversized italic serif (Fraunces, Recoleta, Playfair, Newsreader-italic) as the primary hero headline  -  now the universal AI-startup landing hero. | Set roman, or move to a non-serif display face. (Editorial/magazine register may legitimately keep it  -  judge by context.) |
| 15 | `hero-eyebrow-chip` | slop (type) | Tiny uppercase tracked label immediately above an oversized hero headline, or the same shape as a pill chip  -  the default AI SaaS hero. | Drop the eyebrow, fold the kicker into the headline, or use it as a nav breadcrumb instead. |
| 16 | `repeated-section-kickers` | slop (type, advisory) | Repeating tiny uppercase tracked labels above section headings  -  turns a brand page into AI editorial scaffolding. | Replace with stronger structure, artifacts, imagery, or a deliberate brand system. |
| 17 | `numbered-section-markers` | slop (layout, advisory) | Numbered display markers as section labels (01, 02, 03)  -  one tier deeper than the eyebrow-chip scaffold. | Choose a different section cadence. |
| 18 | `em-dash-overuse` | slop | More than two em-dashes (` - ` or `--`) in body copy  -  an AI cadence tell. | Use commas, colons, periods, or parentheses instead. |
| 19 | `marketing-buzzword` | slop | Generic SaaS phrases: streamline / empower / supercharge / world-class / enterprise-grade / next-generation / cutting-edge, etc. | Pick a specific verb and noun describing what the product literally does. |
| 20 | `aphoristic-cadence` | slop | 3+ sections landing on a short rebuttal sentence ("X. No Y." / "X. Just Y.") or manufactured-contrast aphorism ("Not a feature. A platform."). | Once is fine; the repeated pattern is the tell  -  vary the cadence. |
| 21 | `oversized-h1` | slop (type) | A full-sentence headline set at display size, dominating the viewport. | Set long headlines smaller, or tighten the copy (short 1-2 word headlines at display size are fine). |
| 22 | `extreme-negative-tracking` | slop (type) | Letter-spacing pulled tighter than the point characters keep their own shapes; costs legibility. | Tighten display type optically, not destructively. |
| 23 | `broken-image` | quality | `<img>` tags with empty/missing src or placeholder values, rendering as broken-image boxes. | Use real images, generated assets, or remove the tag. |
| 24 | `gray-on-color` | quality | Gray text on colored backgrounds  -  reads as washed out. | Use a darker shade of the background color, or white/near-white for contrast. |
| 25 | `low-contrast` | quality | Text/background pair fails WCAG AA (4.5:1 body, 3:1 large text). | Increase contrast between text and background. |
| 26 | `layout-transition` | quality | Animating width, height, padding, or margin  -  causes layout thrash and jank. | Use `transform` and `opacity`, or `grid-template-rows` for height animation. |
| 27 | `line-length` | quality (type, layout) | Text lines wider than ~80 characters  -  the eye loses its place. | Add a max-width (65ch-75ch) to text containers. |
| 28 | `cramped-padding` | quality (layout) | Text too close to its container's edge, or a bordered/colored wrapper with near-zero padding around text children. | Add at least 8px (ideally 12-16px) of padding inside bordered/outlined/colored containers. |
| 29 | `body-text-viewport-edge` | quality (layout) | Body paragraphs render flush against the left/right viewport edge with no padding container. | Wrap content with >=16px (ideally 24-32px) horizontal padding, or apply max-width + auto margins. |
| 30 | `tight-leading` | quality (type) | Line-height below 1.3x font size  -  hard to read across multiple lines. | Use 1.5-1.7 for body text. |
| 31 | `skipped-heading` | quality (type) | Heading levels skip (e.g. h1 then h3, no h2)  -  breaks the document outline for screen readers. | Do not skip heading levels. |
| 32 | `justified-text` | quality (type) | Justified text without hyphenation  -  creates uneven word spacing ("rivers of white"). | Use `text-align: left`, or enable `hyphens: auto` if justifying. |
| 33 | `tiny-text` | quality (type) | Body text below 12px  -  hard to read, especially on high-DPI screens. | Use at least 14px for body content; 16px is ideal. |
| 34 | `all-caps-body` | quality (type) | Long passages in uppercase  -  removes word-shape cues (ascenders/descenders) that aid reading. | Reserve uppercase for short labels and headings only. |
| 35 | `wide-tracking` | quality (type) | Letter-spacing above 0.05em on body text  -  disrupts character grouping, slows reading. | Reserve wide tracking for short uppercase labels only. |
| 36 | `text-overflow` | quality (layout) | Content renders wider than its container, spilling out or forcing horizontal scroll. | Let text wrap, constrain widths, or give the region a deliberate scroll affordance. |
| 37 | `clipped-overflow-container` | quality (layout) | An `overflow: hidden`/`clip` container wraps an absolutely-positioned child, cutting off tooltips/menus/popovers. | Let overflow be visible, or move the positioned layer out of the clipping container. |
| 38 | `design-system-font` | quality (type) | A font used that isn't declared in the project's DESIGN.md typography tokens. | Use the documented type system, or update DESIGN.md if intentional. |
| 39 | `design-system-color` | quality (advisory) | A literal color used outside the DESIGN.md palette and its tonal ramps. | May be legitimate, but should be a deliberate design-system addition, not drift. |
| 40 | `design-system-radius` | quality (advisory) | A border-radius value outside the DESIGN.md rounded scale. | Use a documented radius token, or update the design system if intentional. |
| 41 | `design-system-font-size` | quality (advisory, type) | A literal font-size off the type ramp documented in DESIGN.md. | Use a documented size step, or update the design system if intentional. |
| 42 | `gpt-thin-border-wide-shadow` | slop (advisory, gated: gpt) | Hairline border paired with a wide, diffuse shadow  -  a recurring GPT-generated-UI signature. | Commit to one: a defined edge OR a soft elevation, not both. |
| 43 | `repeating-stripes-gradient` | slop (advisory, gated: gpt) | Repeating-gradient stripes used as surface decoration  -  a recurring GPT-generated-UI signature. | Reach for a deliberate texture, or leave the surface plain. |
| 44 | `codex-grid-background` | slop (advisory, gated: gpt) | Two-axis hairline grid-line gradient background (Codex/GPT signature: two "1px, transparent 1px" gradient layers, one per axis, tiled via `background-size`). | Reserve grid overlays for actual canvas/map/blueprint/measurement surfaces; use product structure or a plain surface elsewhere. |
| 45 | `theater-slop-phrase` | slop (advisory, gated: gpt) | Dismissing something as "X theater"  -  a recurring GPT-generated-copy tic. | Say plainly what the thing does or does not do. |
| 46 | `image-hover-transform` | slop (advisory, gated: gemini) | Scaling or rotating an image on hover  -  a recurring Gemini-generated-UI signature. | Let imagery sit still, or use a subtler, purposeful interaction. |

### Representative source citations (for verification)

- `side-tab`: `cli/engine/registry/antipatterns.mjs:4-11`; detection logic
  `cli/engine/rules/checks.mjs:27-52` (`checkBorders`).
- `ai-color-palette`: `cli/engine/registry/antipatterns.mjs:61-68`; detection
  logic (purple/violet hue + Tailwind class matching)
  `cli/engine/rules/checks.mjs:120-126` and `:148-155`; raw-HTML hex-code
  regex match `cli/engine/rules/checks.mjs:452-459`.
- `low-contrast`: `cli/engine/registry/antipatterns.mjs:236-241`; WCAG
  contrast-ratio check `cli/engine/rules/checks.mjs:95-118`.
- `icon-tile-stack`: `cli/engine/registry/antipatterns.mjs:117-125`; sibling
  shape-matching logic `cli/engine/rules/checks.mjs:180-220` (`checkIconTile`).
- `bounce-easing`: `cli/engine/registry/antipatterns.mjs:99-106`; cubic-bezier
  overshoot detection `cli/engine/rules/checks.mjs:373-409` (`checkMotion`).
- `codex-grid-background`: `cli/engine/registry/antipatterns.mjs:415-424`;
  two-axis hairline-gradient detection
  `cli/engine/rules/checks.mjs:590-611`.

## Transform-command vocabulary

The task named 8 commands (bolder, quieter, distill, colorize, typeset,
animate, polish, critique, audit). All 8 exist. The live repo actually ships
22 user-invocable commands under one skill (`/impeccable <command>`), listed
in the router table at `skill/SKILL.src.md:124-148` (commit
`4d849eb75f216109ea7053ed21530a11fafcc786`). Full list below, grouped by the
table's own categories; the 8 named in the task are marked `*`.

**Build**
- `craft [feature]`  -  shape, then build a feature end-to-end.
- `shape [feature]`  -  plan UX/UI before writing code.
- `init`  -  set up project context: PRODUCT.md, DESIGN.md, live config, next steps.
- `document`  -  generate DESIGN.md from existing project code.
- `extract [target]`  -  pull reusable tokens and components into a design system.

**Evaluate**
- `critique [target]` *  -  UX design review with heuristic scoring.
- `audit [target]` *  -  technical quality checks (a11y, perf, responsive).

**Refine**
- `polish [target]` *  -  final quality pass before shipping.
- `bolder [target]` *  -  amplify safe or bland designs.
- `quieter [target]` *  -  tone down aggressive or overstimulating designs.
- `distill [target]` *  -  strip to essence, remove complexity.
- `harden [target]`  -  production-ready: errors, i18n, edge cases.
- `onboard [target]`  -  design first-run flows, empty states, activation.

**Enhance**
- `animate [target]` *  -  add purposeful animations and motion.
- `colorize [target]` *  -  add strategic color to monochromatic UIs.
- `typeset [target]` *  -  improve typography hierarchy and fonts.
- `layout [target]`  -  fix spacing, rhythm, and visual hierarchy.
- `delight [target]`  -  add personality and memorable touches.
- `overdrive [target]`  -  push past conventional limits.

**Fix**
- `clarify [target]`  -  improve UX copy, labels, and error messages.
- `adapt [target]`  -  adapt for different devices and screen sizes.
- `optimize [target]`  -  diagnose and fix UI performance.

**Iterate**
- `live`  -  visual variant mode: pick elements in the browser, generate alternatives.

Plus three management commands (not design transforms): `pin <command>`,
`unpin <command>`, `hooks <on|off|status|...>`.

## DESIGN.md capture format skeleton

Source: `skill/reference/document.md:129-238` (Step 4: Write DESIGN.md),
commit `4d849eb75f216109ea7053ed21530a11fafcc786`. DESIGN.md follows the
external "DESIGN.md format spec"
(https://raw.githubusercontent.com/google-labs-code/design.md/main/docs/spec.md):
YAML frontmatter (machine-readable tokens) + a markdown body with exactly six
sections in a fixed order (`document.md:51-60`): Overview, Colors, Typography,
Elevation, Components, Do's and Don'ts. Headers must match the spec
character-for-character; sections may be omitted but never reordered or
renamed.

```markdown
---
name: [Project Title]
description: [one-line tagline]
colors:
  # key = descriptive slug, value = hex or OKLCH (pick one canonical format)
  primary: "#b8422e"
  neutral-bg: "#faf7f2"
typography:
  display:
    fontFamily: "Cormorant Garamond, Georgia, serif"
    fontSize: "clamp(2.5rem, 7vw, 4.5rem)"
    fontWeight: 300
    lineHeight: 1
    letterSpacing: "normal"
  body:
    # ...
rounded:
  sm: "4px"
  md: "8px"
spacing:
  sm: "8px"
  md: "16px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral-bg}"
    rounded: "{rounded.sm}"
    padding: "16px 48px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
---

# Design System: [Project Title]

## 1. Overview

**Creative North Star: "[Named metaphor in quotes]"**

[2-3 paragraph holistic description: personality, density, aesthetic
philosophy. Start from the North Star and work outward. State what this
system explicitly rejects (pulled from PRODUCT.md's anti-references). End
with a short **Key Characteristics:** bullet list.]

## 2. Colors

[Describe the palette character in one sentence.]

### Primary
- **[Descriptive Name]** (#HEX / oklch(...)): [Where and why this color is
  used. Be specific about context, not just role.]

### Secondary (optional; omit if the project has only one accent)
- **[Descriptive Name]** (#HEX): [Role.]

### Tertiary (optional)
- **[Descriptive Name]** (#HEX): [Role.]

### Neutral
- **[Descriptive Name]** (#HEX): [Text / background / border / divider role.]
- [...]

### Named Rules (optional, powerful)
**The [Rule Name] Rule.** [Short, forceful prohibition or doctrine, e.g. "The
One Voice Rule. The primary accent is used on <=10% of any given screen. Its
rarity is the point."]

## 3. Typography

**Display Font:** [Family] (with [fallback])
**Body Font:** [Family] (with [fallback])
**Label/Mono Font:** [Family, if distinct]

**Character:** [1-2 sentence personality description of the pairing.]

### Hierarchy
- **Display** ([weight], [size/clamp], [line-height]): [Purpose; where it appears.]
- **Headline** ([weight], [size], [line-height]): [Purpose.]
- **Title** ([weight], [size], [line-height]): [Purpose.]
- **Body** ([weight], [size], [line-height]): [Purpose. Include max line
  length like 65-75ch if relevant.]
- **Label** ([weight], [size], [letter-spacing], [case if uppercase]): [Purpose.]

### Named Rules (optional)
**The [Rule Name] Rule.** [Short doctrine about type use.]

## 4. Elevation

[One paragraph: does this system use shadows, tonal layering, or a hybrid?
If "no shadows", say so explicitly and describe how depth is conveyed instead.]

### Shadow Vocabulary (if applicable)
- **[Role name]** (`box-shadow: [exact value]`): [When to use it.]
- [...]

### Named Rules (optional)
**The [Rule Name] Rule.** [e.g. "The Flat-By-Default Rule. Surfaces are flat
at rest. Shadows appear only as a response to state (hover, elevation, focus)."]

## 5. Components

For each component, lead with a short character line, then specify shape,
color assignment, states, and any distinctive behavior.

### Buttons
- **Shape:** [radius described, exact value in parens]
- **Primary:** [color assignment + padding, in semantic + exact terms]
- **Hover / Focus:** [transitions, treatments]
- **Secondary / Ghost / Tertiary (if applicable):** [brief description]

### Chips (if used)
- **Style:** [background, text color, border treatment]
- **State:** [selected / unselected, filter / action variants]

### Cards / Containers
- **Corner Style:** [radius]
- **Background:** [colors used]
- **Shadow Strategy:** [reference Elevation section]
- **Border:** [if any]
- **Internal Padding:** [scale]

### Inputs / Fields
- **Style:** [stroke, background, radius]
- **Focus:** [treatment, e.g. glow, border shift, etc.]
- **Error / Disabled:** [if applicable]

### Navigation
- **Style, typography, default/hover/active states, mobile treatment.**

### [Signature Component] (optional; if the project has a distinctive custom
component worth documenting)
[Description.]

## 6. Do's and Don'ts

Concrete, forceful guardrails. Lead each with "Do" or "Don't". Be specific:
include exact colors, pixel values, and named anti-patterns the user
mentioned in PRODUCT.md. Every anti-reference in PRODUCT.md should show up
here as a "Don't" with the same language.

### Do:
- **Do** [specific prescription with exact values / named rule].
- **Do** [...]

### Don't:
- **Don't** [specific prohibition, e.g. "use border-left greater than 1px as
  a colored stripe"].
- **Don't** [...]
- **Don't** [...]
```

Rules that matter for the frontmatter (source: `document.md:43-49`):
- Token refs use `{path.to.token}` (e.g. `{colors.primary}`, `{rounded.md}`).
  Components may reference primitives; primitives may not reference each
  other.
- Colors: hex sRGB only validates cleanly against the external Stitch linter;
  OKLCH/HSL/P3 trigger a linter warning, not a hard error. Pick one canonical
  format per project and do not split the source of truth.
- Component sub-tokens are limited to 8 props: `backgroundColor`,
  `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`.
  Shadows, motion, focus rings, backdrop-filter do not fit this schema and
  belong in a sidecar file instead.
- Scale keys are open-ended (use the project's own naming, not forced
  Material-default names).
- Variants are a naming convention, not schema: `button-primary` /
  `button-primary-hover` / `button-primary-active` as sibling keys.

## PRODUCT.md capture format skeleton

Source: `skill/reference/init.md:128-166` (Step 4: Write PRODUCT.md), commit
`4d849eb75f216109ea7053ed21530a11fafcc786`. This is the strategic ("who /
what / why") counterpart to DESIGN.md's visual ("how it looks") capture.

```markdown
# Product

## Register

product

## Platform

web

## Users
[Who they are, their context, the job to be done. Primary audience; a
secondary audience or a surface-vs-user split only when they apply.]

## Product Purpose
[What this product does, why it exists, what success looks like]

## Positioning
[The single strategic claim every screen reinforces. Not a visual rule, not
an anti-reference.]

## Conversion & proof
[Brand register only. Product register: omit this section entirely, heading
included.]
- Primary and secondary CTA: [...]
- The line a visitor remembers after 10 seconds: [...]
- Belief ladder: [...]
- Proof on hand: [testimonials, case studies, press, or logos, referenced by path]

## Brand Personality
[Voice, tone, 3-word personality, emotional goals]

## Anti-references
[What this should NOT look like. Specific bad-example sites or patterns to avoid.]

## Design Principles
[3-5 strategic principles derived from the conversation. Principles like
"practice what you preach", "show, don't tell", "expert confidence". NOT
visual rules like "use OKLCH" or "magenta accent".]

## Accessibility & Inclusion
[WCAG level, known user needs, considerations]
```

Notes (source: `init.md:168-172`):
- `Register` is a bare value: `brand` or `product`. No prose, no commentary.
  Brand = design IS the product (marketing/landing/portfolio/editorial).
  Product = design SERVES the product (app UI, dashboards, tools).
- `Platform` is a bare value: `web`, `ios`, `android`, or `adaptive`. Missing
  field defaults to `web`.
- Write fields as prose; use bold sparingly, only where a word carries a
  decision, never as a label lead-in on every line.
