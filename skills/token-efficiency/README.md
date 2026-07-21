# token-efficiency

**Cut token cost across every dev turn without losing quality.**

## What it does

Five pillars, each engaging only when the project condition calls for it:

1. **RTK command-output compression** - a bundled Rust binary (`bin/rtk.exe` on Windows) that proxies dev CLI commands (`git`, `cargo`, `npm`, `pytest`, `docker`, `kubectl`) and compresses their output 60-90% with <10ms overhead. Prefix a command with `rtk` (or install the auto-rewrite hook) and the log the agent reads shrinks dramatically.
2. **Efficient file/command ops** - grep before read, `offset`/`limit` after `wc -l`, quiet flags, summarize-don't-dump. The "read only what you need" discipline.
3. **Model routing** - hard rules so expensive models think, cheap models type, cheapest models log. Pins are full model IDs in agent frontmatter; a bare tier alias (`sonnet`) silently overrides a pin to latest, so you pin the ID and pass **no** `model:` at spawn.
4. **SoT keywords + hybrid memory** - `[SOT:CATEGORY:name]` tags in code + a README index so the agent greps the tag and reads only matched blocks; SQLite agent memory where recall is a `WHERE status='FAILURE'` query, not a re-read of the log pile.
5. **Concise output** - the output contract: lead with the outcome, no action narration, no recap of what a tool just printed, cite `file:line`. Never compresses error diagnoses, caveats, or code.

## Why it works

Output tokens cost the same as input tokens and the user reads them all. The biggest, cheapest win is **not generating** narration and **not re-reading** what a query can answer. RTK attacks the single largest input source (verbose command output); the output contract attacks the largest output source (narration). Model routing stops burning Opus tokens on work Sonnet/Haiku do fine. Together they compound.

## How to use

- **Always-on rules:** append `templates/CLAUDE-md-snippet.md` (~100 tokens) to `~/.claude/CLAUDE.md`. This keeps routing + the output contract in context every turn; the full skill body loads on trigger.
- **RTK:** verify first (`rtk --version && rtk gain`); install only if missing (Windows uses the bundled `bin/rtk.exe`).
- The skill fires on dev CLI commands, subagent spawns, logging, or when you mention `rtk`, `token efficiency`, `model routing`, `checkpoint`, `agent memory`, or `source of truth`.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The five pillars + how to actually pin a subagent |
| `bin/rtk.exe` | Bundled RTK binary (Windows). Cowork/Linux uses the `-cowork` edition's Linux build. |
| `references/model-routing.md` | The routing table + the pin-vs-alias mechanism |
| `references/output-style.md` | The full output contract, incl. the tool-call-batch rubric |
| `references/strategies.md` | Efficient file/command ops, content-type compression rules |
| `references/memory-system.md` | SQLite memory, checkpoints, the CLAUDE.md learnings-block |
| `references/sot-framework.md` | The `[SOT:...]` tagging grammar |
| `scripts/checkpoint.sh` | Mechanical log-compression (folds N failure rows -> 1, deletes folded raw) |
| `templates/CLAUDE-md-snippet.md` | The always-on block to append to CLAUDE.md |
| `templates/agents/*.md` | Ready-made coder/orchestrator/logger agent definitions |

## Cowork note

This edition ships the **Windows** rtk binary. For Cowork (Linux sandbox), use `cowork/token-efficiency-cowork.skill`, which bundles a Linux `rtk` ELF instead.
