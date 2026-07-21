# Hybrid Memory System (SQLite + SoT grep)

Endless .md files do not scale as agent memory - recall degrades into reading everything. Memory lives in one SQLite database per project, queried instead of read. Applies to projects of any size.

## Setup

```bash
mkdir -p .agents && sqlite3 .agents/memory.db < <path-to-skill>/scripts/memory-init.sql
```

Schema (`scripts/memory-init.sql`):

- `agent_logs(id, ts, agent, sot_tags, status, message)` - working log rows. Written by the logger role (`claude-haiku-4-5`), never by Sonnet/Opus.
- `agent_compile_logs(id, ts, agent, sot_tags, status, learnings, replaced_log_count)` - dense checkpoints that replace raw logs.
- `sot_keywords(keyword, category, kind, description, frequency)` - the keyword index (mirrored to the README for humans). **OPTIONAL/deprecated-by-default:** this table is kept in the schema (some harness scaffolds reference `memory-init.sql` as-is), but it is only worth populating if writes to it become a byproduct of an existing mechanical step - e.g. the logger's insert does `INSERT OR IGNORE INTO sot_keywords (...) VALUES (...)` then `UPDATE sot_keywords SET frequency = frequency + 1 WHERE keyword = ...` in the same statement batch as the log write, inside a hook. Populated by hand-ritual (an agent remembering to update it) it drifts silently from day one - prefer the flat category enum + README index (`sot-framework.md`) as the source of truth and treat `sot_keywords`/`IDX:` promotion as a nice-to-have, not required.

## Hybrid search

Structured recall is a query, not a read:

```bash
sqlite3 .agents/memory.db "SELECT learnings FROM agent_compile_logs WHERE status='FAILURE'"   # what went wrong before
sqlite3 .agents/memory.db "SELECT message FROM agent_logs WHERE sot_tags LIKE '%AUTH%' ORDER BY ts DESC LIMIT 10"
```

Code recall is an SoT grep (sot-framework.md). The README index is the shared map between both. That is the hybrid: SQL for history, grep for code, one keyword vocabulary across them.

## Checkpoints (context compression)

Run when the user asks to checkpoint: `bash scripts/checkpoint.sh [path-to-memory.db]` (add `-n` for a dry run that only prints the fold plan). The script is the **sole executable writer** for the mechanical part of compression - it does not just print advisory SQL:

1. Groups `agent_logs` by `(sot_tags, status)` - the failure-signature/task key - keeping only groups with `COUNT(*) > 1` (a singleton is not "compression").
2. Inserts one `agent_compile_logs` row per qualifying group, in the same transaction as step 3, with a mechanical `learnings` summary (count + time span) and `replaced_log_count` set to the folded count.
3. Deletes the folded raw rows in that same transaction, then asserts every new row has `replaced_log_count > 1` (exits non-zero if not). The checkpoint IS the memory; keeping both defeats compression.
4. Reports (advisory only, not auto-applied): `[SOT:IDX:*]` keywords at frequency >= 5, and the most recent FAILURE learnings.

What the script does **not** do mechanically - left to the checkpoint agent: rewriting the mechanical `learnings` text into denser prose ("what was tried, what worked, what failed and why") where the terse summary is not enough for a future agent to act on; promoting listed IDX keywords to real categories (updates `sot_keywords` + README index); appending verified "worked" learnings to `.claude/agents/` definitions.

## Agent learnings

During compression, things that WORKED update the standing instructions - append to the relevant agent definition in `.claude/agents/` (or project CLAUDE.md) as a one-line rule, e.g. "pnpm test needs NODE_OPTIONS=--max-old-space-size=4096 in this repo". Things that FAILED are recorded in `learnings` so no future agent retries them. Instructions grow by verified experience, not speculation; keep additions to one line each and prune contradicted ones at the next checkpoint.

## CLAUDE.md learnings-block (inline glanceable surface)

The SQLite tables above are the queryable memory; they are not glanceable - a human (or a fresh agent skimming CLAUDE.md before it thinks to query) sees nothing. A second, complementary surface fixes that: a stable-marked block inside CLAUDE.md, regenerated at checkpoint time from the same distilled learnings, topic-grouped, human-readable, pure markdown (no tooling needed to read it).

**Markers** (exact, stable across regenerations so re-running the checkpoint step can find-and-replace the block instead of appending duplicates):

```
<!-- token-efficiency:learn:start -->
<!-- token-efficiency:learn:end -->
```

**Structure** - one topic heading per SoT category or recurring failure signature, each line a single verified learning with its measured savings tag (see below):

```markdown
<!-- token-efficiency:learn:start -->
## Token efficiency - learned this session

### AUTH
- Skip re-reading `auth/session.rs` after the first grep hit; the token refresh path never changed across 6 checkpoints. (~800 tokens/session saved)

### BUILD
- `pnpm test` needs `NODE_OPTIONS=--max-old-space-size=4096` in this repo, or it OOMs after ~40 files. (~1200 tokens/session saved - avoids one full failed run + re-read)

### DB
- Migration files under `db/migrations/` are append-only; never re-read the whole directory, `ls -t db/migrations | head -3` is enough. (~300 tokens/session saved)
<!-- token-efficiency:learn:end -->
```

**Regeneration at checkpoint**: `scripts/checkpoint.sh` folds raw `agent_logs` into `agent_compile_logs` (dense learnings) as described above; it does not touch CLAUDE.md. The checkpoint *agent* (not the script) is responsible for the CLAUDE.md side: after the mechanical fold, pull the newest verified "worked" learnings (the same ones being appended to `.claude/agents/` definitions), group them by SoT category/topic, and replace the content between the two markers in CLAUDE.md - find the start/end marker pair, discard whatever is between them, write the new topic-grouped block in its place. Never append a second marker pair; never hand-edit between the markers outside a checkpoint (the next regeneration overwrites it).

This block **complements**, it does not replace, the SQLite query-based recall: the DB is the source of truth for full history and is what a future agent should query for anything not summarized here; the CLAUDE.md block is a lossy, human-readable digest of only the highest-value, verified learnings, meant to be read (by a human or by an agent's initial context load), not queried.

## Measured savings attribution

Tag each learning/rule with its measured impact instead of a vague range: `(~N tokens/session saved)` or, when there's a clearer unit, `(~N tokens/call saved)` or `(avoids one full failed run)`. The number should come from an actual before/after comparison for that specific rule (e.g. tokens in a full mis-run vs. tokens once the rule prevents it) - a rough order-of-magnitude estimate is fine, a made-up number is not. If a learning has never been measured, write `(savings not yet measured)` rather than inventing a figure; fill it in once observed. This keeps the CLAUDE.md learnings-block and `.claude/agents/` rule additions honest and lets a checkpoint prioritize which learnings are worth keeping when the block grows long.
