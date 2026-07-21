# 11 - Pivots (abandoning and refactoring work, on purpose)

status: current

A **pivot** is the moment you conclude that work already built is wrong, and kill or rework it.
This doc exists because the rest of the harness has no concept of one - and, left alone, actively
fights it.

## Why this doc exists

The harness was extracted from a product build with a known destination. This is a research
build: signals die in CPCV, feature families get abandoned, labeling schemes don't survive real
data. **Being wrong on purpose is the job.** `blueprint/00_README_RED_TEAM.md` exists for exactly
that reason.

Four mechanisms resist a pivot, and none of them is a bug - each is correct for forward progress
and wrong for reversal:

| Mechanism | Forward behavior | Behavior after a pivot |
|---|---|---|
| Checkbox queue (`01` Sec. 1) | "first unchecked = your task" | `- [x]` now asserts work that no longer exists on disk |
| `harness_status.py` | reconciles checkboxes <-> tags <-> disk | faithfully reports progress toward an abandoned design |
| Gate tags (`07`) | tag exists => dependents unblocked | tag still certifies a thing you tore out |
| `memory/` (`06` Sec. 25) | append every decision | live and dead decisions look identical forever |

**The audit could not catch this class.** `09_AUDIT.md` asks "did the harness do what it said?"
A pivot is the inverse: the harness does exactly what it says, faithfully, about a plan you no
longer believe. No check in the system can see that.

## The rule

> **A pivot requires human approval.** No agent may unilaterally declare work dead.

This joins the short human-gate list in `01_core_principles.md` Sec. 11. An agent may *propose* a
pivot (and should, loudly, when evidence warrants); only a human approves one. The asymmetry is
deliberate: an agent wrongly continuing costs tokens, an agent wrongly deleting three weeks of
work costs three weeks.

## The four moving parts

### 1. `- [~]` - the superseded checkbox state

```markdown
## Phase 2 - Signals
- [x] Rolling z-score features
- [~] LSTM sequence model -> see memory/decisions/2026-05-02-lstm-to-gbm.md
- [ ] Gradient-boosted meta-model
```

Three states, not two:

| Mark | Meaning | Counted as |
|---|---|---|
| `- [ ]` | open | the task queue - first one is your task |
| `- [x]` | done, still standing | progress |
| `- [~]` | **superseded** - built, then pivoted away from | **neither** |

`parse_phases` excludes `- [~]` from both progress and the queue. Leaving a killed task `- [x]`
makes the file lie; reverting it to `- [ ]` silently re-queues work you deliberately abandoned.
**A `- [~]` line without a pivot-note link is a VIOLATION** - an unlinked one is an undocumented
deletion, not a pivot.

### 2. The pivot note - `memory/decisions/<date>-<slug>.md`

Uses Obsidian typed frontmatter so lineage is a queryable property, not prose. `supersedes:` as
a link type **auto-generates a backlink** - the abandoned note learns it was superseded without
being edited. That is principle #4 working for you: stored once, navigation derived.

```markdown
---
type: pivot
date: 2026-05-02
approved-by: <human name>          # REQUIRED - no agent self-approval
supersedes: "[[2026-03-11-lstm-signal-model]]"   # link type -> auto-backlink
gates-revoked: [signals-v1]        # tags deleted; must be re-earned
revisit: 2026-08-02                # lightweight: did this pay off?
revisit-outcome:                   # one line, filled in AT revisit. blank until then.
tags: [decision/pivot]
---

## Why (with context)
What we believed, what we learned, what forced the call. Include the evidence  - 
a pivot without evidence is a mood.

## Current State -> Pivot State
<what exists today> -> <what will exist instead>

## Pros / Cons
| Pros | Cons |
|---|---|
| ... | ... |

Cons is not optional. A pivot with no cons means you haven't found them yet.

## Salvaged vs. Deleted
- SALVAGED: <what was kept, refactored to where>
- DELETED: <what was removed>

## Now Forbidden
<what no agent should retry, and why>
```

**`Salvaged vs. Deleted` is the field that earns its keep.** "Took parts and refactored" is how a
module ends up half-old and half-new with no explanation; this is the only place that gets
written down.

**`revisit:` is a date plus one line - not a process.** An honest, cheap check on whether the
pivot paid off. Ceremony would just get skipped.

### 3. The queryable warning - `agent_compile_logs`

The narrative lives in the vault; agents don't read the vault before every task. Markdown cannot
give you a "don't retry this" surface, so the same pivot also writes one row:

```sql
INSERT INTO agent_compile_logs (agent, sot_tags, status, learnings, replaced_log_count)
VALUES ('human', 'SIGNAL,FEATURE', 'FAILURE',
        'Tried: LSTM sequence model on 5m bars. Failed: overfit 2019 regime, DSR<0 on CPCV.
         Salvaged: the sequence dataloader (moved to packages/data). Do not retry LSTMs on
         raw bars without regime conditioning. See memory/decisions/2026-05-02-lstm-to-gbm.md',
        0);
```

