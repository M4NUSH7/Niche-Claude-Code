-- Hybrid memory schema. Init: sqlite3 .agents/memory.db < memory-init.sql
CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    agent TEXT NOT NULL,                -- writing agent name
    sot_tags TEXT NOT NULL,             -- comma-separated [SOT:...] tags
    status TEXT NOT NULL DEFAULT 'INFO',-- INFO | SUCCESS | FAILURE | PARTIAL
    message TEXT NOT NULL               -- written by claude-haiku-4-5
);
CREATE INDEX IF NOT EXISTS idx_logs_tags ON agent_logs(sot_tags);
CREATE INDEX IF NOT EXISTS idx_logs_status ON agent_logs(status);

CREATE TABLE IF NOT EXISTS agent_compile_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    agent TEXT NOT NULL,
    sot_tags TEXT NOT NULL,
    status TEXT NOT NULL,               -- SUCCESS | FAILURE | PARTIAL
    learnings TEXT NOT NULL,            -- dense: tried / worked / failed and why
    replaced_log_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_compile_status ON agent_compile_logs(status);
CREATE INDEX IF NOT EXISTS idx_compile_tags ON agent_compile_logs(sot_tags);

CREATE TABLE IF NOT EXISTS sot_keywords (
    keyword TEXT PRIMARY KEY,           -- e.g. AUTH, DB, IDX:retry-jitter
    category TEXT NOT NULL,             -- parent category or 'IDX'
    kind TEXT NOT NULL DEFAULT 'both',  -- code | logs | both
    description TEXT NOT NULL,
    frequency INTEGER NOT NULL DEFAULT 0
);
