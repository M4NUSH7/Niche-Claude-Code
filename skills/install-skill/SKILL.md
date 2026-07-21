---
name: install-skill
description: "End-to-end skill package installer and builder for Claude. Handles the FULL process: platform targeting (CLI / CLI+Desktop / Desktop), acquiring complete packages from GitHub repos or local folders (never just SKILL.md - all references, scripts, hooks, binaries, templates), relevance selection, personalization, platform adaptation, verification, packaging (.skill zips, staged folders), and install commands. Use this skill whenever the user wants to install a skill, install a skill package, add a skill from a repo or URL, build a skill package, port a skill between CLI and desktop, combine skills, or repackage/update an installed skill. Also use when the user complains a previous install only grabbed SKILL.md."
---

# Install Skill

Installs or builds complete skill packages, start to end. The failure mode this skill exists to prevent: grabbing a SKILL.md, calling it installed, and leaving behind the references, scripts, hooks, and binaries that make the skill actually work.

Never make a packaging or personalization decision silently: every fork in the process is an AskUserQuestion multiple-choice with a "(Recommended)" option derived from context.

## Step 1 - Intake (MCQ, before ANY work)

Ask, in one round:

1. **Target surface** - `Claude Code (CLI + desktop Code tab)` / `Cowork` / `claude.ai chat only`. This is question one because it determines packaging format and what (if anything) must be dropped. Note: Code and Cowork BOTH run bundled scripts - only claude.ai chat is script-limited (see `references/platform-formats.md` BEFORE asking, so the recommendation is informed). Most skills target Code and/or Cowork and ship full content; only a chat-only target gets slimmed. A skill for Code + Cowork ships the same content two ways: the folder (Code) and a `.skill` upload (Cowork).
2. **Source** - GitHub repo URL(s) / local folder / build from scratch. From-scratch authoring is done by the `skill-creator` skill; this skill then packages and installs its output (handoff protocol below).
3. **Scope** - install everything found vs. only what is relevant to a stated purpose.

### Step 1a - Build-from-scratch handoff to skill-creator (only when Source = build from scratch)

`skill-creator` authors the skill; this skill packages and installs it. The two are complementary halves - skill-creator owns draft -> test -> eval -> optimize-description -> `package_skill.py`; install-skill owns platform adaptation, verification, and the CLI/desktop install. Wire them explicitly:

1. **Check availability, install if missing.** `skill-creator` ships as a marketplace plugin and may be *catalogued but not installed* (`~/.claude/plugins/installed_plugins.json` lists only active plugins). If the `skill-creator` skill is not available this session, tell the user it must be enabled first (install the `skill-creator` plugin from the `claude-plugins-official` marketplace, or copy `plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/` per the manual-content rule in `references/acquisition.md` step 6). Do not silently proceed - a from-scratch build with no authoring skill produces nothing.
2. **Invoke skill-creator** to author the skill: interview -> draft SKILL.md -> (optionally) evals + iterate -> optimize the description. Pass it the intent captured in Step 1. Its deliverable is a **staged skill folder** on disk (its `package_skill.py` can also emit a `.skill`, but this flow wants the folder).
3. **Return here at Step 2** treating that staged folder as a *local source*: acquire/inventory it (Step 2), select/personalize (Step 3), adapt per platform (Step 4) - **including adding an `allowed-tools` line scoped to the tools the new skill's steps actually call, and a CLAUDE-md snippet under templates/ if its rules must govern every turn** (see `references/skill-anatomy.md`) - then context-audit (Step 5), verify (Step 6), and deliver/install (Step 7).

Net: skill-creator produces the folder; install-skill makes it tight, correct, and installed.

## Step 2 - Acquire and inventory

- `git clone --depth 1` the FULL repo (never raw-fetch single files). Local sources: copy whole tree.
- Inventory: every skill directory and its complete contents (references/, scripts/, hooks/, evals/, assets/, bin/, tools/ registries), plus repo-level README / INSTALL / CLAUDE.md for gotchas (name collisions, required env vars, minimum versions, init commands).
- Detect dependencies beyond files: binaries to install, hooks to register, PATH changes, `init` commands, external API keys. List them - they become setup steps in the handoff.
- Detect content issues: emojis/unicode, non-English text, platform-specific syntax (macOS `sed -i ''` vs Linux). Full procedure: `references/acquisition.md`.

## Step 3 - Select and personalize (MCQ)

