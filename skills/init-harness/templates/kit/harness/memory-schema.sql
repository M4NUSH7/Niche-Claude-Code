-- memory-schema.sql - vendored inside init-harness (D1). Do NOT reach into
-- token-efficiency's $HOME-installed copy - this file is the single source used by
-- scaffold.sh to init each terminal's per-terminal shard: .agents/logs/tN.db
--
-- Flat schema per AUDIT D2. Two tables:
--   agent_log         - raw per-event row, one shard per terminal
--   agent_compile_log - compiled/FAILURE ledger a checkpoint writes into (one-level
--                       compression only - see 10_token_efficiency.md Sec. 4)
--
-- Both tables carry `terminal` so a query against the derived master.db (built by
-- build_master.py from all tN.db shards) can tell which terminal a row came from.

PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS agent_log (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  ts       TEXT NOT NULL,
  terminal TEXT NOT NULL,
  agent    TEXT NOT NULL,
  tags     TEXT,
  status   TEXT,
  message  TEXT
);
CREATE INDEX IF NOT EXISTS idx_agent_log_ts ON agent_log(ts);
CREATE INDEX IF NOT EXISTS idx_agent_log_status ON agent_log(status);

CREATE TABLE IF NOT EXISTS agent_compile_log (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  ts                  TEXT NOT NULL,
  terminal            TEXT NOT NULL,
  agent               TEXT NOT NULL,
  tags                TEXT,
  status              TEXT,
  learnings           TEXT,
  replaced_log_count  INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_agent_compile_log_ts ON agent_compile_log(ts);
CREATE INDEX IF NOT EXISTS idx_agent_compile_log_status ON agent_compile_log(status);
