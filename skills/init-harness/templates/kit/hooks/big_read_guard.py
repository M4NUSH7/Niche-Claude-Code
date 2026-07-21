#!/usr/bin/env python3
"""PreToolUse hook (matcher: Read) - hardened read guard.

Audit fix #5: an explicit `limit` no longer bypasses the guard (limit > maxLines is
blocked too), and every block AND every fail-open is logged to logs/hooks.jsonl so
bypass attempts and silent failures are visible.

Config: harness/harness.config.json -> readGuard { maxLines, exempt[] }.
Fail-open on any internal error (never brick the session), but always log it.
Exit 0 = allow, exit 1 + JSON decision on stdout = block.
"""
import json
import os
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
        return {}


def log_event(root, event):
    # Provenance split: autonomous runs (AGENT_NAME) log under .agents/, else .claude/
    tree = ".agents" if os.environ.get("AGENT_NAME") else ".claude"
    try:
        path = os.path.join(root, tree, "logs", "hooks.jsonl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        event.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
        event.setdefault("hook", "big_read_guard")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging must never cause a block or crash


def block(root, reason, **extra):
    print(json.dumps({"decision": "block", "reason": reason}))
    log_event(root, {"action": "block", "reason": reason, **extra})
    return 1


def main():
    root = find_root()
    cfg = load_cfg(root).get("readGuard", {})
    max_lines = int(cfg.get("maxLines", 500))
    exempt = cfg.get("exempt", [])

    try:
        data = json.load(sys.stdin)
    except Exception as e:
        log_event(root, {"action": "fail-open", "error": f"stdin parse: {e}"})
        return 0

    ti = data.get("tool_input") or {}
    path = ti.get("file_path")
    limit = ti.get("limit")
    if not path:
        return 0

    rel = os.path.relpath(path, root).replace("\\", "/") if os.path.isabs(path) else path.replace("\\", "/")
    if any(fnmatch(rel, pat) for pat in exempt):
        return 0

    # Audit fix #5: cap explicit limits instead of trusting them.
    if limit is not None:
        try:
            if int(limit) > max_lines:
                return block(
                    root,
                    f"limit={limit} exceeds readGuard.maxLines={max_lines}. "
                    f"Read in windows (offset + limit<={max_lines}) or use Grep.",
                    path=rel, limit=limit,
                )
        except (TypeError, ValueError):
            pass
        return 0  # bounded read within cap - allow

    # No limit given: count lines (stop as soon as the cap is exceeded).
    try:
        n = 0
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for n, _ in enumerate(f, 1):
                if n > max_lines:
                    break
        if n > max_lines:
            return block(
                root,
                f"{rel} exceeds {max_lines} lines. Use Grep to search it, "
                f"or Read with offset + limit<={max_lines}.",
                path=rel,
            )
    except OSError as e:
        # File missing/unreadable: let the Read tool surface its own error, but record it.
        log_event(root, {"action": "fail-open", "path": rel, "error": str(e)})
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # absolute fail-open backstop - but logged
        try:
            log_event(find_root(), {"action": "fail-open", "error": repr(e)})
        except Exception:
            pass
        sys.exit(0)
