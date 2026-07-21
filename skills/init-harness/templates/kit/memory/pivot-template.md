---
type: pivot
date: YYYY-MM-DD
approved-by:                       # REQUIRED - a human name. No agent self-approval (principle #11).
supersedes: "[[<decision-note>]]"  # Obsidian link type -> auto-generates a backlink on the old note.
gates-revoked: []                  # tags deleted via `git tag -d` + `git push origin --delete`. [] if none.
revisit: YYYY-MM-DD                # ~90 days out. Lightweight check, not a process.
revisit-outcome:                   # ONE line, filled in at revisit. Leave blank until then.
tags: [decision/pivot]
---

# <Short title: what we stopped doing, and what replaced it>

## Why (with context)

What we believed going in, what we learned, what forced the call.
Include the evidence - a pivot without evidence is a mood.

## Current State -> Pivot State

<what exists on disk today>
->
<what will exist instead>

## Pros / Cons

| Pros | Cons |
|---|---|
|  |  |

<!-- Cons is not optional. A pivot with no cons means you haven't found them yet. -->

## Salvaged vs. Deleted

- **SALVAGED:** <what was kept, and where it was refactored to>
- **DELETED:** <what was removed outright>

<!-- The load-bearing field. "Took parts and refactored" is how a module ends up
     half-old and half-new with no explanation. This is the only place it's recorded. -->

## Now Forbidden

<what no agent should retry, and why>

<!-- Mirror this into agent_compile_logs as a FAILURE row so it's queryable:
     the generated SessionStart hook queries `WHERE status='FAILURE'` and prints it at the
     start of every session (see 05_hooks_and_logging.md - D1). checkpoint.sh compresses logs
     into this table; it does not by itself surface them to a fresh session - the hook does.
     The vault holds the narrative; the db holds the warning. -->

---

## Checklist (delete before committing)

- [ ] Human approved
- [ ] Superseded tasks marked `- [~]` in `.bld/*/phases.md`, each linking this note
- [ ] Invalidated gate tags revoked (local + remote); their GATE lines marked `- [~]`
- [ ] `agent_compile_logs` FAILURE row inserted
- [ ] Salvage rule appended to the relevant `.claude/agents/*.md` (one line)
- [ ] `harness_status.py --check` clean
- [ ] Note + phases + agent-rule committed together
