# Design Principles Reference (LAYER-3)

LAYER-3 principle reference for the UI skill's component-selection logic.
License: MIT. Source: `designer-skills` repo, commit `acc3e57` (local clone at
`.scratch/designer-skills/`). Prose below is lifted verbatim (or lightly
trimmed of "You are an expert in..." preamble) from the source SKILL.md files
cited under each heading. Do not paraphrase further when copying into a
downstream skill - copy the concrete-rule blocks as-is.

This file is a principle reference, not a UI-generation skill by itself: it
tells a coding agent WHY a layout/typography/color choice is correct and WHAT
the numeric rule is. It does not choose components or libraries (see "Does
NOT cover" at the end).

---

## Von Restorff Effect (standout element) -- PRIORITY

Source: `ui-design/skills/von-restorff-effect/SKILL.md`

**Principle**: An item that differs from its surroundings is more likely to
be noticed and remembered. Visual homogeneity is the baseline; deviation
draws the eye.

**When it applies**: Any screen with exactly one thing the user should do or
notice first -- primary CTA among secondary actions, the recommended pricing
tier, the active nav item, the one actionable notification, the current step
in onboarding.

**Concrete rule**:
- One (or very few) items may deviate. Surrounding items must stay visually
  consistent with each other. If everything is differentiated, nothing is.
- Applications:
  | Context | How to Apply |
  |---|---|
  | Call to action | One filled/primary button; all others ghost or text |
  | Pricing | Highlight one recommended tier; reduce visual weight of others |
  | Navigation | Active state distinctly different from inactive |
  | Data tables | Use row highlight or bold type for the key record |
  | Notifications | Badge or accent color reserved for actionable items only |
  | Onboarding | One step or card at a time, visually isolated from upcoming steps |
- What to avoid: applying the effect to multiple competing elements (defeats
  the purpose); using it decoratively (random color pops train users to
  ignore them); relying on color alone (pair with shape, size, or weight).
- Checklist: decide in advance the single most important element per
  screen/section; audit for "isolation inflation" (every new feature
  requesting highlight treatment degrades the system); differentiate on all
  states (hover, focus, disabled); verify the differentiation survives a
  grayscale/colorblindness check.

---

## Visual Hierarchy

Source: `ui-design/skills/visual-hierarchy/SKILL.md`

**Principle**: Establish clear visual hierarchy so users see the most
important content first and can scan efficiently.

**When it applies**: Every screen -- especially hero sections, card layouts,
forms, and navigation, where multiple elements compete for attention.

**Concrete rule**:
- Hierarchy tools and thresholds:
  - Size: use differences of at least **1.5x** between levels for a clear
    distinction.
  - Weight: bold text, thicker strokes, filled icons carry more visual
    weight than light variants.
  - Color/contrast: high contrast attracts attention; reserve for CTAs,
    status, emphasis.
  - Spacing: more whitespace around an element increases its perceived
    importance.
  - Position: top-left (LTR) is seen first; F-pattern and Z-pattern scanning
    govern above-the-fold placement.
  - Density: isolated elements stand out; grouped elements are scanned as a
    unit.
- Hierarchy levels: Primary (page title, primary CTA) -> Secondary (section
  headings, key content) -> Tertiary (supporting text, metadata) ->
  Quaternary (fine print, timestamps).
- Common patterns: hero = large type + image + single CTA; card = image >
  title > description > action; form = label > input > helper text > error.
- Checklist: squint test (blur eyes -- hierarchy should still read); one
  primary action per view; don't let elements compete for attention -- choose
  what matters most.

---

## Layout Grid

Source: `ui-design/skills/layout-grid/SKILL.md`

**Principle**: Define a responsive grid system that creates consistent,
flexible page layouts across breakpoints.

**When it applies**: Any multi-column or responsive layout -- page shells,
dashboards, card grids, forms.

**Concrete rule**:
- Columns: 4 (mobile), 8 (tablet), 12 (desktop) typical.
- Gutters: 16px, 24px, or 32px typical.
- Margins: 16px mobile, 24-48px desktop.
- Breakpoints: e.g. 375, 768, 1024, 1440px.
- Grid types: column grid (equal columns), modular grid (columns + rows),
  baseline grid (4px or 8px vertical rhythm), compound grid (overlapping,
  complex layouts).
- Responsive behavior: fluid (columns stretch proportionally), fixed
  (max-width container, centered), adaptive (distinct layout per
  breakpoint), column dropping (fewer columns at smaller sizes).
- Checklist: consistent gutters/margins; align content to the grid, not
  arbitrarily; test every breakpoint, not just the extremes; allow
  intentional grid-breaking only for deliberate emphasis.

---

## Spacing System

Source: `ui-design/skills/spacing-system/SKILL.md`

**Principle**: Build spacing from one base unit so the whole interface reads
as systematic rather than arbitrary.

**When it applies**: Any padding/margin/gap decision -- component internals,
stacks, grids, page margins.

**Concrete rule (the scale)**:
- Base unit: 4px or 8px.
- Scale: 2xs 2px, xs 4px, sm 8px, md 16px, lg 24px, xl 32px, 2xl 48px,
  3xl 64px.
- Spacing types: Inset (padding inside containers), Stack (vertical space
  between stacked elements), Inline (horizontal space between inline
  elements), Grid gap (space between grid/flex items).
- Application rules: related items get smaller spacing (sm/md); distinct
  sections get larger spacing (lg/xl); page margins stay consistent per
  breakpoint.
- Density modes: Compact = one step down (data-heavy views); Comfortable =
  default; Spacious = one step up (reading-focused).
- Checklist: always use the scale, never an arbitrary pixel value; larger
  gaps between unrelated groups than within a group.

---

## Typography Scale

Source: `ui-design/skills/typography-scale/SKILL.md`

**Principle**: A modular, ratio-based type scale keeps text readable and
harmonious across a product.

**When it applies**: Defining or auditing any set of heading/body/caption
styles.

**Concrete rule**:
- Size scale (ratio-based, e.g. 1.25 major third or 1.333 perfect fourth):
  Caption 12px, Body small 14px, Body 16px (base), Subheading 20px,
  Heading 3 24px, Heading 2 32px, Heading 1 40px, Display 48-64px.
- Weight scale: Regular 400, Medium 500, Semibold 600, Bold 700.
- Line height: Tight 1.2 (headings), Normal 1.5 (body), Relaxed 1.75
  (long-form).
- Letter spacing: Tight -0.02em (large headings), Normal 0 (body), Wide
  0.05em (uppercase labels/captions).
- Responsive: scale down heading sizes on mobile; keep body text at a
  16px minimum for readability; keep line length in the 45-75 character
  range (see Readable Measure below).
- Checklist: use a mathematical ratio for harmony; limit to 4-5 sizes in
  regular use; body text minimum 16px; test with real content, not lorem
  ipsum.

---

## Readable Measure (line length)

Source: `ui-design/skills/readable-measure/SKILL.md`

**Principle**: Measure (line length) governs reading comfort independently
of font size -- too short breaks rhythm, too long loses the eye's place.

**When it applies**: Any body-copy or reading context (articles, docs, UI
descriptions, captions); does NOT apply to display type or short UI strings.

**Concrete rule**:
- Optimal range: **45-75 characters per line** (including spaces); 66
  characters is often cited as ideal.
- By context:
  | Context | Target |
  |---|---|
  | Long-form articles, docs | 55-70 characters |
  | UI body copy, descriptions | 45-65 characters |
  | Captions, helper text | 40-60 characters |
  | Pull quotes, callouts | 30-45 characters |
- Practice: use `max-width: 65ch` as a rough proxy (the `ch` unit approximates
  glyph width); validate by counting characters in real content; widen
  line-height as measure widens.

---

## Color System

Source: `ui-design/skills/color-system/SKILL.md`

**Principle**: A color system needs raw palette, semantic mapping, and
accessibility compliance -- not just hex picks.

**When it applies**: Establishing or auditing any product color palette,
including status/semantic colors and dark-mode mappings.

**Concrete rule**:
- Layers: (1) Brand palette -- primary/secondary/accent with full tonal
  scales (50-950); (2) Neutral palette -- gray scale for text, backgrounds,
  borders, surfaces; (3) Semantic colors -- success (green), warning (amber),
  error (red), info (blue), each with background/foreground/border/icon
  variants; (4) Extended palette -- data-viz, illustration, gradients.
- **Accessibility contrast minimums**:
  - Text on background: **4.5:1** minimum (WCAG AA), **7:1** for AAA.
  - Large text: **3:1** minimum.
  - UI components (buttons, inputs, focus rings): **3:1** minimum against
    adjacent surfaces.
  - Never rely on color alone to convey meaning.
- Checklist: generate full tonal scales, not single swatches; test every
  foreground/background pair for contrast; design for color blindness; plan
  dark-mode mappings from the start, not as an afterthought.

---

## Dark Mode Design

Source: `ui-design/skills/dark-mode-design/SKILL.md`

**Principle**: Dark mode is a redesign of surfaces and color, not a simple
color inversion.

**When it applies**: Any interface that supports (or should support) a dark
theme.

**Concrete rule**:
- Core principles: reduce overall luminance to cut eye strain; use surface
  elevation via lighter shades, not drop shadows; desaturate bright colors
  for dark backgrounds; keep sufficient contrast for readability.
- Surface hierarchy: Background darkest (e.g. `#121212`) -> Surface 1
  (elevated cards, slightly lighter) -> Surface 2 (modals, dropdowns,
  lighter again) -> Surface 3 (tooltips, menus, lightest dark).
- Color adaptation: reduce primary color saturation 10-20%; adjust
  error/warning hues for dark-background contrast; use off-white text
  (`#E0E0E0`), not pure white (`#FFFFFF`); use subtle, low-opacity white
  borders.
- Accessibility: minimum 4.5:1 contrast for body text (same AA floor as
  light mode); respect `prefers-color-scheme`; still provide a manual
  toggle alongside auto-detection.
- Checklist: don't just invert -- redesign surfaces; test every component in
  actual dark mode, not just theory; use semantic tokens so switching is
  effortless.

---

## Responsive Design

Source: `ui-design/skills/responsive-design/SKILL.md`

**Principle**: Layouts and interactions must adapt across screen sizes,
pixel densities, and input methods -- design for content, not devices.

**When it applies**: Any interface that will render on more than one
viewport or input type (virtually all of them).

**Concrete rule**:
- Strategies: Fluid (percentage widths), Adaptive (distinct layout per
  breakpoint), Mobile-first (start smallest, enhance upward), Content-first
  (let content needs drive breakpoints).
- **Common breakpoints**:
  | Range | Device |
  |---|---|
  | 375-639px | Small / phones |
  | 640-1023px | Medium / tablets |
  | 1024-1439px | Large / laptops |
  | 1440px+ | Extra large / desktops |
- Patterns: column drop (fewer columns at smaller sizes); reflow (stack
  horizontal elements vertically); off-canvas (hide secondary content behind
  a toggle); priority+ (show most important, overflow the rest).
- Input adaptation: touch targets **44px minimum**; mouse gets hover states;
  keyboard needs visible focus indicators and logical tab order.
- Checklist: test on real devices, not just browser resize; consider
  landscape and portrait; test accessibility tooling at each breakpoint.

---

## Aesthetic-Usability Effect

Source: `ui-design/skills/aesthetic-usability/SKILL.md`

**Principle**: Users perceive polished, consistent interfaces as more usable
even before interacting with them -- consistency signals quality; the effect
can mask, but does not fix, real usability problems.

**When it applies**: First impressions (onboarding, landing, empty states),
error states, trust-critical flows (payment, health, legal), and any
design-system rollout.

**Concrete rule**:
- Consistent spacing, alignment, and type scale signal a well-considered
  product; visual noise or inconsistency makes users doubt reliability.
- Apply it: (1) enforce one spacing/type scale everywhere; (2) align to
  grid -- misalignment reads as low craft even when functional; (3) keep
  visual weight consistent across similar actions (buttons, links, icons);
  (4) design error/empty/loading states with the same care as primary
  flows; (5) audit for visual inconsistency before launch -- one rough
  screen lowers perceived quality of the whole product.
- Risk / limit: aesthetic polish lowers tolerance for friction but does not
  replace sound information architecture -- pair it with real usability
  testing, don't substitute for it.

---

## Law of Proximity (Gestalt grouping by distance)

Source: `ui-design/skills/law-of-proximity/SKILL.md`

**Principle**: Elements close together are perceived as a group; whitespace
separates, tightness implies relationship. This is the most fundamental
layout-grouping tool -- more spacing between groups, less within a group.

**When it applies**: Forms (label-to-input), card content, section headers,
button groups, data rows, icon+label pairs -- any place grouping must be
communicated without borders.

**Concrete rule**:
- Ratio of within-group spacing to between-group spacing creates the
  hierarchy; there is no fixed pixel value, only relative consistency.
- | Pattern | Proximity Rule |
  |---|---|
  | Form fields | Label tighter to its input than to the next field |
  | Card content | Title/body/metadata tight; card separated from neighbors |
  | Section headers | Less space below header (to content) than above it |
  | Button groups | Related actions tight; destructive action separated |
  | Data rows | Row padding tighter than row gap |
  | Icon + label | Icon and label tight; pairs separated from each other |
- Checklist: use a consistent spacing scale (4/8/16/24/32px...) so proximity
  reads systematically; never let a border do the job spacing should do;
  squint-test groupings for legibility without reading content.

---

## Law of Common Region (Gestalt grouping by containment)

Source: `ui-design/skills/law-of-common-region/SKILL.md`

**Principle**: Elements enclosed in a shared boundary or background are
perceived as a group, even without proximity -- containment is one of the
strongest grouping signals available.

**When it applies**: Cards, sidebars, modals/sheets, form sections, table
row hover/selection, tag groups, tooltips.

**Concrete rule**:
- Prefer proximity first; add common region only when proximity alone is
  insufficient or the boundary needs to be explicit (an actionable card, a
  form section inside a larger form).
- Use the weakest container that does the job: background before border,
  border before full card surface.
- Pitfalls: cards for everything flattens hierarchy; nested common regions
  create noise -- limit nesting to two levels; a border with no added
  grouping value is clutter.
- Checklist: consistent corner radius, padding, and shadow per design
  system; verify containers still read in low-contrast/dark-mode contexts.

---

## Critique: Visual Hierarchy

Source: `visual-critique/skills/critique-visual-hierarchy/SKILL.md`

**Principle**: Audit whether a screen has one clear entry point, a
deliberate eye-flow path, purposeful weight distribution, and a single
earned emphasis zone.

**When it applies**: Reviewing an already-built or drafted screen before
shipping.

**Concrete rule / checklist** (rate each `pass` / `minor issue` /
`major issue`):
- Entry point: is there a single dominant element, sized/contrasted/
  positioned to match the primary user goal?
- Eye flow: F-pattern, Z-pattern, or an intentional reading order with no
  dead ends or confusing jumps, leading to the primary CTA.
- Weight: size differentials of **at least 1.5x** between hierarchy levels;
  bold/heavy type used sparingly enough to keep signal value.
- Emphasis: exactly one primary emphasis zone per view; color/contrast/
  motion used to emphasize, not overused until they cancel out.
- Common failures: multiple competing primaries; hierarchy flattening
  (levels too similar in size/weight/color); false emphasis (decorative
  elements outweighing functional ones); a CTA visually quieter than the
  content around it.

---

## Critique: Composition (balance, whitespace, rhythm, gestalt)

Source: `visual-critique/skills/critique-composition/SKILL.md`

**Principle**: Evaluate spatial/structural quality -- visual-weight balance,
whitespace as an active element, rhythmic consistency, and gestalt grouping.

**When it applies**: Screen-level layout review, especially multi-section
pages and repeated-item layouts (lists, cards, tables).

**Concrete rule / checklist**:
- Balance: intentional symmetry/asymmetry; heavy elements (dark fills,
  large images, dense text) offset by lighter ones; a clear visual center
  of gravity.
- Whitespace: sufficient macro whitespace between sections, consistent
  micro whitespace between labels/icons; whitespace should guide attention,
  not fragment the layout.
- Rhythm: spacing intervals drawn from a spacing scale; repeated elements
  (cards, list items, rows) keep uniform size and gaps.
- Gestalt: proximity (related close, unrelated separated), similarity
  (same function -> same treatment), figure/ground (foreground clearly
  distinct from background), continuity (alignment leads the eye),
  closure (incomplete shapes still read correctly).
- Common failures: equal-weight two-column layout with no clear primary/
  secondary; inconsistent padding (16px vs 20px vs 24px with no system);
  orphaned elements with no proximity to their group; competing dividers
  that multiply without adding structure.

---

## Critique: Color

Source: `visual-critique/skills/critique-color/SKILL.md`

**Principle**: Audit contrast ratios, palette coherence, semantic color use,
and color accessibility as separate, checkable dimensions.

**When it applies**: Any screen-level color audit before ship.

**Concrete rule / checklist**:
- Contrast: body text must hit WCAG AA **4.5:1**; large text (18px+ regular
  or 14px+ bold) must hit **3:1**; interactive components (buttons, inputs,
  focus rings) must hit **3:1** against adjacent surfaces; flag every
  failing pair with its measured ratio vs. the minimum required; check
  placeholder/disabled text too.
- Palette coherence: only defined token values, no arbitrary colors;
  neutrals/primaries/accents used per their intended role.
- Semantic use: color must never be the *sole* indicator of state (error/
  success/warning) -- pair with icon, label, or pattern; status colors
  applied consistently (red = error, green = success, amber = warning).
- Accessibility: check common color-vision deficiencies (deuteranopia,
  protanopia) and forced-color/Windows High Contrast mode.
- Common failures: link color failing 4.5:1 once underline is removed;
  error state conveyed by red alone; low-opacity placeholder text failing
  contrast; one-off hex values outside the token system.

---

## Critique: Typography

Source: `visual-critique/skills/critique-typography/SKILL.md`

**Principle**: Audit whether the type scale is applied as a system,
whether text is readable in context, whether treatment is consistent, and
whether tokens (not raw values) are used.

**When it applies**: Any screen-level typography audit.

**Concrete rule / checklist**:
- Scale usage: only defined scale steps used; each step used for its
  intended purpose; recommend **>= 1.25x** contrast ratio between adjacent
  steps.
- Readability: body text >= 16px desktop / 14px mobile minimum; line-height
  1.1-1.3 for headings, 1.4-1.6 for body; line length 45-75 characters;
  contrast 4.5:1 body / 3:1 large text (WCAG AA).
- Consistency: semantically equivalent elements (all card titles, all form
  labels) share one type style; alignment intentional, not mixed randomly;
  weights consistent, not randomly varied.
- Token compliance: font-family/size/weight/line-height/letter-spacing all
  set via tokens, not hardcoded.
- Common failures: scale drift (nudging px instead of moving to the next
  defined step); display sizes carrying body line-height (or vice versa);
  centred headings above left-aligned body with no intentional reason;
  more than two active weight levels on one screen diluting contrast.

---

## Critique: Affordance

Source: `visual-critique/skills/critique-affordance/SKILL.md`

**Principle**: Interactive elements must visually announce that they are
interactive; states must be visible; the primary action must be obvious.

**When it applies**: Any screen with buttons, links, controls, or
contextual actions.

**Concrete rule / checklist**:
- Clickability: buttons/links/controls visually distinct from static
  content (color, shape, underline, elevation); watch for false affordances
  (looks clickable, isn't) and missing affordances (is interactive, looks
  static); touch targets **at least 44x44px** on mobile.
- State visibility: default/hover/active/focus/disabled/selected states all
  visually distinct; focus state visible and high-contrast (not just a
  browser default ring on a colored background); disabled states not
  communicated by color alone.
- CTA clarity: single dominant CTA per view; primary CTA filled/solid,
  secondary actions ghost/text; action-oriented label ("Save changes", not
  "OK"); positioned where expected (bottom-right on forms, inline after
  content blocks).
- Discoverability: no critical action hidden behind hover-only on
  touch-inaccessible controls; contextual actions (edit/delete/share)
  visible or indicated, not fully hidden until hover; empty states must be
  actionable; destructive actions visually distinguished from constructive
  ones.
- Common failures: ghost buttons whose border vanishes in low-contrast
  contexts; `outline: none` with no replacement focus state; multiple
  filled CTAs competing on one screen; edit/delete hidden behind hover only.

---

## Does NOT cover

This reference is principle-only. It intentionally excludes:
- Component-library or framework mapping (which button/select/dialog
  primitive to use, which CSS framework or design-system package) -- that
  decision belongs to the UI skill's own component-selection layer, not
  this reference.
- Illustration systems (`ui-design/skills/illustration-style/`) and chart/
  data-visualization selection (`ui-design/skills/data-visualization/`) --
  excluded as out-of-scope for general component selection; data-viz
  specifically overlaps with this environment's separate `dataviz` skill.
- Brand-consistency critique (`visual-critique/skills/
  critique-brand-consistency/`) -- excluded because it is a
  process/procedure for diffing a screen against a project's own
  `mood.md`/`voice.md`/`tokens.md` files, not a portable design principle.
- Information-density critique (`visual-critique/skills/
  critique-information-density/`) -- excluded from the main body as
  IA/content-strategy process rather than a visual/coding-relevant rule;
  not reproduced here.
- All UX-research, design-ops, leadership, personas, and interview
  collections in the source repo -- out of scope per task instructions.
