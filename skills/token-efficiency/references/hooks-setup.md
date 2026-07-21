# Claude Code Hooks

> Bundled hook scripts live in `scripts/`: `scripts/rtk-rewrite.sh` (the hook), `scripts/test-rtk-rewrite.sh` (test suite), `scripts/check-installation.sh` (install verification). See `SKILL.md` for the overview.

## Specifics

- Shell-based `PreToolUse` hook -- requires `jq` for JSON parsing
- Returns `updatedInput` JSON for transparent command rewrite (agent doesn't know RTK is involved)
- Exits silently (exit 0) on any failure: jq missing, rtk missing, rtk too old (< 0.23.0), no match
- Version guard checks `rtk --version` against minimum 0.23.0
- `rtk-awareness.md` is a slim 10-line instructions file embedded into CLAUDE.md by `rtk init`

## Testing

```bash
# Run the full test suite (60+ assertions)
bash scripts/test-rtk-rewrite.sh

# Test against a specific hook path
HOOK=/path/to/rtk-rewrite.sh bash scripts/test-rtk-rewrite.sh

# Enable audit logging during testing
RTK_HOOK_AUDIT=1 RTK_AUDIT_DIR=/tmp bash scripts/test-rtk-rewrite.sh
```

## Config-edit rollback hygiene

Any edit this skill makes to a shared config file - `settings.json`, `CLAUDE.md`, `.claude/agents/*.md` - follows the same three-part discipline so an install is always reversible and never silently clobbers a user's existing content:

1. **Fenced managed blocks.** Everything this skill writes into a file it does not own outright goes inside a marker pair naming the skill and the block's purpose:

   ```
   # >>> token-efficiency:hook >>>
   ... managed content (e.g. the PreToolUse hook entry) ...
   # <<< token-efficiency:hook <<<
   ```

   Use the comment syntax native to the file (`#` for shell/JSON-with-comments configs is illustrative; `<!-- -->` for markdown, as the learnings-block in `memory-system.md` already does). A re-run of setup finds the marker pair and replaces only what is between the markers - it never appends a duplicate pair and never touches content outside them. Each distinct managed section gets its own marker pair (e.g. `token-efficiency:hook` vs `token-efficiency:learn`) so sections can be added, updated, or removed independently.

2. **Timestamped backup before any edit.** Before writing to a config file for the first time in a session, copy it: `cp settings.json settings.json.bak.$(date +%Y%m%dT%H%M%S)` (or the Windows equivalent, `Copy-Item settings.json "settings.json.bak.$(Get-Date -Format yyyyMMddTHHmmss)"`). Keep the most recent backup at minimum; do not silently overwrite an existing backup from the same run. This is cheap insurance against a bad merge or a hook edit that breaks JSON parsing.

3. **Reversible uninstall.** Removing the skill's config footprint means deleting exactly the content between each of its marker pairs (and the markers themselves) and leaving everything else in the file untouched - never a blind restore-from-backup as the primary path (the file may have changed since), but the backup remains available as a manual fallback if the marker-based removal is not enough (e.g. the file was hand-edited inside the markers and no longer round-trips cleanly).

This pattern is plain text/JSON manipulation - no special tooling required, works identically on Windows/macOS/Linux.
