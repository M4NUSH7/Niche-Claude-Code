# init-harness

**Stand up a parallel-terminal Claude Code build harness in one pass - with mechanical gates, scoped subagent handoffs, and enforced definition-of-done.**

## What it does

Initializes a complete agentic build harness in a project: `preflight -> intake -> scaffold -> content -> derive -> verify`. It is ~80% a config generator - the heavy lifting (`sync_harness.py`, `harness_status.py`) already exists and is tested; you write one good `harness.config.json`, run the scripts, and prove the result blocks.

Core mechanisms:

- **Phase checkboxes as the task queue** - `.bld/tN/phases.md`, first unchecked box = current task, plus a `- [!]` blocked/awaiting-human state.
- **N-terminal parallelism** - scale terminals to the work (1 if the domains do not split, N if they do); the only hard rule is one terminal `neverBlocked`, and a validator enforces it.
- **Mechanical git-tag gates** - a gate is a git tag meaning "this is true now"; `gate_guard.py` blocks by-design, not by discipline.
- **Worktree write isolation** - each terminal gets its own git worktree (`.claude/worktrees/tN`) as its write sandbox; the hook is kept only for sensitive paths + human-gated actions.
- **Per-terminal SQLite memory** - `.agents/logs/tN.db` shards + a derived `master.db`; logging is a mechanical hook byproduct, and FAILURE recall is one query surfaced at SessionStart (no ritual, no reading the whole log pile).
- **Goal Packets + graph-of-loops** - every orchestrator->subagent handoff carries a structured brief (`objective`, machine-checkable `success_criteria`, `scope_boundaries`, `inputs`, `outputs`, `budget`, `escalation`) and declared terminal conditions checked in code.
- **Enforced definition-of-done** - `verify_goal_packet.py` runs the `success_criteria` as real checks, assigns the terminal (`success/partial/failure/ambiguity/blocked`) mechanically, and writes a FAILURE ledger row - "works until DoD" is not an honor system.
- **Pinned model/effort per agent, CI drift checks, human-gated pivots.**

## Why it works

The one meta-lesson behind the design: **the parts of a harness that survive are mechanical and readable; the parts that erode require an agent to remember a ritual against the grain of how agents work.** So every rule is a hook, a generator step, or a git tag - never an instruction an agent must remember - and every mechanism is proven by a probe that fails when it is broken (`verify_init.py`), not by files merely existing.

The Goal Packet + declared-terminals convention fixes the three things retrospectives found most broken: inferred-done (a subagent claiming success), unbounded silent retries (hallucination loops), and lost failures (a killed agent leaving no trace). Retries are bounded and visible; blocked/ambiguity are first-class terminals that route to a handoff note + a recall-surfaced ledger row.

## How to use

Say `/init-harness` (or "initialize the harness", or drop a `project-context.yml`). It runs preflight, asks the few decisions that cannot be inferred (terminal split, gate topology, sensitive paths, model tiers, permission posture) as MCQs, scaffolds, generates, and verifies that the guards actually block.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The flow, the division of labour, the hard rules |
| `scripts/preflight.py` | Verifies the interpreter path before anything is stamped |
| `scripts/scaffold.sh` | Deterministic structure: dirs, kit copy, git init, worktrees, DB shards |
| `scripts/verify_init.py` | Proves guards block, gates gate, routing binds, DoD is assigned in code |
| `templates/kit/harness/sync_harness.py` | Generates `.agents/`, stamps model IDs, emits indexes |
| `templates/kit/harness/verify_goal_packet.py` | Runs success_criteria, assigns the terminal, writes the ledger row |
| `templates/kit/harness/build_master.py` | Derives `master.db` from per-terminal shards |
| `templates/kit/harness/memory-schema.sql` | The vendored flat log/ledger schema |
| `templates/kit/hooks/*.py` | Read guard, gate guard, tool-use logger, log folder |
| `templates/goal-packet.template.yml` | The orchestrator->subagent brief |
| `templates/docs/12_graph_of_loops.md` | The goal-packet + terminal-condition doctrine |
| `references/*.md` | Decision guide, permissions, pivots, verification, context bootstrap |

## Scope note

This is a **Claude Code** tool by nature - it initializes a persistent machine harness (`~/.claude` hooks, worktrees, per-terminal DBs). It does not have a Cowork edition because Cowork's ephemeral, account-loaded model does not fit the multi-terminal machine harness.
