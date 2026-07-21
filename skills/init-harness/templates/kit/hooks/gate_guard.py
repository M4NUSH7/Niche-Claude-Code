#!/usr/bin/env python3
"""PreToolUse hook (matcher: Write|Edit|MultiEdit|NotebookEdit) - gates + sensitive paths.

C1/C3 (see 05_hooks_and_logging.md "Worktree write-gate"): the DEFAULT write sandbox for a
terminal is now its own git worktree (.claude/worktrees/tN/ on branch harness/tN, spawned with
isolation: "worktree") - a terminal literally cannot reach another terminal's files from inside
its own checkout. That makes general domain-boundary policing by path-glob mostly redundant, so
this hook's PRIMARY job shrank to the two things a worktree genuinely cannot express:

  0. SENSITIVE PATHS (PRIMARY) - `sensitivePaths` globs (payments/ledger/auth/admin/identity,
     etc.) are blocked for everyone, worktree or not. Nobody touches these without review.
  1. GATE SEQUENCING (PRIMARY) - a terminal whose `blockedUntil` git tags don't all exist yet
     may write ONLY to sharedWritePaths (it can plan/document, not build). `neverBlocked: true`
     terminals skip this.
  2. DOMAIN BOUNDARY (SECONDARY / advisory - audit #2's original mechanism, kept as a safety
     net) - a terminal may only write inside its own `terminals[t].paths` plus the global
     `sharedWritePaths`. This still fires for terminals not yet spawned under
     isolation: "worktree", and it is the only backstop against a Bash write that `cd`-ed out of
     a worktree (see the note below - this hook's matcher does not cover Bash at all).

IMPORTANT - Bash writes bypass this hook entirely. The matcher is
Write|Edit|MultiEdit|NotebookEdit, never Bash (avoids fighting the token-efficiency skill's
user-tier RTK rewriter on the same matcher - see 05_hooks_and_logging.md "coexisting with
user-tier hooks"). A `Bash` command that does `echo ... > file`, `sed -i`, or `cd`s into another
terminal's worktree/the main tree is NOT intercepted here. This is exactly why the worktree
(a filesystem fact) is the real isolation mechanism and this hook is a secondary gate, not the
primary one: the worktree boundary holds even when this hook doesn't fire.

Terminal identity comes from env HARNESS_TERMINAL (set in each terminal's start prompt).
If config or env is missing and gateGuard.failOpenWhenUnconfigured is true (default), the hook
allows and logs - the harness stays usable mid-bootstrap, and every fail-open is auditable.
"""
import json
import os
import subprocess
import sys
import time
from fnmatch import fnmatch


def find_root():
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, ".claude")) or os.path.isfile(
            os.path.join(d, "harness", "harness.config.json")
        ):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.getcwd()
        d = parent


def load_cfg(root):
    try:
        with open(os.path.join(root, "harness", "harness.config.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def log_event(root, event):
    tree = ".agents" if os.environ.get("AGENT_NAME") else ".claude"
    try:
        path = os.path.join(root, tree, "logs", "hooks.jsonl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        event.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
        event.setdefault("hook", "gate_guard")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def tag_exists(root, tag):
    try:
        out = subprocess.run(
            ["git", "tag", "-l", tag], cwd=root, capture_output=True, text=True, timeout=10
        )
        return tag in out.stdout.split()
    except Exception:
        return False  # can't verify -> treat as not satisfied (safe direction)


def matches(rel, patterns):
    return any(fnmatch(rel, p) for p in patterns or [])


def block(root, reason, **extra):
    print(json.dumps({"decision": "block", "reason": reason}))
    log_event(root, {"action": "block", "reason": reason, **extra})
    return 1


def main():
    root = find_root()
    cfg = load_cfg(root)
    fail_open = True if cfg is None else cfg.get("gateGuard", {}).get("failOpenWhenUnconfigured", True)

    if cfg is None or not cfg.get("gateGuard", {}).get("enforce", True):
        if cfg is None:
            log_event(root, {"action": "fail-open", "why": "no harness.config.json"})
        return 0

    # Read tool_input once, up front: Rule 0 (sensitivePaths) applies UNCONDITIONALLY, even
    # before terminal identity is resolved - a missing/unknown HARNESS_TERMINAL must never be a
    # way to bypass the sensitive-path block. This is the one rule worktrees cannot replace, so
    # it is checked first and is not subject to fail-open-when-unconfigured.
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        log_event(root, {"action": "fail-open", "error": f"stdin parse: {e}"})
        return 0

    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path")
    if not path:
        return 0
    rel = os.path.relpath(path, root).replace("\\", "/") if os.path.isabs(path) else path.replace("\\", "/")

    sensitive = cfg.get("sensitivePaths", [])
    if matches(rel, sensitive):
        return block(
            root,
            f"{rel} matches a sensitivePaths glob (harness.config.json). This is blocked for "
            f"every terminal, worktree or not - sensitive paths are the one boundary a git "
            f"worktree cannot express. Route this change through human review.",
            path=rel, rule="sensitivePaths",
        )

    terminal = os.environ.get("HARNESS_TERMINAL")
    terminals = cfg.get("terminals", {})
    if not terminal or terminal not in terminals:
        log_event(root, {"action": "fail-open" if fail_open else "block",
                         "why": f"HARNESS_TERMINAL={terminal!r} not set/known"})
        if fail_open:
            return 0
        return block(root, f"HARNESS_TERMINAL={terminal!r} is not set or not in harness.config.json. "
                           "Set it in this terminal's start prompt/profile.")

    shared = cfg.get("sharedWritePaths", [])
    me = terminals[terminal]

    if matches(rel, shared):
        return 0  # memory/context/checklists/docs are always writable

    # Rule 1 (PRIMARY): my gates must exist before I build in my own domain.
    missing = [t for t in me.get("blockedUntil", []) if not tag_exists(root, t)]
    if missing and not me.get("neverBlocked", False):
        return block(
            root,
            f"{terminal} is gated: git tag(s) {missing} do not exist yet "
            f"(see harness.config.json gates). Until then you may only write to "
            f"sharedWritePaths (plan, document, update your checklist).",
            terminal=terminal, path=rel, missingTags=missing,
        )

    # Rule 2 (SECONDARY / advisory): stay inside my own domain. A terminal spawned with
    # isolation: "worktree" already cannot reach another terminal's files, so this rule is a
    # safety net - it still matters for terminals not yet worktree-isolated, and for a Bash
    # write that escaped its worktree (this hook's matcher never sees Bash, see module docstring).
    if matches(rel, me.get("paths", [])):
        return 0
    for other, spec in terminals.items():
        if other != terminal and matches(rel, spec.get("paths", [])):
            return block(
                root,
                f"{rel} belongs to {other}'s domain ({spec.get('domain', '?')}). "
                f"{terminal} owns: {me.get('paths')}. Hand this off via the {other} "
                f"checklist (.bld/{other}/phases.md) instead of writing it here.",
                terminal=terminal, path=rel, ownerTerminal=other,
            )

    # Unclaimed path: allow but record it - harness_status reports unclaimed writes.
    log_event(root, {"action": "allow-unclaimed", "terminal": terminal, "path": rel})
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        try:
            log_event(find_root(), {"action": "fail-open", "error": repr(e)})
        except Exception:
            pass
        sys.exit(0)
