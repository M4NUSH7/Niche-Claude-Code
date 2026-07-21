# Architecture decay - fighting the vibecode->rot failure mode

The failure this exists for: an app works, features get added, and over months it gets slower,
tangled, and hard to change. Nobody decides to build a mess - it accretes, one reasonable-looking
addition at a time. AI assistance *accelerates* this: it makes adding easy and never gets tired,
so the accretion rate goes up while the review rate stays flat.

**Sourcing note (honest):** an audit of a 20,868-line architecture reference vault produced almost
nothing for this file. Searched across the whole corpus: "N+1" appeared 9 times, all incidental;
"god object" once; "circular dependency", "unbounded growth", "perf cliff" - zero. Such vaults are
organized by **technology** (Docker, Neo4j, gRPC); decay is a **failure-mode** axis. Only the three
rules in Sec. 2 came from it. The rest is written from this harness's own doctrine. Don't go looking
for a checklist in a textbook - textbooks teach technologies, not rot.

## 1. Right-size it first (or this whole file is gold-plating)

**Ask the user; do not assume.** Scale requirements decide how much of this applies.

> **What does "production-grade" mean for this project?**

| Option | What it means | What it turns on |
|---|---|---|
| **Solid single-user / small tool (Recommended default)** | Correct, readable, tested where it matters. No scale story needed. | Ladder + reviewer only |
| Multi-user product | Real users, real data, real uptime | + seams, + perf checks, + observability |
| High-scale / low-latency | Scale or latency is a stated requirement | + everything, + budgets |

**Wrong-sizing is itself decay.** A hexagonal-architecture, CQRS, repository-pattern scaffold for a
CLI tool is *worse* than the mess it prevents: you pay the complexity every day and never collect.
Principle #8's ladder applies to architecture exactly as it applies to code.

## 2. Decay checks - the review checklist

Load on `/code-review` when the diff touches data access, state, or a module boundary. Each item
is a **question with a right answer**, not a principle.

### Data access (the #1 source of "it got slower")
- **Is implicit lazy loading disabled globally?** Lazy loading hides database IO behind innocent
  property access - the N+1 that only appears under production traffic, long after the code
  looked fine in review. Disable it globally; declare loading explicitly per query.
  *(A config-level fix that kills a whole failure class - very ponytail-shaped.)*
- Does this add a query inside a loop? Count the queries per request, not per function.
- Is there an index for the predicate this filters on? Is it used, or is the column wrapped in a
  function / implicitly cast (which silently disables it)?
- Does this fetch a whole row set to compute one aggregate the database could have computed?

### Object size and coupling
- **Are objects small, and do they reference other aggregates by ID rather than by direct object
  reference?** Reference-by-ID is the *forcing function* - it makes god objects structurally hard
  to build, instead of relying on discipline nobody sustains at 6 months.
- Does this module now import from more than ~3 others? Coupling grows quietly, one import at a
  time, and each one is individually defensible.
- Is there a cycle? (`A -> B -> A` is where "I can't test this in isolation" starts.)

### State (the frontend god object)
- **Is API-derived data being put into a global client store?** It shouldn't be - server state
  belongs in a data-fetching/caching layer. The global store accreting server state *is* the
  frontend equivalent of a god object.
- Is state colocated with where it's used, or hoisted "just in case"?

### Growth and boundaries
- What grows without bound here - a log, a cache, a table, a list in memory? What's the ceiling?
- Is this the seam it looks like, or a seam-shaped thing with the internals leaking through?
- If this needs to change in 6 months, how many files does the change touch?

### The meta-question
- **Could this be deleted?** (Principle #8. Ask it first, not last.)

## 3. Decay checks the *harness* already does mechanically

Worth naming, because they're doing anti-decay work nobody labelled as such:

| Mechanism | Decay it prevents |
|---|---|
| `terminals[].paths` + `gate_guard.py` | Module boundaries that erode because "it was easier to just edit it here" |
| `docRouting` | Decisions made without reading the layer's existing decisions - the root of contradictory architecture |
| `readGuard` | Files growing past readability unnoticed (a 3000-line file you can't read is a 3000-line file nobody reviews) |
| `sensitivePaths` | Review depth staying flat while risk rises |
| **Pivots** (`11_pivots.md`) | The big one - dead approaches left in the codebase because deleting felt like waste. **Sunk-cost rot.** |
| `ponytail` ladder | Speculative abstraction at the moment of writing |

**The pivot mechanism is the most under-rated anti-decay tool here.** Most rot isn't bad code - it's
*abandoned direction* left standing next to its replacement, with nothing marking which is live.

## 4. Architecture doc format - `Action:` / `Context:`

The one genuinely non-obvious thing from the vault: its 245 architectural decisions all use a rigid
shape. Adopt it for `architecture/*.md` (the docs `docRouting` points at):

```markdown
> [!action] Architectural Decision: Default to eager loading; disable lazy loading
> **Action:** Disable implicit lazy loading globally in production.
> **Context:** Lazy loading is the silent killer of ORM performance. It masks database IO
> behind innocent property access, producing N+1 queries that only surface under load.
```

**Why this and not prose:** `Action:` is imperative and greppable - an agent can obey it without
interpretation. `Context:` is *why* - which is what lets an agent (or a human) recognise when the
decision no longer applies, rather than cargo-culting it forever. Prose decision docs decay into
essays that agents skim and humans stop updating.

Enforce on the `architect` agent when writing or updating any `architecture/*.md`.

## 5. What NOT to do

Flagged from the vault audit - these are the traps, and they're seductive because they look like
"doing architecture properly":

| Anti-pattern | Why it's worse than the mess |
|---|---|
| GoF pattern catalog as a to-apply list | Speculative abstraction - the exact thing the ladder rejects |
| Wrap the ORM in a custom repository "for polyglot persistence" | Building a seam for a database swap that will never happen. The ORM's own collection type *is* the repository. |
| CQRS / event sourcing on a small project | Its own reference docs say stick to CRUD |
| Micro-frontends | An org-scaling fix for a team-coordination problem you don't have |
| Hexagonal/clean architecture scaffold on day 1 | Pay every day, collect never |

**The tell:** all of these solve a problem you might have later, by giving you a problem now. That
is decay too - it just decays from a different direction.
