---
name: init-harness
description: One-shot initialization of a parallel-terminal Claude Code build harness in a project - phase checkboxes as the task queue, pinned model/effort per agent, mechanical git-tag gates, hardened read/gate/log hooks, Obsidian memory vault plus SQLite agent memory, human-gated pivots, and CI drift checks. Use when the user says "/init-harness", "init-harness", "initialize the harness", "set up the build harness", "scaffold this project's harness", "bootstrap the agent harness", or drops in a project-context.yml and asks to initialize. Also use when a project needs multi-terminal agent orchestration with gates, or when an existing harness must be verified/repaired (hooks not firing, guards not blocking, .agents drift). Do NOT use for adding a single agent or skill to an existing project.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# init-harness

Stands up a complete agentic build harness in one pass: **preflight -> intake -> scaffold ->
content -> derive -> verify.**

## The one thing to understand first

**This skill is ~80% a config generator.** The heavy lifting already exists and is tested:
`sync_harness.py` generates the entire `.agents/` tree, stamps model IDs, and emits the skill
indexes and prompt stubs; `harness_status.py --write` generates the Active Context block and
`REALITY.md`. The source docs say so outright - *"the config is the only step that requires
thought."*

So do **not** write a new generator. Write a good `harness.config.json`, run the scripts that
exist, and prove the result works. Anything else fails the simplicity ladder at rung two
(*already in the codebase?*).

## Division of labour - do not blur it

| Layer | Who | What |
|---|---|---|
| **Structure** | `scripts/scaffold.sh` | ~40 dirs, kit copy, `git init`, sqlite init. **One call, zero judgment.** |
| **Content** | **you (the agent)** | config, agent prompts, commands, `CLAUDE.md`/`AGENTS.md`, context packs, `.bld/*/phases.md`, `memory/INDEX.md` |
| **Derivation** | existing scripts | `sync_harness.py` -> `.agents/` + indexes + stubs; `harness_status.py --write` |
| **Proof** | `scripts/verify_init.py` | guards actually **block** |

**Never `mkdir`/copy through tool calls.** Scaffolding directories one-by-one is ~40 round trips
of ceremony for zero judgment. Your tokens go to content. (Unless the user explicitly asks for a
different initialization path - then follow them.)

## Load these

- **`token-efficiency`** - mandatory, and the harness auto-loads it in generated projects. Obey it
  here too: RTK for command output, grep before read, offset/limit, summarize.
- Reference files in this skill load **only when routed** (below). Don't read them all.

## Flow

### 0. Preflight - ALWAYS FIRST, never skip

```bash
python scripts/preflight.py --json
```

**If it fails, stop and report.** Do not generate anything.

> **Why this is non-negotiable.** The original template pinned `py -3` for every hook. On a
> machine with no `py` launcher that exits 127 - the hook process never starts. It doesn't fail
> *open*, it fails **absent**: no block, no log row, no audit trail. The harness looks installed
> and enforces nothing. Bare `python` is no safer (Store stub / foreign venv).
>
> **Pin the verified absolute path preflight returns.** Never a bare name, never a venv.

**Toolchain rule:** tools the harness shells out to (`python`, `git`, `sqlite3`, `rtk`) install to
the **global/user toolchain** - `uv python install 3.11`, `scoop install git sqlite rtk`. Never
vendored in-project, never a foreign venv, never left to whatever an installer chose. Project
*libraries* (pnpm/cargo/uv deps) are unaffected. If a framework is added later, its **tools** go
global too.

### 0.5 - Context bootstrap: `context/` is a PREREQUISITE, not an output

**Do not scaffold a folder you haven't read.** `harness.config.json` is derived from what the
project *is* - domains, gates, sensitive paths. If the source material is a pile of loose files at
the root, every one of those derivations is a guess.

Classify first (`ls -la`, `find . -maxdepth 2 -type f | head -40`):

| State | Do |
|---|---|
| Empty / only `.git` | **greenfield** - interview, write `context/` from the answers |
| Loose docs/specs, no source tree | **unorganized** - **triage into `context/` FIRST** -> `references/context-bootstrap.md` |
| Real source tree | **brownfield** - do NOT move source; derive `context/` *from* the code |
| `context/` exists and is populated | **ready** - read it, confirm it's current |

Triage moves vision/roadmap -> `context/.initial/` (frozen, reference-only), architecture ->
`architecture/`, requirements -> `context/architecture/`. **Ask before moving anything** - one
confirmation, then `git mv` in one shell call. Never move source. Never move secrets - flag them.

Scaffolding before reading bakes a wrong `terminals{}` into the files the harness treats as truth,
and `gate_guard.py` then blocks legitimate work on boundaries nobody agreed to.

### 1. Intake

