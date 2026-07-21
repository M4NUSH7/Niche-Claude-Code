#!/usr/bin/env python3
"""build_master.py - rebuild .agents/master.db from the per-terminal shards (D1).

master.db is DERIVED, never hand-written: read-only for recall, exactly like REALITY.md and the
Active Context block are derived rather than hand-maintained (same "generated, not a second
bookkeeping system" rule as harness_status.py). This script is idempotent - every run drops and
rebuilds master.db's two tables from whatever .agents/logs/tN.db shards currently exist, so it is
always safe to re-run and never accumulates duplicate rows across repeated calls.

Wiring: called from harness_status.py's --write path (and --brief, before the FAILURE recall
query, so a fresh SessionStart sees current data) - see 05_hooks_and_logging.md "Per-terminal
memory shards + derived master.db (D1)". Also runnable standalone:

  <python> harness/build_master.py [project-root]

Guarded: if no shards exist yet (fresh project, sqlite3 unavailable at scaffold time), this is a
clean no-op, not an error.
"""
import glob
import os
import sqlite3
import sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, terminal TEXT, agent TEXT, tags TEXT, status TEXT, message TEXT
);
CREATE TABLE IF NOT EXISTS agent_compile_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT, terminal TEXT, agent TEXT, tags TEXT, status TEXT, learnings TEXT,
  replaced_log_count INTEGER DEFAULT 0
);
"""


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


def shard_paths(root):
    return sorted(glob.glob(os.path.join(root, ".agents", "logs", "t*.db")))


def build(root, quiet=False):
    """Rebuild master.db from all tN.db shards. Returns (n_shards, n_agent_log, n_compile_log)."""
    shards = shard_paths(root)
    master_path = os.path.join(root, ".agents", "master.db")
    os.makedirs(os.path.dirname(master_path), exist_ok=True)

    # isolation_level=None (autocommit): ATTACH/DETACH must not straddle an implicit
    # transaction the sqlite3 module would otherwise open around each execute() - that is what
    # produced "database shard is locked" on DETACH even after an explicit commit().
    con = sqlite3.connect(master_path, timeout=15, isolation_level=None)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
        # Idempotent: clear and re-derive every run rather than appending, so master.db can
        # never drift from "exactly what the shards currently say."
        con.execute("DELETE FROM agent_log")
        con.execute("DELETE FROM agent_compile_log")

        n_log, n_compile = 0, 0
        for shard in shards:
            try:
                con.execute("ATTACH DATABASE ? AS shard", (shard,))
            except sqlite3.OperationalError as e:
                if not quiet:
                    print(f"build_master: skipped {shard}: {e}", file=sys.stderr)
                continue
            try:
                cur = con.cursor()
                cur.execute("SELECT name FROM shard.sqlite_master WHERE type='table'")
                tables = {r[0] for r in cur.fetchall()}
                cur.close()
                if "agent_log" in tables:
                    cur = con.cursor()
                    cur.execute(
                        "INSERT INTO agent_log (ts, terminal, agent, tags, status, message) "
                        "SELECT ts, terminal, agent, tags, status, message FROM shard.agent_log"
                    )
                    n_log += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
                    cur.close()
                if "agent_compile_log" in tables:
                    cur = con.cursor()
                    cur.execute(
                        "INSERT INTO agent_compile_log "
                        "(ts, terminal, agent, tags, status, learnings, replaced_log_count) "
                        "SELECT ts, terminal, agent, tags, status, learnings, replaced_log_count "
                        "FROM shard.agent_compile_log"
                    )
                    n_compile += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
                    cur.close()
                con.commit()  # flush before DETACH - an uncommitted write can hold the shard locked
            finally:
                con.execute("DETACH DATABASE shard")
        con.commit()
    finally:
        con.close()
    return len(shards), n_log, n_compile


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else find_root()
    n_shards, n_log, n_compile = build(root)
    print(f"build_master: rebuilt .agents/master.db from {n_shards} shard(s) "
          f"({n_log} agent_log row(s), {n_compile} agent_compile_log row(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
