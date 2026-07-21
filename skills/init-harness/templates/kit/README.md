# template/ - Drop-in Harness Kit (audit fixes implemented)

This folder is the **runnable implementation** of the audit fixes in `../09_AUDIT.md`. Copy it
into any project; every project-specific decision lives in **one file**  - 
`harness/harness.config.json` - and the scripts derive everything else from it. No value is
pinned twice.

## What's in the kit

```
template/
+-- harness.config.json        # THE single source of truth (copy to <repo>/harness/)
+-- harness/
|   +-- sync_harness.py        # generates .agents/ from .claude/, stamps models, emits indexes
|   \-- harness_status.py      # cross-checks checkboxes vs git tags vs disk; writes status blocks
+-- hooks/
|   +-- big_read_guard.py      # hardened read guard (caps explicit limits, logs bypass attempts)
|   +-- gate_guard.py          # mechanical gate + domain-boundary enforcement on writes
|   +-- log_tool_use.py        # fast JSONL audit logger (no per-call SQLite)
|   \-- fold_logs.py           # folds JSONL -> per-agent SQLite (WAL) on Stop/session end
+-- ci/harness-check.yml       # CI: drift check + status check + secret scan
+-- settings.claude.json       # .claude/settings.json shape with full hook wiring
\-- gitignore.snippet          # .obsidian noise, logs, env files
```

## Install into a new project (10 minutes)

1. Copy `harness.config.json` -> `<repo>/harness/harness.config.json` and edit it (see field
   guide below). **This is the only editing step that requires thought.**
2. Copy `harness/*.py` -> `<repo>/harness/`, `hooks/*.py` -> `<repo>/.claude/hooks/`.
3. Copy `settings.claude.json` -> `<repo>/.claude/settings.json`; author your agent/command/skill
   `.md` files under `.claude/` and `.skills/` (see `../03` and `../04` for the prompts).
4. Run `py -3 harness/sync_harness.py` - this **generates** `.agents/` (never hand-edit it),
   stamps model IDs everywhere, and emits `context/skills/index.md`, `memory/skills/index.md`,
   and `logs/{agent}/prompt.md` stubs.
5. Run `py -3 harness/harness_status.py --write` to seed `memory/INDEX.md`'s Active Context
   block and `context/architecture/REALITY.md`.
6. Copy `ci/harness-check.yml` -> `.github/workflows/`, append `gitignore.snippet` to `.gitignore`.
7. Commit. Open T1 with its start prompt. Done.

## How "project context decides" - the config field guide

| Field | What the project decides through it |
|---|---|
| `project` | Name stamped into generated files |
| `python` | Interpreter used in ALL hook commands (audit #14 - Windows: `py -3`; Linux/mac: `python3`; venv: absolute path) |
| `models` | Role -> concrete model ID, defined ONCE (audit #6). Upgrade a model = edit one line, run sync |
| `agents` | Which named agents exist, their role + effort ceiling. Rename `domain-reviewer` to whatever your domain needs (design-reviewer, data-reviewer, backtest-reviewer...) |
| `maxEffort` | The hard ceiling; agents never self-escalate past it |
| `terminals` | How many parallel terminals, what each **owns** (`paths` globs), what each **waits for** (`blockedUntil` gate tags), what each **controls** (`ownsGates`), and which one is `neverBlocked` |
| `gates` | The full gate registry: tag name -> owner + meaning. Gates are **git tags**; `gate_guard.py` + `harness_status.py` enforce/verify them (audit #2) |
| `sensitivePaths` | Globs that auto-escalate review + require the security skill before merge |
| `sharedWritePaths` | Paths every terminal may write (memory, context, checklists, docs) |
| `docRouting` | Topic -> architecture doc **by filename** (audit #10 - no more "doc 03" numbering). Agent prompts should reference this map, not hardcode paths |
| `readGuard` | `maxLines` threshold + `exempt` globs the guard skips |
| `gateGuard.enforce` | Turn mechanical gate enforcement on/off; `failOpenWhenUnconfigured` lets the harness work before config/env is complete (every fail-open is logged) |
| `logging` | JSONL-first logging knobs (audit #8) |
| `skills` | The skill registry, defined ONCE - sync emits both index files from it (audit #12) |

## The three invariants the kit enforces mechanically

1. **`.agents/` is generated, never edited** (audit #1). `sync_harness.py --check` fails CI on
   drift. The declared differences (env var name, `logging{}` block, path rewrites) are applied
   by the script - both trees get BOTH hooks (fixes the missing read guard in Coursly's `.agents/`).
2. **Gates are checked, not trusted** (audit #2, #7). `gate_guard.py` blocks writes to a
   terminal's domain until its `blockedUntil` tags exist and blocks writes to *other* terminals'
   domains; `harness_status.py` reconciles checkboxes <-> tags <-> disk on every session start and
   regenerates the Active Context block so status can't go stale by hand.
3. **Reality is generated** (audit #3). `context/architecture/REALITY.md` comes from
   `git ls-files`, refreshed by `harness_status.py --write`; architecture docs must carry a
   `status: target | current` header line, and the status script warns on docs missing it.

## Per-terminal environment

Each terminal's start prompt (or shell profile) sets:

```
set HARNESS_TERMINAL=t2        # which terminal this session is
set CLAUDE_AGENT_NAME=coder    # which agent identity logs attribute to
```

Autonomous runners set `AGENT_NAME` instead of `CLAUDE_AGENT_NAME`; the scripts detect which
tree (`.claude`/`.agents`) to log under from that.

## Credentials rule (audit #4)

Nothing under `context/`, `memory/`, `.bld/`, or `.env.example` may contain a literal secret or
sandbox credential - reference **env var names only**; values live in gitignored `.env.local`,
signup URLs live in `.initialization/02_accounts_and_services.md`. The CI workflow runs gitleaks
to make this mechanical.
