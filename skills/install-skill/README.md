# install-skill

**Install or build a COMPLETE skill package - start to end - never just a stray SKILL.md.**

## What it does

Handles the full lifecycle of getting a skill onto a Claude surface:

- **Surface targeting** - Claude Code (CLI + desktop Code tab) / Cowork / claude.ai chat. Only chat is script-limited; Code and Cowork both run bundled scripts, so most skills ship full content.
- **Acquisition** - `git clone --depth 1` the whole repo (never raw-fetch single files); copy the entire tree - references, scripts, hooks, binaries, templates.
- **The vendor-collision rule** - when a source ships an installer that rewrites `~/.claude`/`CLAUDE.md`/hooks, copy the content manually instead; never run a vendor installer that fights a harness that owns those files.
- **Adaptation** - per target: ASCII policy, English-only, Linux vs Windows shell, and (for chat only) dropping hooks/binaries/routing.
- **Verification** - `scripts/verify_skill.py` checks frontmatter, referenced-path existence, ASCII, script syntax, truncation, and a functional smoke (a bundled binary must complete its smallest real task, not just pass `--version`).
- **Packaging** - a `.skill` zip (the Cowork/claude.ai upload artifact) with exec bits preserved on `bin/*` and `*.sh`; or a staged folder + copy commands (the Code/CLI install unit).
- **From-scratch authoring** hands off to the `skill-creator` skill, then returns here for packaging and install.

## Why it works

The failure mode this skill exists to prevent: grabbing a SKILL.md, calling it installed, and leaving behind the references/scripts/hooks/binaries that make the skill actually work. Every fork in the process is an explicit choice with a recommended default - platform, scope, keep-or-drop - so nothing is silently dropped or ported. Verification is a fixed gate that proves behaviour (does the tool run?) rather than existence (is the file there?).

## How to use

Say "install this skill", "build a skill package", "repackage/update a skill", or "port a skill to Cowork". It asks target surface, source, and scope up front, then walks acquire -> select -> adapt -> audit -> verify -> deliver.

Verify or package a folder directly:

```bash
python scripts/verify_skill.py <skill-dir>            # gate
python scripts/verify_skill.py <skill-dir> --fix      # auto-fix unicode/newlines
python scripts/verify_skill.py <skill-dir> --package  # build <name>.skill
```

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The 7-step flow + the skill-creator handoff |
| `scripts/verify_skill.py` | The verification + packaging gate |
| `references/skill-anatomy.md` | Frontmatter spec, `allowed-tools`, progressive disclosure, always-on snippets |
| `references/platform-formats.md` | The three-surface capability matrix (Code / Cowork / chat) |
| `references/acquisition.md` | Clone/inventory/dependency-detect + the vendor-collision rule |
| `references/context-audit.md` | Density gate: prune/demote/consolidate without rewriting |
| `references/verification-checklist.md` | What the script cannot judge |
| `references/windows-install.md` | robocopy `/E` vs `/MIR`, PATH one-liners, protected `~/.claude` |

This repo was itself packaged and verified with this skill.
