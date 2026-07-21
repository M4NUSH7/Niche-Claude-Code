# 07 - Phases, Terminals, and Gates (the execution loop)

## Terminal model

**Scale terminals to the work: 1 if the domains don't split, N if they do.** N is not fixed at
four - it is however many domains genuinely make simultaneous progress without writing the same
files (`references/decision-guide.md` Sec. 1's test). The hard rules that hold at any N: **one
terminal is always `never_blocked`**, and **a gate exists only when work is actively wrong
without it** - not a fixed shape to fill in.

Each terminal owns a **domain**, defined once in `.bld/README.md`. Coursly's build happened to
land on four; treat the table as an illustration of the pattern, not a template to match:

| Terminal | Domain (Coursly) | Primary agent | Gate it controls |
|---|---|---|---|
| T1 | infra / DB / API / ledger | coder (+architect) | `scaffold-complete` tag; ledger merge |
| T2 | auth / workspace / community | coder | - |
| T3 | commerce / automation / notifications | coder | security pass on payments |
| T4 | frontend / design system | coder (+design-reviewer) | design-review before merge |

Opening a terminal = `cd <repo> && claude`, then paste that terminal's bootstrap prompt from
`.initialization/agent_start_prompts.md` (tells it which context file, which phase file, which
agent/model/effort, and its domain rules).

## Phase files: the checkbox queue

`.bld/tN/phases.md` = markdown checkboxes grouped by phase, with inline markers:

```markdown
## Phase 0 - Scaffold (T1 only, sequential)
- [x] Turborepo + pnpm workspace
- [x] ESLint module-boundary rules
- [ ] GATE SIGNAL: commit "chore: scaffold-complete" + git tag scaffold-complete

## Phase 2 - Payments
- [ ] Khalti sandbox checkout          <!-- Security pass required -->
```

**The loop:** first unchecked item = current task -> do it -> check it -> next. Progress state is
the file itself; any session, any agent, any day can resume with zero handover.

### The third state: `- [~]` superseded

```markdown
- [x] Rolling z-score features
- [~] LSTM sequence model -> see memory/decisions/2026-05-02-lstm-to-gbm.md
- [ ] Gradient-boosted meta-model
```

| Mark | Meaning | Counted as |
|---|---|---|
| `- [ ]` | open | the queue |
| `- [x]` | done, still standing | progress |
| `- [~]` | **superseded** - built, then pivoted away from | **neither** |
| `- [!]` | **blocked / awaiting-human** - stuck on a decision only a human can make | **neither** |

Leaving killed work `- [x]` makes the file assert code that no longer exists; flipping it back to
`- [ ]` silently re-queues work you deliberately abandoned. A `- [~]` **without a pivot-note link
is a violation** (`harness_status.py`) - an unlinked one is an undocumented deletion, not a pivot.
Doctrine: `11_pivots.md`. `- [!]` is the same idea for a task that isn't wrong, just stuck - link
a `memory/decisions/` note (see `06_memory_and_context.md` Sec. "The fourth checkbox state").

## Gate rules (cross-terminal sequencing)

- Dependent terminals are **blocked until the gate tag exists** (T2/T3/T4 wait for T1's
  `scaffold-complete`; T3 payments wait for T1's ledger).
- **One terminal never_blocked + gate-only-when-work-is-actively-wrong** are the two hard rules,
  independent of how many terminals the plan uses (Coursly: T4 design system never blocks).
- **Security gate:** anything touching money/identity/admin paths requires the `/security`
  checklist to fully pass before merge.
- Human pre-flight gates live in `.initialization/README.md` (e.g. "legal opinion commissioned
  before any production payment code") - business conditions, not code conditions.

### Gate revocation (when a pivot invalidates a gate)

A gate tag means **"this is true now"**, not "this happened once". If a pivot tears out the work
a gate certified, the tag is **revoked and must be re-earned**:

```bash
git tag -d <tag>                      # local
git push origin --delete <tag>        # remote
```

Then mark that GATE line `- [~]` with its note link, and re-open the work that must re-earn it.
**`gate_guard.py` needs no change** - it already asks "does the tag exist?" and will now correctly
answer no, so dependent terminals re-block automatically. `harness_status.py` reports the mismatch
for free. This is the one place a pivot can cascade into a work stoppage, and that is the point:
dependents must not keep building on a certification you invalidated.

## Phase ladder (Coursly's 16-week shape, adapt freely)

Phase 0 scaffold (single terminal, sequential) -> Phase 1 foundation (parallel starts) ->
Phases 2-5 domain build-out with per-phase gates -> Phase 6 hardening/launch.

## CI/deploy backdrop

- CI: single workflow, sequential jobs `lint -> typecheck -> test-unit -> build`
  (pnpm + Node 22, frozen lockfile). (Audit: parallelize the first three.)
- Deploy: merge to `main` -> Coolify webhook -> rolling restart; rollback = redeploy previous
  image tag in the UI (<60 s). Resource definitions as JSON in `.coolify/`.

## Adapting to the Trading terminal

Natural terminal split for this repo's two-plane architecture:
T1 = engine core (providers/pipeline/contracts - owns the `lake-trusted` gate = G1),
T2 = quant (features/signals/training - gated on G1, owns G2/G3),
T3 = harness (LLM routes/safeguards - gated on contracts),
T4 = product plane (nit CLI/Tauri/web - never blocked; builds against artifact schemas from day 1).
Gates map 1:1 onto the project's existing G1-G5 promotion gates.
