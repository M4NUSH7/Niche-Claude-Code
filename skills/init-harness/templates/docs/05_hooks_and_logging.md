# 05 - Hooks and Logging (hardened - implementations in `template/hooks/`)

Four hooks, all config-driven via `harness/harness.config.json`, all tested. Coursly's two
originals are superseded: the read guard was bypassable (any explicit `limit` skipped it) and the
logger opened SQLite on every tool call - both fixed here (audit #5, #8).

> ### [!] The interpreter is the whole ballgame - verify it, never assume it
>
> Audit #14 pinned `py -3` to dodge the Windows Store stub. **On a machine without the `py`
> launcher that command exits 127 - the hook process never starts.** It does not fail *open*; it
> fails **absent**: no block, no log row, no audit trail. Every guard below becomes decorative and
> **nothing reports it.** Bare `python` is no safer - it may resolve to an unrelated app's venv or
> to `WindowsApps\python.exe`, the Store stub itself.
>
> So: `config.toolchain.python` is an **absolute path** to a project-independent interpreter, and
> `sync_harness.py` **executes it before stamping** it into any hook command, exiting loudly if it
> can't. Install one globally - `uv python install 3.11` - never a venv, never in-folder.
> Rationale: `10_token_efficiency.md` Sec. 1.

## Wiring (stamped into settings by `sync_harness.py` from the config's `toolchain.python`)

| Event | Matcher | Script | Purpose |
|---|---|---|---|
| PreToolUse | `Read` | `big_read_guard.py` | Token discipline: no unbounded/oversized reads |
| PreToolUse | `Write\|Edit\|MultiEdit\|NotebookEdit` | `gate_guard.py` | Mechanical gates + `sensitivePaths`/human-gated actions (domain isolation is now the worktree's job - see C1 below) |
| PostToolUse | `.*` | `log_tool_use.py` | One JSONL append per tool use (fast path) |
| Stop | - | `fold_logs.py` | Fold JSONL -> per-agent SQLite (WAL) + heartbeat |
| SessionStart | - | `harness_status.py --brief` | Status/violation report + FAILURE-row recall (D1, see below) injected at session start |

Both config trees get **all** hooks (Coursly's `.agents/` was missing the read guard - that drift
class is eliminated because `.agents/` is generated, never hand-edited).

> ### [!] `sync_harness.py` OVERWRITES `hooks` in the project settings - it does not merge
>
> `sync_harness.py` assigns `settings["hooks"] = {...}` wholesale (not a deep merge). Every run
> rebuilds the block from the table above, so **any hand-added hook in
> `<project>/.claude/settings.json` is silently erased on the next sync** - no warning, no diff,
> the hook simply stops firing. If a project needs an extra hook, add it to the generator
> (`sync_harness.py`) or to `settings.claude.json`, never to the generated file. The rest of the
> settings tree *is* preserved (sync reads the existing file first and only replaces the fields it
> stamps) - `hooks` is the one that gets replaced outright.
>
> **Scope: this is the PROJECT tree only.** `ROOT` is derived from the script's own location, so
> sync writes `<project>/.claude/settings.json` and `<project>/.agents/settings.json`. It never
> reads or writes `~/.claude/settings.json`. User-tier hooks are structurally out of reach.
>
> ### Coexisting with user-tier hooks (they all fire - that is fine)
>
> Hooks from every settings tier **merge and all run**; they do not override each other the way
> `model` does. A user-tier hook (e.g. the token-efficiency skill's `rtk-rewrite.sh` on
> `PreToolUse`/`Bash`, or a doctrine injector on `SessionStart`/`SubagentStart`) fires *alongside*
> the harness hooks in every harness project. That is by design and costs nothing here - the
> matchers do not overlap:
>
> | Event | Harness (project tier) | Typical user tier |
> |---|---|---|
> | PreToolUse | `Read`, `Write\|Edit\|...` | `Bash` |
> | PostToolUse | `.*` | - |
> | Stop | - | - |
> | SessionStart | `harness_status.py --brief` | doctrine injector |
> | SubagentStart | - | doctrine injector |
>
> `SessionStart` is the only shared event: both fire, both inject, neither wins - two small
> context blocks, not a conflict. **Do not "fix" this by deleting one.** Before adding a harness
> hook on `PreToolUse`/`Bash`, check `~/.claude/settings.json` first: two independent rewriters on
> the same matcher WOULD conflict (each rewrites the other's output), and that is the one
> combination to avoid. If RTK rewriting is wanted, use the user-tier hook - do not reimplement it
> here.

## big_read_guard.py - hardened read guard

- Blocks `Read` of a file over `readGuard.maxLines` (default 500) when no `limit` is given.
- **Also blocks `limit > maxLines`** - the old guard trusted any explicit limit, so
  `limit: 999999` walked right past it. Windowed reads (`offset` + `limit <= maxLines`) pass.
- `readGuard.exempt` globs skip the guard (project context decides - e.g. `memory/INDEX.md`).
- Line counting stops at `maxLines + 1` (no full scan of huge files).
- **Every block and every fail-open is logged** to `{tree}/logs/hooks.jsonl` - bypass attempts
  and silent failures are visible to `harness_status.py`, which reports their counts.

## gate_guard.py - gates + sensitive paths, not general domain policing

Terminal identity from env `HARNESS_TERMINAL`. **PRIMARY job (C1/C3): `sensitivePaths` +
human-gated actions.** General cross-domain writes are now the git worktree's job by
construction (see "Worktree write-gate" below) - a terminal spawned with `isolation: "worktree"`
cannot reach another terminal's files at all, so policing that in the hook is redundant for any
terminal actually running under worktree isolation. The hook keeps three rules:

0. **Sensitive-path block (PRIMARY)** - writes into `sensitivePaths` globs (payments, ledger,
   auth, admin, identity) are always blocked, worktree or not. This is the one thing a worktree
   cannot express ("nobody, from anywhere, touches this path without review").
1. **Gate sequencing** - if any of the terminal's `blockedUntil` git tags is missing, writes are
   allowed **only** to `sharedWritePaths` (it can plan, document, and update its checklist  - 
   it cannot build). `neverBlocked: true` terminals skip this.
2. **Domain boundary (SECONDARY / advisory)** - writes into another terminal's `paths` are
   blocked with a redirect message ("hand off via `.bld/<owner>/phases.md`"). This rule now exists
   as a safety net for terminals not yet spawned under `isolation: "worktree"`, or for a Bash
   write that escaped a worktree by `cd`-ing out of it (see the limitation below) - it is not the
   primary isolation mechanism anymore. Writes to unclaimed paths are allowed but logged
   (`allow-unclaimed`) so the config can be tightened.

Fail-open behavior is explicit: no config or unknown terminal -> allow + log (configurable via
`gateGuard.failOpenWhenUnconfigured`), so the harness works mid-bootstrap without lying about it.

**Bash writes still bypass this hook entirely** (matcher is `Write|Edit|MultiEdit|NotebookEdit`,
not `Bash` - see "coexisting with user-tier hooks" above for why). That is precisely why the
worktree - a filesystem fact, not a hook - is the real isolation mechanism: it holds even when the
hook doesn't fire, as long as the process stays inside its own checkout.

## log_tool_use.py + fold_logs.py - two-stage audit logging

- **Hot path**: one `O_APPEND` JSONL line per tool use - no SQLite, no locks, crash-safe.
  Row: `{ts, level, agent, terminal, module, message, payload.result_summary(<=500 chars)}`.
- **Fold (Stop hook or manual)**: JSONL -> `{agent}.db` (`PRAGMA journal_mode=WAL`), same
  `logs(id, ts, level, agent, module, message, payload)` schema as the original harness, plus a
  **heartbeat row** per fold - a logger that stops logging is now detectable, and unparseable
  lines are preserved as `warn` rows instead of vanishing.
- Provenance split unchanged and automatic: `AGENT_NAME` env -> `.agents/logs/...` (autonomous),
  `CLAUDE_AGENT_NAME` -> `.claude/logs/...` (interactive), never mixed.

Query pattern:

```
sqlite3 .claude/logs/coder/coder.db "SELECT ts, message FROM logs ORDER BY ts DESC LIMIT 20"
```

## Log tree layout

```
{tree}/logs/hooks.jsonl            # guard blocks, fail-opens, unclaimed writes (gitignored)
{tree}/logs/{agent}/prompt.md      # GENERATED by sync_harness.py from the agent's .md (tracked)
{tree}/logs/{agent}/{agent}.jsonl  # hot-path buffer (gitignored, truncated by fold)
{tree}/logs/{agent}/{agent}.db     # folded audit trail, WAL (gitignored)
```

## Per-terminal memory shards + derived master.db (D1)

**Vendored, not reached-into.** The schema lives INSIDE init-harness at
`templates/kit/harness/memory-schema.sql` - the harness no longer inits its memory db from
token-efficiency's `$HOME`-installed copy. That removed a silent-skip dependency: previously,
`.agents/memory.db` only existed if the token-efficiency skill happened to be installed at
`~/.claude/skills/token-efficiency/...` on the machine running `scaffold.sh`. Vendoring the
schema makes the harness self-contained.

**Schema (flat, minimal - AUDIT D2):**

```sql
CREATE TABLE IF NOT EXISTS agent_log (
  ts TEXT, terminal TEXT, agent TEXT, tags TEXT, status TEXT, message TEXT
);
CREATE TABLE IF NOT EXISTS agent_compile_log (
  ts TEXT, terminal TEXT, agent TEXT, tags TEXT, status TEXT, learnings TEXT,
  replaced_log_count INTEGER
);
```

`agent_log` is the raw per-event row; `agent_compile_log` is the compiled/FAILURE ledger a
checkpoint writes into (one-level compression - see `10_token_efficiency.md` Sec. 4). Both tables
carry `terminal` because there are now N independent shards, one per terminal, and a query against
the derived master needs to know which terminal a row came from.

**Per-terminal shards.** `scaffold.sh` inits one db per terminal from the vendored schema:
`.agents/logs/t1.db`, `.agents/logs/t2.db`, ... (guarded on `sqlite3` being on PATH; skips with a
warning, not a hard failure, if it is absent - consistent with every other optional-tool guard in
this harness). Each terminal's own agents write into their own shard only - no cross-terminal
writer contention on a single db file.

**Derived master.db - never hand-written.** `templates/kit/harness/build_master.py` ATTACHes each
`.agents/logs/tN.db` in turn and `INSERT ... SELECT`s its rows into `.agents/master.db`. It is
**idempotent**: it truncates and rebuilds `master.db`'s tables from the shards every time it runs,
so master.db is always a pure derivation, never a second source of truth (same "generated, not
hand-maintained" rule as `REALITY.md` and the Active Context block). Run it either as a
`harness_status.py --write` step or standalone:

```bash
<python> harness/build_master.py             # rebuild .agents/master.db from all tN.db shards
<python> harness/harness_status.py --write    # also rebuilds master.db, then reports + recalls
```

**FAILURE recall - wired for real, not prose.** `harness_status.py` now runs (and its `--brief`
mode, the one stamped into the generated `SessionStart` hook, prints):

```python
def print_failure_recall(root, dbpath=".agents/master.db"):
    import os, sqlite3
    path = os.path.join(root, dbpath)
    if not os.path.exists(path):
        return  # skip cleanly - no shards built yet, or sqlite3 wasn't on PATH at scaffold time
    try:
        con = sqlite3.connect(path, timeout=5)
        rows = con.execute(
            "SELECT terminal, agent, tags, learnings FROM agent_compile_log "
            "WHERE status='FAILURE' ORDER BY ts DESC LIMIT 10"
        ).fetchall()
        con.close()
    except Exception:
        return  # table absent or db locked - skip cleanly, never crash SessionStart
    if rows:
        print("## Past failure learnings (do not retry these)")
        for terminal, agent, tags, learnings in rows:
            print(f"- [{terminal}/{agent} {tags}] {learnings}")
```

This is the actual function in `harness/harness_status.py` (not a sibling stub) - `--brief` calls
it after rebuilding `master.db` from the shards, so a fresh `SessionStart` genuinely sees prior
FAILURE rows instead of the recall being pure doctrine. Guard behavior is unchanged and
deliberate: **absent db or table is a clean skip, not an error** - a fresh project with no shards
built yet must still start a session normally. `verify_init.py` reports (does not hard-fail)
whether the shards and master.db exist and are queryable, and smoke-tests `build_master.py`'s
idempotency - see its D1 section.

**No longer PLANNED.** The full per-terminal `t{N}.db` + derived `master.db` design that was
deferred in the previous pass is implemented above. What remains genuinely open: `build_master.py`
does a full rebuild every call rather than an incremental append - fine at harness scale (shards
are small, rebuild is cheap), but if a project's logs grow very large, an incremental
`INSERT ... SELECT ... WHERE ts > last_synced` variant would be the next step. That is a
performance refinement, not a correctness gap - the current full-rebuild is provably idempotent
and correct at any size, just not maximally efficient at very large sizes.

## Worktree write-gate (C1/C3) - the DEFAULT sandbox

**The model.** Each terminal `tN` is not a policy fiction inside one shared working tree - it is
its own **git worktree**:

(a) `scaffold.sh` creates one worktree per terminal under `.claude/worktrees/tN/`, on a dedicated
    branch `harness/tN` (`git worktree add .claude/worktrees/tN harness/tN`, branch created first
    if it doesn't exist yet).
(b) When a terminal spawns agents, it spawns them with `isolation: "worktree"` (the Agent tool's
    worktree isolation), so an agent working for `tN` sees and can only write inside `tN`'s own
    tree. It cannot open, let alone write, another terminal's files - there is no path to them
    from that checkout.
(c) Changes return to the main line via an **explicit human/CI `git merge`** of `harness/tN` into
    the integration branch. Agents never merge and never tag (consistent with existing doctrine:
    principle #11, `git tag -d` is human-gated the same way) - a worktree makes it easy to
    *isolate* work, not to *promote* it, and promotion stays a deliberate, reviewed step.
(d) Worktree lifecycle is asymmetric on purpose: an **empty** worktree (no commits ahead of the
    branch point) is safe to auto-clean (`git worktree remove`) since nothing would be lost. A
    **changed** worktree (has commits, or dirty state) lingers until a human runs cleanup - the
    harness never silently discards work sitting in a terminal's tree.

**Honest limitation - this is why `gate_guard.py` still exists.** A worktree is a filesystem
boundary enforced by *checkout location*, not by the shell. A determined `Bash` command that does
`cd ../../main-tree && echo ... > file` (or an absolute path into the main tree, or a symlink)
escapes the worktree boundary entirely - nothing about `isolation: "worktree"` prevents a process
from `cd`-ing somewhere else and writing there. So the hook is **kept**, but its job shrinks: it
no longer tries to police general domain boundaries (the worktree does that structurally, for
anything that stays inside its own checkout) - it polices the two things a worktree genuinely
cannot: the small `sensitivePaths` glob set (secrets, payments, auth, admin, identity - see
`harness.config.json`'s `sensitivePaths`), and human-gated actions (`git tag -d`, force-push,
`.agents/` writes - see `settings.claude.json`'s deny list). Domain isolation is the worktree's
job now; `gate_guard.py`'s domain-glob check (Rule 1) is kept only as a **secondary/advisory**
check for terminals not yet re-spawned under `isolation: "worktree"`, or for the same-Bash-escape
case above where the hook is the only thing left standing.

**Say this in the generated `CLAUDE.md`:** *"Your write sandbox is your terminal's git worktree
(`.claude/worktrees/tN/`), not a hook. `gate_guard.py` only blocks `sensitivePaths` and
human-gated actions now - it is not your domain fence. Bash writes (`echo >`, `sed -i`, a script
that writes) are not intercepted by any hook; if you `cd` out of your worktree you can still touch
other files. Stay in your own worktree - that is the real boundary, not the hook."*

**What proves this (see `scripts/verify_init.py`):**

1. Each configured terminal has a worktree directory (`.claude/worktrees/tN/`) and its branch
   (`harness/tN`) exists - report-only if git or `git worktree` is unavailable in the verify
   environment (per the harness's "report the gap, don't design around it" doctrine).
2. `gate_guard.py` still blocks a write into a `sensitivePaths` glob, regardless of worktrees -
   this is the part no worktree structurally replaces.

**Still explicitly open, for whoever extends this next:**

- `harness_status.py`'s `git ls-files`-based REALITY.md generation reads one tree (today: the
  main checkout). It does not yet aggregate "what's sitting in each terminal's worktree, unmerged."
  A terminal's in-progress work is real but invisible to REALITY.md until it merges. Extending
  `harness_status.py` to shell `git -C .claude/worktrees/tN ls-files` per terminal and report both
  "merged reality" and "in-flight per-worktree reality" is a reasonable next step but out of scope
  here (it is additive to REALITY.md's format, not required to make worktrees the default sandbox).
- `07_phases_and_gates.md`'s gate-tag rules should state gate tags are created against the
  integration branch **after** a merge, not inside a terminal's own worktree branch - update that
  doc if gate semantics ever need per-worktree tagging.

## Design intent

- Discipline is **mechanical and unbypassable-by-default**; every exception is a logged event,
  not a silent hole.
- The hot path costs one process spawn + one append; all SQLite work happens once per session.
- **A hook that cannot start is worse than no hook** - it enforces nothing while looking wired up.
  Hence: absolute interpreter path, verified by execution at sync time (see the box above).

## Fail-open logging earns its keep

Every guard logs its own fail-opens to `{tree}/logs/hooks.jsonl`. That is not bookkeeping - it is
the only thing that makes a silent hole findable. During this rebuild a test appeared to show the
read guard allowing `limit: 9999` (i.e. audit #5 broken). The guard's own log said otherwise:

```json
{"action": "fail-open", "error": "stdin parse: Expecting value: line 1 column 1 (char 0)"}
```

The test harness wasn't delivering stdin; the guard was fine. Re-run correctly, all four cases
pass (block unbounded, block over-limit, allow windowed, honour exempt globs). **Trust the audit
trail over the assertion** - and check `hooks.jsonl` before believing a guard is broken.
