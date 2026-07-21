# Acquisition procedure

## 1. Get the whole source

```bash
git clone --depth 1 <repo-url> /tmp/<name>     # ALWAYS the full repo
```

Never raw-fetch individual files - you cannot see what you are missing. Multiple repos: clone all before deciding anything.

## 2. Inventory

```bash
find /tmp/<name> -maxdepth 2 -type d | grep -v .git     # tree shape
for d in /tmp/<name>/skills/*/; do echo "-- $d"; ls "$d"; done   # per-skill contents
```

For each skill: SKILL.md plus what else? references/, scripts/, hooks/, evals/, assets/, bin/. Also check repo level: tools/ registries, shared assets, .claude-plugin manifests, hooks/ directories - these are part of "the full package" even when they sit outside skill folders.

Read the frontmatter descriptions (awk the description line) to build the relevance picture. Read repo README / INSTALL / CLAUDE.md for: name collisions with other projects, required env vars or API keys, minimum versions, init commands, platform support (e.g. which OS binaries exist).

Reality check both directions: verify folders assumed full are full (an evals/ containing only .gitkeep IS the complete package - do not hunt for ghosts), and that nothing referenced by a SKILL.md is missing from the tree (grep the SKILL.md for path references, check each exists).

## 3. Dependency detection

Grep the docs and scripts for signals that the skill needs more than files:

- Binary: install instructions, `--version` checks, releases pages, brew/cargo/npm install lines.
- Hook: settings.json, PreToolUse, hook registration.
- Environment: `API_TOKEN`, `API_KEY`, env var names in ALL_CAPS.
- Init: `<tool> init`, setup wizards.
- Runtime: python packages, node modules, sqlite3, jq.

Each detected dependency becomes: (a) bundled if it is a file and the platform supports it, (b) a documented user setup step with a verification command otherwise.

## 4. Copy and prove completeness

```bash
cp -r /tmp/<name>/skills/<skill> <staging>/skills/
diff -rq /tmp/<name>/skills/<skill> <staging>/skills/<skill>   # must be silent
```

`diff -rq` against source is the completeness proof - do not eyeball it.

## 5. Content issue scan

Before adaptation, scan for: emojis and decorative unicode, non-ASCII characters generally, non-English text (foreign-language README variants ride along in clones - exclude them), macOS-specific shell syntax, hardcoded paths. Report findings; fix per the user's MCQ choices.

## 6. Vendor-installer collision rule (acquire content, do not run the installer)

Many skill/framework repos ship an installer (`install.py`, `<tool> init -g`, a setup wizard) that rewrites `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, or hooks. If the destination is a project running a harness whose generator owns those same files (e.g. init-harness's `sync_harness.py`, which reassigns `settings["hooks"]` wholesale on every run), the vendor installer and the harness will fight over the same bytes - each silently erasing the other's edits.

Rule: when a source ships such an installer, **acquire the skill *content* manually** - copy the `skills/<name>/` directory (or harvest its rules into a reference doc) - and never run the vendor installer against a harness-owned `~/.claude`. Document any genuinely-needed global step (a PATH entry, a binary install) as an explicit user setup step with a verification command, so the user runs it knowingly rather than an installer doing it silently.

Detection: during step 3, if a dependency signal is an installer that writes outside the skill folder (`~/.claude`, `$HOME/.config`, global hook registration), flag it here and switch to manual content-copy for that source.
