#!/usr/bin/env python3
"""Stop / SessionEnd hook (and manually runnable) - fold JSONL audit logs into SQLite.

Audit fix #8, second half: SQLite work happens once per session, not once per tool call.
For every {tree}/logs/{agent}/{agent}.jsonl:
  - insert rows into {agent}.db  (schema-compatible with the original harness:
    logs(id, ts, level, agent, module, message, payload) + index on ts)
  - PRAGMA journal_mode=WAL
  - write a heartbeat row, so a silent logger is detectable (audit: hook crash was invisible)
  - truncate the JSONL after a successful commit

Run manually anytime:  py -3 .claude/hooks/fold_logs.py
"""
import glob
import json
import os
import sqlite3
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


SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, level TEXT, agent TEXT, module TEXT, message TEXT, payload TEXT
);
CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts);
"""


HOOKS_LOG_MAX_BYTES = 2_000_000  # ~2 MB, then rotate once (keep .1, drop older)


def rotate_hooks_log(path, max_bytes=HOOKS_LOG_MAX_BYTES):
    """Rotate {tree}/logs/hooks.jsonl once it exceeds max_bytes.

    The original shipped a comment promising this and never did it, so the guard-event log
    (blocks, fail-opens, unclaimed writes) grew unbounded. Single-generation rotation: the
    recent past is worth keeping, the distant past isn't - harness_status.py only ever reports
    counts since the last run.
    """
    try:
        if os.path.exists(path) and os.path.getsize(path) > max_bytes:
            bak = path + ".1"
            if os.path.exists(bak):
                os.remove(bak)
            os.replace(path, bak)
    except OSError:
        pass  # rotation must never break a session


def fold_file(jsonl_path):
    agent_dir = os.path.dirname(jsonl_path)
    agent = os.path.basename(agent_dir)
    db_path = os.path.join(agent_dir, f"{agent}.db")

    rows = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                rows.append((
                    r.get("ts"), r.get("level", "info"), r.get("agent", agent),
                    r.get("module", ""), r.get("message", ""),
                    json.dumps(r.get("payload", {}), ensure_ascii=False),
                ))
            except json.JSONDecodeError:
                rows.append((time.strftime("%Y-%m-%dT%H:%M:%S"), "warn", agent,
                             "fold_logs", "unparseable_line", json.dumps({"raw": line[:200]})))

    con = sqlite3.connect(db_path, timeout=15)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
        if rows:
            con.executemany("INSERT INTO logs (ts, level, agent, module, message, payload) "
                            "VALUES (?, ?, ?, ?, ?, ?)", rows)
        con.execute(
            "INSERT INTO logs (ts, level, agent, module, message, payload) VALUES (?, ?, ?, ?, ?, ?)",
            (time.strftime("%Y-%m-%dT%H:%M:%S"), "info", agent, "fold_logs",
             "heartbeat", json.dumps({"folded": len(rows)})),
        )
        con.commit()
    finally:
        con.close()

    open(jsonl_path, "w").close()  # truncate only after successful commit
    return len(rows)


def main():
    root = find_root()
    total = 0
    # N4 note (documented asymmetry, not a bug): this glob only matches per-agent JSONL under
    # {tree}/logs/{agent}/{agent}.jsonl. {tree}/logs/hooks.jsonl (guard blocks/fail-opens/
    # unclaimed writes) lives one level up and is NEVER folded into a .db - it is only rotated
    # (see rotate_hooks_log below). That is deliberate: hooks.jsonl is a flat append-only guard
    # audit trail read directly by harness_status.py, not per-agent working logs meant for
    # SQLite query/compression. If a future pass wants it queryable too, fold it into its own
    # hooks.db here rather than assuming this loop already covers it.
    for tree in (".claude", ".agents"):
        for jsonl_path in glob.glob(os.path.join(root, tree, "logs", "*", "*.jsonl")):
            try:
                total += fold_file(jsonl_path)
            except Exception as e:
                print(f"fold_logs: skipped {jsonl_path}: {e}", file=sys.stderr)
    for tree in (".claude", ".agents"):
        rotate_hooks_log(os.path.join(root, tree, "logs", "hooks.jsonl"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
