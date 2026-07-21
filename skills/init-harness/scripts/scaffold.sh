#!/usr/bin/env bash
# scaffold.sh - create the harness directory tree and copy the kit. DETERMINISTIC ONLY.
#
# DIVISION OF LABOUR (deliberate):
#   shell (this script) : structure - mkdir, copy, git init, sqlite init. No judgment.
#   agent               : content  - harness.config.json, agent prompts, commands, CLAUDE.md,
#                         context packs, .bld/*/phases.md, memory/INDEX.md.
#   existing scripts    : derivation - sync_harness.py, harness_status.py --write.
#
# Scaffolding ~40 directories through agent tool calls is ~40 round trips of pure ceremony
# for zero judgment. This is one call. The agent's tokens go to the parts that need thought.
#
# Usage: scaffold.sh <project-root> <skill-dir> [t1 t2 t3 t4 ...]
set -euo pipefail

ROOT="${1:?usage: scaffold.sh <project-root> <skill-dir> [terminals...]}"
SKILL="${2:?missing skill dir}"
shift 2
TERMINALS=("$@")
[ ${#TERMINALS[@]} -eq 0 ] && TERMINALS=(t1)

KIT="$SKILL/templates/kit"
DOCS="$SKILL/templates/docs"
[ -d "$KIT" ] || { echo "scaffold: kit not found at $KIT" >&2; exit 1; }

mkdir -p "$ROOT"
cd "$ROOT"

echo "=== structure ==="
mkdir -p harness \
         .claude/{agents,commands,hooks,output-style,logs} \
         .agents/logs \
         .skills \
         context/{agents,architecture,skills} \
         memory/{architecture,agents,skills,build,decisions,handoff/session} \
         architecture \
         .initialization \
         .github/workflows
for t in "${TERMINALS[@]}"; do mkdir -p ".bld/$t" "memory/handoff/$t"; done

echo "=== kit (verbatim - never hand-edited) ==="
cp "$KIT/harness/sync_harness.py"        harness/
cp "$KIT/harness/harness_status.py"      harness/
cp "$KIT/harness/build_master.py"        harness/
cp "$KIT/harness/verify_goal_packet.py"  harness/
cp "$KIT/harness/memory-schema.sql"      harness/
cp "$KIT/hooks/"*.py                 .claude/hooks/
cp "$KIT/ci/harness-check.yml"       .github/workflows/
cp "$KIT/memory/pivot-template.md"   memory/decisions/_pivot-template.md
[ -f harness/harness.config.json ] || cp "$KIT/harness.config.json" harness/harness.config.json
[ -f .claude/settings.json ]       || cp "$KIT/settings.claude.json" .claude/settings.json

echo "=== reference docs ==="
mkdir -p setup
cp "$DOCS/"*.md setup/ 2>/dev/null || true

echo "=== git ==="
[ -d .git ] || git init -q .
if [ -f "$KIT/gitignore.snippet" ]; then
  touch .gitignore
  grep -q "harness (append to project .gitignore)" .gitignore 2>/dev/null \
    || cat "$KIT/gitignore.snippet" >> .gitignore
fi

echo "=== worktree write-sandbox, one per terminal (C1/C3) ==="
# Each terminal tN gets its own git worktree on branch harness/tN under
# .claude/worktrees/tN/ - this becomes the DEFAULT write sandbox (spawn that terminal's
# agents with isolation: "worktree"). gate_guard.py is kept only for sensitivePaths +
# human-gated actions - see 05_hooks_and_logging.md "Worktree write-gate (C1/C3)".
# Guard: only if this is a real git repo AND a worktree isn't already there. A fresh `git
# init` has no commits yet, so `git worktree add` on a brand-new branch can fail (no HEAD
# to branch from) - that is expected pre-first-commit and is a clean skip, not a hard error.
mkdir -p .claude/worktrees
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  for t in "${TERMINALS[@]}"; do
    WT_DIR=".claude/worktrees/$t"
    BRANCH="harness/$t"
    if [ -d "$WT_DIR" ]; then
      echo "  $t: worktree already present at $WT_DIR - skipping"
      continue
    fi
    if git rev-parse --verify -q "$BRANCH" >/dev/null 2>&1; then
      git worktree add "$WT_DIR" "$BRANCH" >/dev/null 2>&1 \
        && echo "  $t: worktree added at $WT_DIR (branch $BRANCH)" \
        || echo "  $t: WARN - git worktree add failed for existing branch $BRANCH; skipping"
    else
      git worktree add -b "$BRANCH" "$WT_DIR" >/dev/null 2>&1 \
        && echo "  $t: worktree + branch created at $WT_DIR (branch $BRANCH)" \
        || echo "  $t: WARN - git worktree add -b failed (no commits yet? run after first commit); skipping"
    fi
  done
else
  echo "  WARN - not inside a git work tree; worktrees skipped (run again after 'git init' has a commit)"
fi

echo "=== agent memory shards, one per terminal (D1) ==="
# Vendored schema (templates/kit/harness/memory-schema.sql) - never reached into
# token-efficiency's $HOME install. One db per terminal: .agents/logs/tN.db. The derived
# .agents/master.db is built later by harness/build_master.py (also wired into
# harness_status.py), never here - scaffold only creates the shards.
mkdir -p .agents/logs
if command -v sqlite3 >/dev/null 2>&1; then
  for t in "${TERMINALS[@]}"; do
    SHARD=".agents/logs/$t.db"
    if [ -f "$SHARD" ]; then
      echo "  $t: $SHARD already exists - skipping"
    else
      sqlite3 "$SHARD" < "$KIT/harness/memory-schema.sql" && echo "  $t: $SHARD initialised"
    fi
  done
else
  echo "  SKIPPED: sqlite3 not on PATH - install globally (scoop install sqlite) and re-run"
  echo "           this step, or run: sqlite3 .agents/logs/tN.db < harness/memory-schema.sql"
fi

echo
echo "=== scaffold done. NOT yet a working harness. Next: ==="
echo " 1. agent writes harness/harness.config.json (toolchain.python = VERIFIED absolute path)"
echo " 2. agent writes .claude/agents/*.md, commands, CLAUDE.md, context packs, .bld/*/phases.md"
echo " 3. <python> harness/sync_harness.py          # generates .agents/, stamps models, emits indexes"
echo " 4. <python> harness/harness_status.py --write # Active Context + REALITY.md + master.db + recall"
echo " 5. <python> \$SKILL/scripts/verify_init.py    # PROVES the guards block"
