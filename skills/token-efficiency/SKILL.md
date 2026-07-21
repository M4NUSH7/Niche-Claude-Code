---
name: token-efficiency
description: "Comprehensive token optimization: RTK (Rust Token Killer) command-output compression, efficient file/command strategies, hard model-routing rules (Sonnet 4.6 coders, Opus 4.6 orchestrator, Haiku 4.5 logging), Source-of-Truth keyword framework, hybrid SQLite agent memory with checkpoints, and concise output style. Use this skill whenever running dev CLI commands (git, cargo, npm, pytest, docker), spawning coding subagents, writing logs or agent memory, setting up a project's keyword index, checkpointing, or whenever the user mentions 'rtk', 'token efficiency', 'token savings', 'context bloat', 'model routing', 'checkpoint', 'agent memory', or 'source of truth'. Also use to install/verify RTK or its Claude Code hook."
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Token Efficiency

Five pillars, each detailed in a reference file. Apply all of them by default; the user saying "verbose" or naming a model lifts the relevant rule.

Pillars engage by project condition, not all-or-nothing: no dev commands means RTK stays dormant; no subagents means routing is idle; pillars 2, 4, and 5 apply to any project, code or not (SoT categories seed from the project goal, whatever the domain - a writing project seeds BRIEF/VOICE/PLATFORM the same way a web app seeds AUTH/DB/API). Never force an inapplicable pillar.

| Pillar | What it saves | Read |
|---|---|---|
| 1. RTK command proxy | 60-90% of command output | this file, `references/rtk-awareness.md` |
| 2. Efficient file/command ops | wasteful reads and dumps | `references/strategies.md` |
| 3. Model routing (hard rules) | Opus tokens on Sonnet/Haiku work | `references/model-routing.md` |
| 4. SoT keywords + hybrid memory | blind scanning and re-planning | `references/sot-framework.md`, `references/memory-system.md` |
| 5. Concise output | narration and filler | `references/output-style.md` |

## 1. RTK (Rust Token Killer)

Single Rust binary proxying dev CLI commands, compressing output with <10ms overhead. Prefix commands: `rtk git status`, `rtk cargo test`, `rtk npm install`, `rtk pytest`, `rtk docker ps`, `rtk kubectl ...`. Unknown subcommands pass through safely. `rtk proxy <cmd>` gives raw output. `rtk gain` shows savings.

- Verify FIRST, never reinstall blindly: `rtk --version && rtk gain` (if `rtk gain` fails you have the wrong rtk - Rust Type Kit is a different project).
- Install (only if missing): Windows - bundled `bin/rtk.exe`, add to PATH (`%USERPROFILE%\.claude\skills\token-efficiency\bin` when global); macOS - `brew install rtk`; Linux - `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh`. Avoid `cargo install` when GNU coreutils shadows MSVC link.exe (symptom: "link: extra operand"). Full guide: `references/install.md`.
- Claude Code hook (auto-rewrites commands): `rtk init -g`; verify `rtk init --show`. Bundled hook copy + tests: `scripts/rtk-rewrite.sh`, `scripts/test-rtk-rewrite.sh`, `scripts/check-installation.sh`. Details: `references/hooks-setup.md`.
- Full filter reference: run `rtk --help`, or see the rtk upstream docs (not vendored here - avoids shipping stale/un-localized copies). Quick start: `references/quick-start.md`.

## 2. Efficient file and command operations

Core rules (detail + cost math in `references/strategies.md`, `references/examples.md`): quiet flags by default; never read whole log files (tail/grep first); check lightweight sources (git status --short, package.json) before big files; grep instead of read; read with offset/limit after `wc -l`; bash transforms (cp, sed, cat) instead of Read+Write for non-code files - but Read+Edit for code so diffs stay reviewable; filter output (head, -maxdepth); summarize, don't dump. Learning/exploration patterns: `references/learning-mode.md`. Long-running analysis projects: `references/project-patterns.md`.

## 3. Model routing - hard rules

