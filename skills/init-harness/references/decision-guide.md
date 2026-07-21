# Decision guide - the four questions worth asking

These are the choices the scripts cannot make. Everything else is derived.

## 1. Terminal split

A terminal = one parallel Claude Code session owning one domain. Split by **who owns which
paths**, not by "what feels like a module."

**Test:** two terminals are justified only if they can make progress *simultaneously without
writing the same files*. If T2 waits on T1 for everything, that's one terminal with two phases.

**Default: single terminal (`t1`).** Splitting later is cheap - you add a `.bld/t2/phases.md` and
a config entry. Un-shipping a wrong split is not: ownership boundaries get baked into the phase
files and the domain-boundary blocks start firing on legitimate work.

**Scale terminals to the work - 1 if the domains don't split, N if they do.** The hard rules are
fixed regardless of N: **one terminal is always `never_blocked`**, and a **gate exists only when
work is actively wrong without it** (Sec. 2). A shape that illustrates the pattern at N=4 - not a
prescribed count:

| Terminal | Owns | Gate posture |
|---|---|---|
| T1 | core / infra / contracts | owns the first gate; blocked by nothing |
| T2 | primary feature domain | blocked until T1's gate |
| T3 | sensitive domain (money/identity/admin) | blocked; owns a security gate |
| T4 | frontend / product plane | **never blocked** - builds against schemas |

A 2-domain project is 2 terminals, not a padded 4; a 6-domain project is 6, not a capped 4. Split
by ownership boundaries that actually exist (Sec. 1's test), never to hit a round number.

**One terminal must be `never_blocked`**, or a stalled gate stalls the whole build.

## 2. Gate topology

A gate is a **git tag** meaning *"this is true now"*. It is not a milestone marker.

Ask: *"If X isn't done, is work on Y actively wrong - not just harder?"*
- Yes -> gate.
- "Harder but fine" -> **not** a gate. Note the dependency in the phase file and move on.

**Every gate you add costs parallelism.** The failure mode isn't too few gates, it's a gate that
blocks work which could have proceeded - the terminal sits idle, and humans start bypassing gates,
which is how audit #2 happened in the first place.

**Default: `scaffold-complete` only.** Add `security-pass-<domain>` if a sensitive domain exists.

**Gates are revocable.** If a pivot tears out what a gate certified, `git tag -d` it - dependents
re-block automatically. Design gates knowing they can be withdrawn; that's what makes them mean
"true now" rather than "happened once."

## 3. Sensitive paths

Globs that auto-escalate the reviewer to the strong model and require the security checklist.

Include: credentials/keys, money movement (payments, ledger, broker, execution), identity/auth,
admin surfaces. Exclude: everything else - every false positive escalates cost and trains people
to ignore the escalation.

**Never put the credential *values* anywhere tracked.** Sensitive paths mark where credentials are
*used*; env-var names only, values in gitignored `.env.local`.

## 4. Model tiers

Follow the token-efficiency hard rule: **expensive thinks, cheap types, cheapest logs.**

| Role | Model | Used by |
|---|---|---|
| `thinker` | `claude-opus-4-8` | architect, planner, reviewer, domain-reviewer |
| `workhorse` | `claude-sonnet-5` | coder (all implementation/debugging), `verifier` (medium effort - runs rejecting-checks/terminal-evaluators, not the coder itself) |
| `utility` | `claude-haiku-4-5` | logger - hook-driven writes only |

**Part V.3 - roster additions (cheap-pins-by-design, unchanged):**

- **`verifier`** - runs the rejecting-checks/terminal-evaluators from a Goal Packet's
  `success_criteria` (`12_graph_of_loops.md` Sec. 2) so a subagent's own "I think this worked"
  is never the terminal condition. Pinned `workhorse` / effort `medium` - it needs enough
  judgment to run and interpret checks, but it is not doing novel design work, so it does not
  need `thinker`-tier reasoning.
- **`research`/`scout` (optional)** - pairs with `deep-research`/agent-reach patterns: fans out
  searches, reports gaps in the evidence. It **reports the gap, never designs around it** - if
  research can't confirm something, that goes in the handoff/decision note, not a guess baked
  into the implementation.

**Checkpoint/compression judgment is NOT pinned to `logger`/Haiku.** Deciding *what* in a batch
of logs is worth compressing into a durable `learnings` row is a judgment call (the
`10_token_efficiency.md` bar: "must be useful to an agent that has never seen the raw logs") -
Haiku is the cheapest-logs tier by design (principle #2), not the cheapest-judgment tier. Assign
checkpoint/compression review to the `reviewer`/`verifier` tier (or keep it fully mechanical via
`checkpoint.sh`'s deterministic parts) - never silently downgrade a judgment call to the logging
pin just because it touches the same logs the logger writes.

**`sessionDefault` (Opus latest) is NOT `models.workhorse`.** The interactive session default and
the coder agent's pin are different things; sharing a value silently downgrades every interactive
session to Sonnet. This bug shipped in the original template.

**Effort ceiling is `high`.** Agents never self-escalate - only a human raises it, temporarily, in
main chat.

**Two documented deviations,** same reasoning both times - the token-efficiency routing table's
pins predate newer models at identical price. It pins the coding-subagent orchestrator to
`claude-opus-4-6`; we use `4-8` (same $5/$25 per MTok, higher ceiling). It pins coders to
`claude-sonnet-4-6`; we use `claude-sonnet-5` (same $3/$15 per MTok tier, near-Opus quality on
coding and agentic work). The *rankings* are unchanged - expensive still thinks, cheap still types.
Both are recorded in `_modelPolicy` so nobody "fixes" them back.

## What never gets asked

`sharedWritePaths`, `readGuard`, `gateGuard`, `logging`, the core four skills, `docRouting`
(derived from files that exist), SoT seed categories (from `goal:` prose). Asking about these
burns the user's attention on choices with a right answer.
