# Verification checklist

Run `scripts/verify_skill.py <skill-dir>` first - it covers the mechanical items. This checklist is the full gate, including what the script cannot judge.

## Mechanical (scripted)

1. Frontmatter parses as YAML; `name` and `description` present; `name` matches the folder name.
2. Every path referenced in SKILL.md (references/, scripts/, templates/, bin/, modules/) exists on disk.
3. ASCII policy: no emojis or decorative unicode (unless user opted out).
4. Shell scripts pass `bash -n`; Python scripts compile; SQL schemas execute against a scratch db.
5. Truncation symptoms: every text file ends with a newline; SKILL.md's last section is intact (compare against intended content, not just syntax).
6. Package builds: .skill zip contains the full tree, correct top-level folder name.

## Judgment (manual)

7. Completeness vs source: `diff -rq` silent against the acquired tree for unmodified skills; modifications are intentional and listed.
8. Description quality: trigger phrases cover how THIS user talks; scoped away from sibling skills; platform edition stated if applicable.
9. Platform fit: matches the target surface. Code (CLI + desktop Code tab) and Cowork keep scripts/hooks-logic/binaries - stripping them is the failure there. Only a claude.ai-chat-only build drops hooks/binaries/model-routing; leaving those in a chat-only build is the failure. For Cowork, binaries must be Linux-compatible (a Windows `.exe` is a fail) and always-on rules must live in the skill body / account instructions, not a `~/.claude/CLAUDE.md` snippet. Nothing applicable to the target was dropped.
10. Pointers make sense: each reference doc is pointed to with when-to-read guidance; no orphan files nobody routes to (templates/agents referenced as a directory is fine).
11. Dependencies documented: every detected binary/hook/env/init has a setup step with a verification command in the handoff.
12. Collision check: destination has no stale same-name folder needing /MIR or removal; distinct names across CLI and desktop stores.
13. Version-sensitive facts (model IDs, tool flags) were verified by search, not recalled.

## After every change

Re-run the script, re-read the tail of any file written by file tools (`wc -l` + `tail -3`) - sync truncation is real and silent; rewrite via shell heredoc if a file comes back clipped. Rebuild the .skill package after ANY file change - a stale zip ships old bugs.