| Role | Model |
|---|---|
| Master Orchestrator (primary chat) | Opus latest (user's setting) |
| Coding Subagent Orchestrator | `claude-opus-4-6` - pinned, NOT latest |
| Coding Agents (repetitive codegen) | `claude-sonnet-4-6` - pinned, NOT latest |
| Logging and comments | `claude-haiku-4-5` - always |

These are cost-tier choices, not "latest" - verify each ID is still Active before a project bumps it. Override only when the user explicitly names a model. Ready-made agent definitions: `templates/agents/` (coder, orchestrator, logger) - copy to `.claude/agents/`. Detail: `references/model-routing.md`.

> ### How to actually pin a subagent (measured 2026-07-17, not assumed)
>
> **This section previously said "Pass model explicitly when spawning subagents." That instruction defeated its own pinning rule and is corrected here.**
>
> The Agent tool's `model:` parameter takes a **tier alias** (`sonnet`/`opus`/`haiku`), **not** a model ID. Passing it resolves to *latest of that tier* and **silently overrides** the pinned ID in the agent's frontmatter. Passing `model:` to "enforce" the pin is the one thing that breaks it.
>
> | Spawn | Runs as |
> |---|---|
> | `subagent_type: coder`, **no `model:`** | **`claude-sonnet-4-6`** - the frontmatter pin [OK] |
> | `subagent_type: coder`, `model: "sonnet"` | `claude-sonnet-5` - pin overridden [WARN] |
>
> **Rule: to pin, put the model ID in the agent definition's frontmatter (`model: claude-sonnet-4-6`) and pass NO `model:` argument.** Pass `model:` only for ad-hoc `general-purpose`/`Explore` agents that carry no frontmatter pin - there a tier alias is the only lever, and latest-of-tier is the honest expectation.
>
> **Verify, don't assume.** Config, `settings.json`, and frontmatter agreeing is *not* proof - none of them is the runtime. One probe (spawn with no `model:`, ask it to name its model, assert it matches the pin) settles it. Applies to this skill's own claims too.
>
> **Effort: default `high`, never `max`.** `max` is a deliberate per-task escalation the user asks for - never a default. A harness shipping `max` burns reasoning budget on mechanical work forever, silently.

## 4. SoT keywords + hybrid memory

Never blind-scan code or re-read log piles. Standardized `[SOT:CATEGORY:name]` tokens live in code comments and log headers; the README SoT index maps them; agents grep the tags then read only matched blocks. Categories seed at project init from the project goal; one-offs get `[SOT:IDX:name]`; promotion to category at frequency >= 5 (during checkpoints). Grammar + workflow: `references/sot-framework.md`. Index template: `templates/sot-readme-template.md`.

Memory is SQLite, not endless md files: `.agents/memory.db` (init: `sqlite3 .agents/memory.db < scripts/memory-init.sql`). Logs written by the logger agent (Haiku); recall is a query (`SELECT learnings FROM agent_compile_logs WHERE status='FAILURE'`), not a read. On user request "checkpoint": run `scripts/checkpoint.sh`, which mechanically folds log groups (n>1) into dense learnings rows and deletes the folded raw rows in one transaction; the agent then promotes keywords and appends verified "what worked" learnings to agent instructions. Detail: `references/memory-system.md`.

CLAUDE.md also carries an inline, glanceable learnings-block (`<!-- token-efficiency:learn:start -->...:end -->`), regenerated at checkpoint time and topic-grouped, each line tagged with its measured "~N tokens/session saved" - complements the SQLite query-based recall above rather than replacing it. Structure + regeneration: `references/memory-system.md`; marker block ships in `templates/CLAUDE-md-snippet.md`.

## 5. Concise output

Answer directly, minimum words. Never narrate actions - announce as `{tool {optimized args}}` (e.g. `{browser search {rust profilers 2026}}`), distilling the user's phrasing into the optimized request, then do the real work in the background; applies to all tools and outputs. Cite code as `file:line`, never re-explain context. Brevity governs narration/status/confirmations only - never substantive answers or error diagnoses. Content-type compression rules (what to compress vs. protect, when to use `rtk proxy` raw): `references/strategies.md`. Full output rules: `references/output-style.md`.

## Setup shortcut

For always-on enforcement (skills load on trigger; routing and output style should govern every turn), append `templates/CLAUDE-md-snippet.md` (~100 tokens) to `~/.claude/CLAUDE.md`.

Config-edit rollback hygiene (fenced managed blocks, timestamped backups, reversible uninstall) for any settings.json/CLAUDE.md edit this skill makes: `references/hooks-setup.md`.
