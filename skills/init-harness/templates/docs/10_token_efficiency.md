# 10 - Token Efficiency (the two pillars the harness was missing)

status: current

The harness already implements three of the `token-efficiency` skill's five pillars:

| Pillar | Where it already lives |
|---|---|
| 2. Efficient file/command ops | `hooks/big_read_guard.py` - mechanical, not a plea |
| 3. Model routing | `harness.config.json models{}` -> `thinker`/`workhorse`/`utility` |
| 5. Concise output | `.claude/output-style/default.md` |

This doc adds the two that need infrastructure: **RTK** and **SoT + hybrid memory**.

---

## 1. Toolchain: global installs, pinned by absolute path

**Rule:** tools the harness *shells out to* install to the **global/user toolchain** - scoop on
Windows, `uv python install` for Python. Never vendored into the project folder, never a foreign
venv, never a bare name that PATH may resolve somewhere surprising.

This is not style. It is the fix for the worst bug found in the original template:

> The template pinned `py -3` for every hook (audit #14's fix for the Windows Store stub). On a
> machine with no `py` launcher that command **exits 127 - the hook process never starts.** It
> does not fail *open*; it fails **absent**: no block, no log row, no audit trail. The guards
> become decorative and nothing reports it. Meanwhile bare `python` resolved to an unrelated
> app's venv, and `WindowsApps\python.exe` was the Store stub itself.

So: `harness.config.json -> toolchain{}` records the **absolute path** of every tool the harness
invokes, and `sync_harness.py` **executes the interpreter before stamping it** into any hook
command, exiting loudly if it can't.

```jsonc
"toolchain": {
  "python":  "C:/Users/<you>/AppData/Roaming/uv/python/cpython-3.11.15-.../python.exe",
  "git":     "git",        // scoop shim
  "sqlite3": "sqlite3",    // scoop shim
  "rtk":     "rtk"         // scoop shim
}
```

Install what's missing globally - never in-folder:

```bash
uv python install 3.11        # standalone CPython, not a venv
scoop install git sqlite rtk  # global shims on PATH
```

Project *libraries* (pnpm/cargo/uv deps) are unaffected - this governs harness tooling only.

---

## 2. RTK - the command-output proxy (pillar 1)

RTK proxies dev CLI output and compresses it 60-90% with <10ms overhead. Unknown subcommands pass
through safely.

```bash
rtk git status      rtk cargo test     rtk pytest
rtk npm install     rtk docker ps      rtk proxy <cmd>   # raw output
rtk gain            # savings so far
```

**Verify first, never reinstall blindly:**

```bash
rtk --version && rtk gain
```

If `rtk gain` errors, you have the wrong `rtk` - Rust Type Kit is a different project.

This project will run `cargo`/`pytest`/`git` constantly, which is exactly RTK's hot path. Put it
in the coder agent's conventions and in `CLAUDE.md`, not just here - a tool nobody is told to use
saves nothing.

---

## 3. SoT keywords - grep the map, don't scan the tree (pillar 4a)

Standardized tokens in code comments and log headers, so agents **grep tags before reading**:

```
[SOT:CATEGORY]           category marker
[SOT:CATEGORY:name]      named block
[SOT:IDX:name]           one-off (frequency < 5)
```

Always inside a host-language comment: `# [SOT:DATA:ingest-validate]`, `// [SOT:SIGNAL:zscore]`.

**Seeded categories for this project** (`config.sot.categories`):

| Category | Covers |
|---|---|
| `DATA` | providers, pipeline, validation, storage |
| `FEATURE` | feature engineering |
| `SIGNAL` | signal construction |
| `BACKTEST` | CPCV, DSR, protocol |
| `RISK` | sizing, portfolio risk |
| `HARNESS` | LLM routes, safeguards |
| `CONTRACT` | schemas, artifact contracts |

Workflow: read the README SoT index -> `rtk grep -rn "\[SOT:SIGNAL" --include=*.py` -> read only
the matched blocks with offset/limit. **Never blind-scan a tree when a grep answers it.**
One-offs get `[SOT:IDX:name]`; promote to a category at frequency >= 5 during a checkpoint.

---

## 4. Hybrid memory - vault + per-terminal shards + derived master, one boundary (pillar 4b)

The skill says *"endless .md files do not scale as agent memory."* True - for **working logs**.
It is not true for curated decisions, and `09_AUDIT.md` explicitly lists the Obsidian vault under
"keep, don't improve." So we run both, with a hard boundary - and the db side is itself split
into per-terminal shards plus one derived master (D1, see `05_hooks_and_logging.md`'s
"Per-terminal memory shards + derived master.db"):

| | `memory/` (Obsidian vault) | `.agents/logs/tN.db` (shard, per terminal) | `.agents/master.db` (derived) |
|---|---|---|---|
| Holds | decisions, pivot narratives, architecture rationale | that terminal's raw agent_log + compiled agent_compile_log rows | union of all shards - read-only recall surface |
| Written by | humans (+ agents on approval) | that terminal's own agents/logger | nobody directly - `harness/build_master.py` rebuilds it from the shards |
| Read by | humans; agents on explicit reference | that terminal, for its own history | any session, **as a query** (FAILURE recall) |
| Recall | wikilinks / backlinks | - | `WHERE status='FAILURE'` |
| Authority | **single source of long-term truth** (principle #4) | source shard - authoritative for that terminal | derived; rebuild any time, never hand-edited |

**One boundary, never two sources for the same fact.** The vault says *why*; the shards say *what
happened, mechanically*, per terminal; the master is a pure derivation of the shards, exactly like
`REALITY.md` is a pure derivation of `git ls-files` - never a second place facts get written by
hand. A pivot writes to both the vault and a shard - narrative to the vault, warning to the
terminal's `agent_compile_log` (see `11_pivots.md`).

Schema is vendored **inside init-harness** (`templates/kit/harness/memory-schema.sql`) - it does
NOT reach into token-efficiency's `$HOME`-installed copy, removing a silent-skip dependency where
the db only existed if that skill happened to be installed on the machine running `scaffold.sh`.

Init (done by `scaffold.sh`, one shard per configured terminal):

```bash
mkdir -p .agents/logs
sqlite3 .agents/logs/t1.db < harness/memory-schema.sql
sqlite3 .agents/logs/t2.db < harness/memory-schema.sql
# ... one per terminal in harness.config.json's terminals{}
```

Derive the master (idempotent - safe to re-run any time):

```bash
<python> harness/build_master.py    # ATTACHes every .agents/logs/tN.db, rebuilds .agents/master.db
```

### Checkpoints - one level, never recursive

On request: compress `agent_log` groups (within a terminal's own shard) into dense
`agent_compile_log` rows, delete the raw rows compressed (`replaced_log_count` records how many),
promote `[SOT:IDX:*]` at frequency >= 5, and append verified "what worked" learnings to agent
definitions as one-liners. `checkpoint.sh` (from the `token-efficiency` skill, if installed) does
the deterministic parts of the compression itself, against that terminal's shard.

**FAILURE recall is wired for real, not left as doctrine.** `harness/harness_status.py` rebuilds
`.agents/master.db` from the shards and then runs `SELECT terminal, agent, tags, learnings FROM
agent_compile_log WHERE status='FAILURE' ORDER BY ts DESC LIMIT 10` against it, printing the
result - this happens on every `--brief` call, which is exactly what the generated `SessionStart`
hook invokes. See `05_hooks_and_logging.md` Sec. "Per-terminal memory shards + derived master.db
(D1)" for the actual function. A fresh terminal now sees "do not retry this" automatically; it
does not need to remember to grep the vault.

The `learnings` bar: **"must be useful to an agent that has never seen the raw logs."**

> **Do NOT build recursive compression.** Compression is one-way and one-level:
> `agent_logs -> agent_compile_logs -> STOP`. Compiling compile-rows is lossy twice, and the second
> pass has no fresh evidence to check itself against - you'd be summarizing summaries, which is how
> *"LSTMs overfit on 2019 data"* decays into *"we tried some models."* For a pivot record that is
> total loss of the thing you kept it for. Growth is not a real concern: compile rows are
> **indexed**, so recall is a `WHERE` clause, not a full read. If it ever genuinely bloats,
> **archive old rows out - do not re-compress them.** The audit trail is the point.

---

## 5. Vault writing conventions (vendored, not installed)

Audited `kepano/obsidian-skills` against `install-skill`: five format-syntax references, no
scripts, and **no decision-record or supersession pattern at all**. Installing the useful one
would cost ~1,400 tokens on the harness's most frequent write path ("writing any memory note"),
violating the lazy-load rule (`01` Sec. 3) for ~70% payload we don't use. **So we vendored the
conventions instead** - these ~15 lines are the whole benefit:

| Convention | Why it matters here |
|---|---|
| `[[Note]]`, `[[Note#Heading]]`, `[[Note#^block-id]]` | Block links let a pivot cite the **exact** superseded line, not a whole file |
| Frontmatter **link type**: `supersedes: "[[Other]]"` (quoted) | Lineage is a queryable property **and auto-generates a backlink** - the old note learns it was superseded without being edited. Principle #4 working for you. |
| Typed properties: `date`, `list`, `text`, `checkbox` | `date: 2026-05-02` sorts/filters natively; `salvaged: [ipc, cfg]` is a real list |
| `aliases: [informal-name]` | Reach a note by its informal name without forking a duplicate stub |
| Nested tags: `decision/pivot`, `decision/locked` | Hierarchy without moving files - wikilinks never break |
| `cssclasses:` | The only legit `.obsidian/` interaction: per-note, lives in the note, not in machine-churning `workspace.json` (audit #11 safe) |

**Rejected - `obsidian-bases`.** A hand-authored `.base` file gives a filterable "current
decisions" table that *looks* generated (filters, formulas) but is static YAML that drifts
silently. That is audit #7's forbidden second bookkeeping system in disguise. Status blocks are
**generated** by `harness_status.py --write`, never hand-maintained.

**Rejected - `obsidian-cli`.** Requires the Obsidian GUI running, targets the "most recently
focused vault" (ambient, machine-local, non-deterministic), and can run arbitrary JS outside the
hook audit trail - breaking the provenance split (`01` Sec. 5).