- If scope is purpose-filtered: present the inventory with per-skill one-line descriptions and a recommended subset. Skills other skills depend on (context/registry files) ride along with their dependents.
- Ask personalization in the same round where possible: emoji/ASCII policy, naming (slash command = frontmatter `name`; distinct names per platform when both stores can surface in one session), and any user rules to merge in (append as new sections or reference docs - never scattered edits).

## Step 4 - Adapt per platform

Rules in `references/platform-formats.md`. Summary - there are THREE surfaces, and only ONE is script-limited: **Claude Code** (CLI + the desktop app's Code tab) and **Cowork** both run bundled scripts, hooks logic, and binaries; only plain **claude.ai chat** is limited. So: CLI/Code gets everything (full folder in `~/.claude/skills/`). Cowork gets the SAME content packaged as a `.skill` (Cowork runs scripts - only adjust for its Linux sandbox and the fact it loads account-enabled skills, NOT `~/.claude/`; do not strip scripts). Only for a **claude.ai-chat-only** target do you DROP hooks/binaries/model-routing and slim to instruction-only pillars, as a separately named variant. The `.skill` zip is the upload artifact for Cowork/claude.ai; the plain folder is the Code/CLI install unit - same content, different channel.

If adaptation raises a judgment call (keep-or-drop a borderline component, rename, merge two sources), that is an MCQ with a recommendation - not a silent choice.

Anatomy standards for anything built or restructured (frontmatter spec, pushy descriptions, progressive disclosure, modules/ nesting, templates/): `references/skill-anatomy.md`.

## Step 5 - Context audit and prune (density gate)

The package ships only what it needs, as dense as possible - WITHOUT rewriting any content. Cost model and full rules: `references/context-audit.md`. Run `scripts/verify_skill.py <dir> --audit`, then resolve every finding by MCQ (delete / demote to references / keep, with recommendations): prune upstream repo meta, non-English variants, empty placeholders, and true orphans; consolidate duplicated content to one canonical location (move verbatim, fix pointers); demote situational content from SKILL.md to references. HARD RULE: content is moved or deleted, never rewritten, paraphrased, or summarized - unless the user explicitly requests a rewrite. Scripts, binaries, and templates are never loaded into context - their size is free; do not prune them for density.

## Step 6 - Verify (fixed gate, never skipped)

Run `scripts/verify_skill.py <skill-dir>` - checks frontmatter, referenced-path existence, ASCII policy, script syntax, truncation symptoms (files not ending in newline), and can auto-fix mechanical items (`--fix` for unicode replacement) and build the package (`--package`). Content decisions are never auto-fixed - they were settled by MCQ in Step 3/4. Manual checklist for what the script cannot judge: `references/verification-checklist.md`. CRITICAL learned behavior: after any large file write, re-read the tail (`wc -l` + `tail`) - file sync can silently truncate; if it does, rewrite via shell heredoc.

**Functional smoke - a bundled binary/tool must WORK, not just exist.** Syntax-valid and present-on-PATH is not "works": `cargo typify --help` once passed while panicking on every real schema, and `<tool> --version` passing says nothing about whether the tool does its job. For any skill that bundles or depends on a binary/toolchain (rtk, lizard, a formatter, a codegen tool), run a **one-shot functional smoke**: feed the smallest real input and assert non-error, task-shaped output - e.g. `rtk git status` returns compressed output (not just `rtk --version`); `lizard` run on one tiny file emits a metrics row. A skill whose tool can't complete its smallest real task is not verified, regardless of `--version`.

## Step 7 - Deliver and install

- **CLI:** stage the final folder in the working directory, then hand the user exact copy commands - `~/.claude` is protected from agent writes, the user runs the one-liner. Windows commands, robocopy /E-vs-/MIR semantics, PATH one-liners: `references/windows-install.md`.
- **Desktop:** zip as `<name>.skill` and present the file - the Save skill button installs it to the user's profile.
- Hand over dependency setup steps (binary installs, `init` commands) with verification commands for each.
- Warn about collisions (old versions in the destination, same-name skills across stores). Updates to an existing install: mirror-copy (/MIR), not merge.
- Offer a test run of the installed skill.

## Repackaging an installed skill

Same flow, short-circuited: acquire = copy the installed folder to the working directory (installed locations may be read-only); adapt/personalize per MCQ; verify; re-deliver. Rename = folder + frontmatter `name` + rebuilt package, atomically - never one without the others.
