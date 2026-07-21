#!/usr/bin/env python3
"""PostToolUse hook (matcher: .*) - fast JSONL audit logger.

Audit fix #8: the original spawned Python AND opened SQLite on every tool call.
This version only appends one line to a JSONL file (O_APPEND, crash-safe, no locks);
fold_logs.py compacts JSONL -> per-agent SQLite on the Stop hook / session end.

Identity + provenance:
  AGENT_NAME set        -> autonomous run  -> .agents/logs/{agent}/{agent}.jsonl
  CLAUDE_AGENT_NAME set -> interactive run -> .claude/logs/{agent}/{agent}.jsonl
  neither               -> .claude/logs/claude/claude.jsonl
Never mix the trees.
"""
import json
import os
import sys
import time


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


def main():
    root = find_root()
    if os.environ.get("AGENT_NAME"):
        tree, agent = ".agents", os.environ["AGENT_NAME"]
    else:
        tree, agent = ".claude", os.environ.get("CLAUDE_AGENT_NAME", "claude")

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    try:
        with open(os.path.join(root, "harness", "harness.config.json"), encoding="utf-8") as f:
            n_chars = int(json.load(f).get("logging", {}).get("resultSummaryChars", 500))
    except Exception:
        n_chars = 500

    tool = data.get("tool_name", "?")
    resp = data.get("tool_response")
    summary = (resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False, default=str))[:n_chars] if resp is not None else ""

    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "level": "info",
        "agent": agent,
        "terminal": os.environ.get("HARNESS_TERMINAL", ""),
        "module": tool,
        "message": f"tool_use:{tool}",
        "payload": {"result_summary": summary},
    }

    log_dir = os.path.join(root, tree, "logs", agent)
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"{agent}.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # logging must never break a session
