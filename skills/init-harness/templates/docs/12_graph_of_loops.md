# 12 - Goal Packets and the Graph of Loops (F1 / Part V.2)

status: current

This doc is **conventions + templates, hand-rolled** - not a running orchestration engine. It
gives an orchestrator (main session or a `thinker`-tier agent) a consistent way to hand work to a
subagent and a consistent way for that subagent to report back, so a multi-hop build reads as one
system instead of N ad-hoc prompts.

## Why this exists

Without a shared handoff shape, every spawn reinvents what "done" means, retries loop silently
when a subagent hallucinates progress, and "blocked" or "ambiguous" results get silently folded
into either success or failure because there's no third bucket to put them in. The goal-packet +
declared-terminals convention fixes the shape of the handoff; it does not require a framework.

## 1. The Goal Packet

A Goal Packet is the structured brief the orchestrator stamps into every subagent handoff -
whether that's a spawned Agent's prompt, a `.bld/tN/phases.md` task, or a `memory/handoff/`
note. Template: `templates/goal-packet.template.yml`.

Fields:

| Field | What it holds |
|---|---|
| `objective` | One sentence: what done looks like, in the world, not "do X" |
| `success_criteria` | **Machine-checkable** conditions - a test passes, a file exists with a shape, a command exits 0. Not "looks good." |
| `scope_boundaries` | What this task must NOT touch (paths, decisions, other terminals' domains) |
| `inputs` | What the subagent starts with - files, context packs, prior handoff notes |
| `outputs` | What it must produce and where (file paths, not prose descriptions) |
| `budget` | Bounded retries/turns/tokens before this counts as a stall, not a struggle |
| `escalation` | Where an ambiguous/blocked result goes - the handoff folder + a `memory/decisions/` note, never silent |

**`success_criteria` is the field that earns its keep.** "Implement the feature" cannot be
checked; "`pytest tests/test_x.py` exits 0 AND `contracts/x.schema.json` validates the new
output" can be. If a packet's success criteria can't be checked by a script or a grep, rewrite it
until it can - that is the whole point of the convention.

## 2. Declared terminals per node - checked in code, not inferred

Every node in the graph (every subagent spawn, every phase-file task) declares its own possible
**terminal conditions** up front, and each maps to exactly one edge:

| Terminal | Meaning | Routes to |
|---|---|---|
| `success` | success_criteria met | next node / next checkbox |
| `partial` | some success_criteria met, not all | orchestrator judgment - retry narrower scope, or split |
| `failure` | attempted, did not meet criteria, no ambiguity about it | `agent_compile_logs` FAILURE row + `- [~]` if it invalidates built work |
| `ambiguity` | criteria themselves are unclear or contradictory | `memory/handoff/` note + `- [!]` blocked checkbox |
| `blocked` | criteria are clear but cannot proceed (missing input, needs a human decision) | `memory/handoff/` note + `- [!]` blocked checkbox |

**"Checked in code, not inferred from the final message"** is the load-bearing phrase. A
subagent's own prose ("I think this worked!") is not the terminal - the orchestrator (or a
`verifier` agent, see `03_agents_and_models.md` / Part V.3) runs the `success_criteria` checks
and assigns the terminal from their actual result. This is the same discipline as gates being git
tags instead of prose: a terminal condition an agent self-reports is exactly the failure mode
this whole harness exists to prevent.

**This is now mechanical, not just described.** `harness/verify_goal_packet.py` (vendored from
`templates/kit/harness/verify_goal_packet.py`, stdlib only) takes a filled goal-packet YAML,
parses it, runs every `success_criteria` item as a shell check, and assigns the terminal FROM THE
EXIT CODES in code:

```
<python> harness/verify_goal_packet.py memory/handoff/tN/2026-07-20-topic.yml [--attempt N]
```