If a `project-context.yml` exists -> read it. Else -> offer the template
(`templates/project-context.yml`), or run the interview directly.

**Infer mechanically** (never ask): `project` name, `sharedWritePaths`, `readGuard`, `gateGuard`,
`logging`, the core four skills, `docRouting` (from `architecture/*.md` that actually exist), SoT
seed categories (from the goal prose).

**ASK - never guess.** Two `AskUserQuestion` rounds (<=4 each), **every option carries a
Recommended marker**. Never silently pick a permission posture for someone.

**Round A - shape:**
1. **Terminal split** - options from directories that actually exist, plus *"Single terminal (t1)"*
   **(Recommended when unstated)**.
2. **Gate topology** - *"scaffold-complete only"* **(Recommended)** / *"+ security-pass on the
   sensitive domain"* / custom.
3. **Sensitive paths** - prefilled from the kit defaults, filtered to real dirs.
4. **Model tiers** - kit defaults **(Recommended)** / custom.

**Round B - permissions and rules** (-> `references/permissions-and-rules.md` for the full option
text; do not improvise these):
1. **Permission profile** - **Balanced (Recommended)** / Strict / Permissive / Custom.
2. **Network + installers** - **Ask each time (Recommended)** / Allow / Deny.
3. **Git attribution** - **No attribution (Recommended, DEFAULT)** / Yes / Custom.
   Claude does **not** tag itself as a contributor unless the user opts in.
4. **Production-grade bar** - **Solid small tool (Recommended)** / Multi-user product /
   High-scale. Right-sizes the architecture-decay checks (-> `references/architecture-decay.md`).

> A hallucinated terminal split or gate topology is worse than a question: gates are the
> concurrency contract, and a wrong one silently unblocks work that should be blocked. **Ask.**
>
> Same for permissions. The kit's own ancestor shipped `Bash(*)` with an empty `deny` - root
> access presented as a default. `deny` beats `ask` beats `allow`, and the non-negotiable deny
> list (force-push, hard reset, secret reads, `.agents/` writes, **`git tag -d`**) is re-stamped
> into *every* profile including Permissive. `git tag -d` is denied to agents on purpose: gate
> revocation is a human-approved pivot action.

### 2. Scaffold (shell)

```bash
bash scripts/scaffold.sh <project-root> <this-skill-dir> t1 t2 t3
```

### 3. Content (you)

Write, in this order:

1. **`harness/harness.config.json`** - the one file that matters. `toolchain.python` = the
   **verified absolute path** from preflight. `sessionDefault` = Opus latest (the interactive
   session default - deliberately **not** `models.workhorse`, which pins the coder agent).
   Model **rankings** follow token-efficiency: expensive thinks -> cheap types -> cheapest logs
   (`thinker`/`workhorse`/`utility`).
   **`maxEffort: "high"`. Never `"max"`** - `max` is a per-task escalation the user asks for, never a
   default; a harness shipping `max` burns reasoning budget on mechanical work forever, silently.

   > **The pin only binds if you DON'T pass `model:` at spawn** (measured 2026-07-17). The Agent
   > tool's `model:` takes a **tier alias** (`sonnet`/`opus`/`haiku`), not a model ID - passing it
   > resolves to *latest of that tier* and **silently overrides** the ID `sync_harness.py` stamped
   > into the frontmatter:
   >
   > | Spawn | Runs as |
   > |---|---|
   > | `subagent_type: coder`, **no `model:`** | **`claude-sonnet-4-6`** - the config's pin [OK] |
   > | `subagent_type: coder`, `model: "sonnet"` | `claude-sonnet-5` - pin overridden WARNING |
   >
   > So: **stamp the pin in the config, then spawn with NO `model:` argument.** Pass `model:` only for
   > ad-hoc `general-purpose`/`Explore` agents that carry no stamped pin. **Say this in the generated
   > `CLAUDE.md` + `AGENTS.md`** - it is the least discoverable rule in the harness, and the mistake
   > costs money silently rather than erroring.
2. **Agent prompts** in `.claude/agents/` - architect, planner, coder, reviewer,
   `<domain>-reviewer`, `verifier` (runs `harness/verify_goal_packet.py` against the goal packet -
   a real mechanical check, not the coder's self-report; see Part V.3 and
   `templates/docs/12_graph_of_loops.md`), logger, plus optional `research`/`scout`
   if the project needs it. Leave `model:`/`effort:` out; sync stamps them.
   -> route to `templates/docs/01_core_principles.md` and the source `03_agents_and_models.md`.
