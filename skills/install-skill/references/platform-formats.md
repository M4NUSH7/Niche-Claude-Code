# Platform formats and adaptation rules

Ask the platform question FIRST - it determines everything below.

## Three surfaces, not two - the key distinction

"Desktop" is not one target. There are THREE runtime surfaces, and only ONE of them is script-limited:

- **Claude Code** (the CLI, and the desktop app's Code tab) - real machine shell, filesystem, subagents. Runs bundled scripts/hooks/binaries. Loads skills from `~/.claude/skills/<name>/` (personal) or `<project>/.claude/skills/<name>/`.
- **Cowork** (the desktop app's agentic workspace, interactive or scheduled) - has a shell, filesystem, and subagents, and DOES run bundled scripts. Its only real differences from Code are (a) it does NOT read `~/.claude/skills/` on your machine - it loads the skills enabled for your claude.ai account (synced at session start; manage via Desktop -> Customize -> Skills, or in a repo's `.claude/skills/`), and (b) its sandbox is a Linux environment, so platform-specific shell/binaries must be Linux-compatible.
- **claude.ai chat** (the plain web/desktop messaging surface - NOT Code, NOT Cowork) - the constrained one. Skills load as instructions; whether it executes bundled scripts is not documented/guaranteed. Treat it as "SKILL.md guidance may apply, but do not rely on scripts/hooks/binaries running here."

The old advice "drop scripts/hooks/binaries for desktop" was really about **claude.ai chat**, and was wrong for Cowork and the desktop Code tab - both run scripts.

## Capability matrix

| Capability | Claude Code (CLI + desktop Code tab) | Cowork | claude.ai chat |
|---|---|---|---|
| Runs bundled `scripts/` | Yes | Yes | Not guaranteed - do not rely on it |
| Hooks (PreToolUse, settings.json) | Yes | Partial - session-level, no `~/.claude` machine hooks; keep hook logic out of the account-synced skill | No |
| Model routing / pinned model IDs | Yes (`claude-sonnet-4-6` etc. in agent templates) | Session models are account-driven; do not build per-agent routing around them | No |
| Binaries (bin/) | Yes - persistent, PATH-able, OS-native | Yes, but Linux sandbox - a Windows `.exe` is useless; ship a Linux build or install-on-first-run | No |
| Install / load path | folder in `~/.claude/skills/` or `<project>/.claude/skills/` | account-enabled skills (Desktop -> Customize) OR repo `.claude/skills/`; does NOT read `~/.claude/` | uploaded via Customize / "Upload skill" |
| Install artifact | plain FOLDER (no `.skill`) | `.skill` zip (upload) or repo folder | `.skill` zip (upload) |
| Always-on config | `~/.claude/CLAUDE.md` snippet | account/project instructions (no machine CLAUDE.md) | profile preferences / project instructions |
| sqlite3 CLI | machine-dependent - verify with `sqlite3 --version`, fall back to python3 | Linux sandbox - prefer `python3` sqlite3 module | n/a |
| Shell | user's machine (Windows/macOS/Linux - detect!) | Linux sandbox, each call may be independent (absolute paths, no assumed cwd/env carryover) | n/a |
| Persistence | full filesystem | connected folder / repo; sandbox resets per session | n/a |
| Subagents | Yes, with pinned models | Yes (account models); no browser/display | No |

## The `.skill` package vs the folder

Same content, different distribution channel - NOT a capability difference:

- **Folder** = the install unit for **Claude Code (CLI + desktop Code tab)**. Copy `<skill>/` into `~/.claude/skills/`. No `.skill` file involved.
- **`.skill` zip** = the upload unit for **Cowork and claude.ai** (the "Save skill" / "Upload skill" button; syncs to the account). Because Cowork runs scripts, the `.skill` should carry the SAME content as the CLI folder - do NOT strip scripts/binaries out of a `.skill` destined for Cowork.

So `verify_skill.py --package` zipping the full CLI folder into `<name>.skill` is CORRECT for a Cowork/claude.ai upload. The only time you slim is a claude.ai-chat-only target (below).

## Adaptation matrix - by target, not by "desktop"

**Target = Claude Code (CLI or desktop Code tab):** ship the full folder. Nothing dropped. Detect the user's real OS for shell/binary correctness. This is the default.

**Target = Cowork:** ship the full content as a `.skill` (or a repo `.claude/skills/` folder). Adjust only for the Linux sandbox and account-loading:
1. Binaries: provide a Linux build, or an install-on-first-run step - a Windows `.exe` won't run.
2. Shell: assume Linux; each bash call may be independent (absolute paths, no exported env carryover); convert macOS `sed -i ''` -> Linux `sed -i`.
3. Machine hooks / `~/.claude/CLAUDE.md` snippets: these don't apply (Cowork doesn't read `~/.claude`) - move always-on rules into the skill body or account/project instructions instead of a machine-CLAUDE.md snippet.
4. Do NOT drop scripts - Cowork runs them.
5. Name collision: account skills AND (in Code) `~/.claude/skills` can both surface - use a distinct name if the same skill exists in both stores.

**Target = claude.ai chat only (the genuinely limited surface):** derive a slimmed variant by DROPPING what can't run:
1. Drop: hooks/hook scripts, binaries/bin/, model routing (no alias substitute), machine CLAUDE.md snippets, anything needing script execution or persistence.
2. Keep: the SKILL.md guidance and references that are useful as pure instructions.
3. Convert any remaining machine calls to documented manual steps.
4. Re-scope the description: state it is the chat edition and that the Code/Cowork version covers the dropped capabilities.
5. Result is dramatically smaller - if it isn't, something that can't run in chat was left in.

## Adaptation: chat/desktop -> CLI

Rare, but: keep everything (a chat/desktop skill's content is a subset of what Code supports), fix Linux-sandbox assumptions (detect the user's actual OS), and consider what Code-only power (hooks, native binaries, always-on `~/.claude` snippets) the skill would benefit from - as MCQ suggestions, not silent additions.

## Multi-surface builds

Build the full Code folder first (it is the superset). For Cowork, package that same content as a `.skill` (only Linux/account adjustments, no stripping). Only produce a slimmed variant when the explicit target is **claude.ai chat**, and give it a distinct name. Never maintain two divergent full versions - the chat variant is a derivation of the full one.