`checkpoint.sh` compresses logs into these rows, but recall into a fresh session is a SEPARATE
step: it must be wired into the harness's own generated `SessionStart` hook (a
`SELECT learnings FROM agent_compile_logs WHERE status='FAILURE'`, guarded to skip cleanly if
the DB/table is absent - see `05_hooks_and_logging.md` Sec. "SessionStart FAILURE recall (D1)").
Recall is a `WHERE status='FAILURE'` query, not a read. The `learnings` bar from
`token-efficiency/references/memory-system.md` applies exactly: the row **must be useful to an
agent that has never seen the raw logs.**

### 4. The salvage rule - one line on the agent definition

Per memory-system.md Sec. Agent learnings: what *worked* becomes a standing one-line rule appended to
the relevant `.claude/agents/*.md`; what *failed* stays queryable. A pivot writes both.

## Gate revocation

If a pivot invalidates a gate, **the tag is revoked and must be re-earned**:

```bash
git tag -d signals-v1                    # local
git push origin --delete signals-v1      # remote
```

Then mark its GATE line `- [~]` with the note link, and re-open the work that must re-earn it.

**`gate_guard.py` needs no change.** It already asks exactly the right question - *does the tag
exist?* - and will now correctly answer no. Dependent terminals re-block automatically. This is
the one place a pivot can cascade into a work stoppage, and that is the point: a gate means
"this is true now," not "this happened once."

`harness_status.py` detects the revoked tag for free (GATE checked + tag missing -> violation),
which is why the violation message points here.

## Runbook

1. **Agent proposes** - surfaces evidence, does not act.
2. **Human approves** - the gate. Without this, stop.
3. Write the pivot note (`template/memory/pivot-template.md`); fill Pros/Cons and
   Salvaged/Deleted honestly.
4. Mark superseded tasks `- [~] ... -> see memory/decisions/<note>.md`.
5. Revoke invalidated gate tags; mark those GATE lines `- [~]` too.
6. Insert the `agent_compile_logs` FAILURE row.
7. Append the salvage rule to the relevant agent definition.
8. Add `supersedes:` - the backlink appears on its own.
9. Run `harness_status.py --check` -> **must be clean**. If it isn't, the pivot is incomplete.
10. Commit note + phases + agent-rule together. One pivot, one commit.

## Anti-patterns

- **Silent deletion** - removing code without a note. Six months later nobody knows why, and an
  agent rebuilds it.
- **`- [x]` on killed work** - the file lies; status reports lie downstream forever.
- **Pivot without gate revocation** - the worst one. Dependents keep building on a certification
  you invalidated.
- **Agent self-approval** - see the rule.
- **Empty Cons** - you haven't looked hard enough.
- **Re-compressing pivot learnings** - "LSTMs overfit on 2019 data" decays into "we tried some
  models." Compile rows are indexed; archive, never re-compress.

---

# What /init-harness scaffolds for this

`scaffold.sh` creates `memory/decisions/` and drops `_pivot-template.md` there. The config carries
the policy block:

```jsonc
"pivots": {
  "requireHumanApproval": true,      // principle #11 - an agent may propose, only a human approves
  "notesDir": "memory/decisions",
  "supersededMarker": "- [~]",
  "revokeGatesOnPivot": true
}
```

`verify_init.py` asserts both the template and `requireHumanApproval: true` are present.

**Nothing else needs building.** The mechanism is deliberately made of parts that already exist:

| Part | Reuses |
|---|---|
| `- [~]` state | `harness_status.py parse_phases` - three states instead of two |
| Unlinked-pivot violation | the same reconciliation loop that checks gates |
| Gate revocation | `gate_guard.py` **unchanged** - "does the tag exist?" is already the right question |
| Queryable warning | `agent_compile_logs` - the schema token-efficiency already defines |
| Recall | generated `SessionStart` hook, FAILURE-row query - see `05_hooks_and_logging.md` (D1; wiring required, not automatic) |
| Salvage rule | memory-system.md Sec. Agent learnings - already the documented path |

That is the whole point: a pivot is a **human-gated checkpoint**, not a subsystem.

## Emit this into CLAUDE.md

The generated project's `CLAUDE.md` should carry a short pointer, or agents will never know the
mechanism exists:

```markdown
## Pivots
If evidence says built work is wrong, PROPOSE a pivot - do not act. Surface: what's wrong,
what you'd salvage, what you'd delete. A human approves. Never mark work `- [~]`, never revoke
a gate tag, never delete built work on your own authority. See setup/11_pivots.md.
```