3. **Commands** (`/plan`, `/code-review`, `/security`, domain ones) + `output-style/default.md`.
4. **`CLAUDE.md`** (session ritual, agents table referencing the config - never restate model IDs,
   effort ceiling, skills triggers, explicit "Do NOT" list, and a note that **the real write
   sandbox is your terminal's git worktree** (`.claude/worktrees/tN/` on branch `harness/tN`,
   spawn agents with `isolation: "worktree"`) - `gate_guard.py` now only blocks `sensitivePaths`
   and human-gated actions, not general domain boundaries, and its matcher
   (`Write|Edit|MultiEdit|NotebookEdit`) never sees `Bash`, so a `cd` out of your worktree still
   escapes both the hook and the worktree boundary; see `05_hooks_and_logging.md` Sec. "Worktree
   write-gate (C1/C3)") and **`AGENTS.md`**.
5. **Context packs** - `context/agents/tN-context.md`, one per terminal. Each sets
   `HARNESS_TERMINAL=tN` + `CLAUDE_AGENT_NAME`. **Env-var names only - never a credential value.**
6. **`.bld/README.md` + `.bld/tN/phases.md`** - GATE lines must contain the exact tag names from
   `gates{}`. Four checkbox states (`- [ ]`, `- [x]`, `- [~]`, `- [!]` blocked/awaiting-human).
7. **`memory/INDEX.md`** - hub. Leave the Active Context block to `harness_status.py --write`;
   hand-written status is the second bookkeeping system the rules forbid.

### 4. Derive (existing scripts)

```bash
<verified-python> harness/sync_harness.py            # .agents/, models, indexes, stubs
<verified-python> harness/sync_harness.py --check    # must print OK
<verified-python> harness/harness_status.py --write  # Active Context + REALITY.md
```

### 5. Verify - prove it, don't assume it

```bash
<verified-python> scripts/verify_init.py <project-root>
```

Asserts guards **block**, gates **gate**, logger **logs**. **"Files exist" is not verification.**
If anything fails, fix it before the user builds on the harness - a harness that doesn't block is
decorative.

## Reference routing (load only what you need)

| Need | Read |
|---|---|
| **Unorganized/brownfield folder; what goes where in `context/`** | `references/context-bootstrap.md` |
| **Permission MCQ text, profiles, deny list, agent rules** | `references/permissions-and-rules.md` |
| **Code-quality/scalability checks; arch doc format; what NOT to build** | `references/architecture-decay.md` |
| Context-file fields; ask-vs-infer table | `references/context-file-schema.md` |
| Terminal split, gate topology, model tiers, sensitive paths | `references/decision-guide.md` |
| Pivots: `- [~]`, gate revocation, note template, SQLite row | `references/pivot-mechanism.md` |
| What verification proves and why | `references/verification.md` |
| Goal packets, declared terminals, bounded retries, blocked/ambiguity routing | `templates/docs/12_graph_of_loops.md` |
| Full doctrine to emit into the project | `templates/docs/*.md` |

## Hard rules

- **Never stamp an unverified interpreter.** Preflight or stop.
- **Never pass `model:` when spawning a harness-defined agent.** The stamped frontmatter carries the
  pinned ID; the Agent tool's `model:` is a **tier alias** that overrides it with latest-of-tier.
  The argument you would add to "enforce" routing is the one thing that breaks it. Verify by
  **probe** - config, `settings.json`, and frontmatter agreeing is not proof; none of them is the
  runtime. `verify_init.py` proves guards block and gates gate, but nothing proves models route:
  spawn with no `model:`, ask the agent to name its model, assert it matches `models[role]`.
- **`maxEffort: "high"`, never `"max"`.** Agents never self-escalate; only the human raises effort.
- **Never hand-edit `.agents/`** - generated; CI fails on drift.
- **Never hand-add a hook to `<project>/.claude/settings.json`.** `sync_harness.py` assigns
  `settings["hooks"]` wholesale - every run erases hand-added hooks silently (no warning, the hook
  just stops firing). Add them to the generator instead. Scope is the project tree only: sync never
  reads or writes `~/.claude/settings.json`.
- **Never duplicate a user-tier hook in the harness.** Hooks from all tiers merge and *all* fire.
  Check `~/.claude/settings.json` before adding one - a harness hook on `PreToolUse`/`Bash` would
  fight the token-efficiency skill's `rtk-rewrite.sh` (two rewriters, each mangling the other's
  output). The harness deliberately claims `Read`/`Write|Edit` and leaves `Bash` to the user tier.
  Two hooks on `SessionStart` is fine - they inject different things and neither wins.
- **Never put a credential in a tracked file** - env-var names only.
- **Never infer gates or terminal splits from prose.** Ask.
- **Never hand-write a status block** - `harness_status.py --write` generates it.
- **Pivots are human-gated.** An agent may propose; only a human approves.
- **Verify behaviour, not existence.**