- all criteria pass -> `success` (exit 0)
- some pass, some fail, budget remains -> `partial` (exit 1)
- criteria fail and this attempt exhausts `budget.max_retries` -> `blocked` (exit 4, if the
  packet's declared `inputs` are missing on disk) or `failure` (exit 2, criteria simply unmet)
- criteria are empty or still template placeholders (`<e.g. ...>`) -> `ambiguity` (exit 3)

On `failure`/`blocked`/`ambiguity` it writes a FAILURE-shaped `agent_compile_log` row (same table
`harness_status.py`'s SessionStart recall reads) so a future session sees "do not retry this"
without anyone remembering to write it down. It also tracks a **visible** retry counter in
`<packet>.state.json` next to the packet - see Sec.3. No YAML dependency: it parses the
template's known shape directly (see the script's own docstring), so this runs anywhere the
harness's pinned Python runs, no pip, no network.

## 3. Bounded, visible retries - the anti-hallucination-loop counter

A node that returns `partial` or `failure` may retry, but:

- The retry count is **visible** - written into the handoff/log, not held only in the
  orchestrator's working memory. Mechanically: `verify_goal_packet.py` writes it to
  `<packet>.state.json` (attempts + a timestamped history of every prior terminal/reason) next
  to the packet on every run, and reads it back on the next run rather than trusting an
  orchestrator to remember. `--attempt N` overrides it explicitly when an orchestrator tracks
  its own count instead.
- There is a **budget** (from the Goal Packet's `budget` field) - when exhausted, the node's
  terminal becomes `blocked` or `failure` (never another silent `partial`/retry) - see the exact
  in-code rule in Sec.2.
- Each retry gets a **narrower** scope where possible (the failure should inform the next
  attempt's `scope_boundaries`), not an identical re-run hoping for a different result.

This is the mechanical fix for the "agent loops forever almost-succeeding" failure mode: the loop
is bounded, the bound is visible, and hitting it is itself a first-class terminal.

## 4. Blocked/ambiguity as first-class terminals

`blocked` and `ambiguity` are not failure-with-extra-steps and not success-with-caveats - they
are their own terminal, and both route to the same two places:

1. **`memory/handoff/{tN|session}/{YYYY-MM-DD}-{topic}.md`** - what was tried, what's unclear or
   missing, what a human needs to decide. See `06_memory_and_context.md`.
2. **A FAILURE-shaped ledger row** in `agent_compile_logs` (status can stay `FAILURE` - the
   schema doesn't need a new enum value; the `learnings` text says "blocked, awaiting human" so
   it reads correctly on recall) so a future session's SessionStart FAILURE-recall (`05
   _hooks_and_logging.md` D1) surfaces it without anyone having to remember it happened.

And on the phase-file side: mark the task `- [!]` (06's fourth checkbox state), linking the
handoff note.

## 5. A short declarative graph example

```yaml
# illustrative only - hand-authored per project, not a schema this harness executes
graph:
  - node: t1-scaffold
    goal_packet: templates/goal-packet.template.yml   # filled in per node
    terminals: [success, failure]
    edges:
      success: t2-feature-a
      failure: memory/handoff/t1/  # + FAILURE row, human reviews

  - node: t2-feature-a
    depends_on: [t1-scaffold]       # gate: scaffold-complete tag
    terminals: [success, partial, failure, ambiguity, blocked]
    edges:
      success: t2-feature-a-review
      partial: t2-feature-a          # bounded retry, narrower scope
      failure: memory/handoff/t2/
      ambiguity: memory/handoff/t2/
      blocked: memory/handoff/t2/

  - node: t2-feature-a-review
    terminals: [success, failure]
    agent: verifier                  # runs harness/verify_goal_packet.py - NOT the coder's
                                      # self-report; exit code IS the terminal (see Sec.2)
    edges:
      success: DONE
      failure: t2-feature-a          # bounded retry
```

Every edge is explicit; there is no "the agent decided it was done" edge. That is the whole
convention in one example.

## What this is NOT

Not a workflow engine and not something `sync_harness.py` generates from a declarative graph -
the graph in Sec.5 is still illustrative/hand-authored, not a schema this harness executes end to
end. But terminal-checking itself is **no longer** "apply by hand and hope": `harness/
verify_goal_packet.py` is a real, vendored, stdlib-only script that runs a filled goal-packet's
`success_criteria` and assigns the terminal in code (see Sec.2 above and the script's own
docstring for the exact decision table). It is copied into every scaffolded project's `harness/`
by `scaffold.sh` alongside `sync_harness.py`/`harness_status.py`/`build_master.py` - same kit-copy
step, since it lives in `templates/kit/harness/` - and `scripts/verify_init.py` probes it
mechanically (feed it a packet with one passing and one failing criterion, assert the terminal
and ledger row are real, not self-reported). What is still hand-authored: writing the goal packet
itself (the objective, the criteria, the scope) - that judgment call stays with whoever hands off
the work; only the checking of it is mechanical.
