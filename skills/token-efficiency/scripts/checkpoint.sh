#!/usr/bin/env bash
# Checkpoint: sole executable writer for the mechanical compression fold.
#
# What it folds mechanically (no LLM step required for this part):
#   - Groups agent_logs by (sot_tags, status) - the failure-signature/task key.
#   - Only groups with COUNT(*) > 1 are folded (a singleton row is not "compression").
#   - Each qualifying group becomes exactly one agent_compile_logs row with
#     learnings = a factual, mechanical summary (message count + first/last ts).
#     This is deliberately terse and NOT a substitute for an agent writing real
#     prose "what worked / what failed and why" learnings - see memory-system.md.
#     An agent may UPDATE a compiled row's `learnings` column afterward with
#     denser hand-authored prose; the mechanical text is a safe minimum, not
#     the ceiling.
#   - The folded raw rows are DELETED in the SAME transaction as the insert
#     (the GROUP BY ... HAVING COUNT(*) > 1 filter is identical in both
#     statements, so what gets summarized is exactly what gets deleted).
#   - Every new agent_compile_logs row is asserted replaced_log_count > 1
#     right after commit; the script exits non-zero (without further changes)
#     if any row fails that - sqlite3's RAISE() only works inside triggers,
#     so this assertion is a shell-level check, not an in-transaction one.
#
# What is NOT done here (left to the agent, per memory-system.md):
#   - Promoting [SOT:IDX:*] keywords at frequency >= 5 (advisory report only).
#   - Prose learnings quality - the mechanical summary is a safe minimum, not
#     a replacement for an agent's judgment on what actually worked/failed.
#
# Usage: checkpoint.sh [path-to-memory.db]   (default .agents/memory.db)
#   -n   dry run: print the fold plan, execute nothing.
set -euo pipefail

DRY_RUN=0
if [ "${1:-}" = "-n" ]; then DRY_RUN=1; shift; fi
DB="${1:-.agents/memory.db}"
[ -f "$DB" ] || { echo "No memory db at $DB. Init: sqlite3 $DB < memory-init.sql"; exit 1; }

echo "=== Log groups eligible for fold (sot_tags, status; n > 1) ==="
sqlite3 -header -column "$DB" "
  SELECT sot_tags, status, COUNT(*) AS n
  FROM agent_logs
  GROUP BY sot_tags, status
  HAVING COUNT(*) > 1
  ORDER BY n DESC;
"

if [ "$DRY_RUN" = "1" ]; then
    echo ""
    echo "(dry run - no fold executed)"
    exit 0
fi

echo ""
echo "=== Folding (single transaction: insert compiled rows, delete raw rows) ==="
BEFORE_COMPILE_MAX=$(sqlite3 "$DB" "SELECT COALESCE(MAX(id),0) FROM agent_compile_logs;")
sqlite3 "$DB" <<SQL
BEGIN TRANSACTION;

-- One compiled row per (sot_tags, status) group with more than one raw row.
INSERT INTO agent_compile_logs (agent, sot_tags, status, learnings, replaced_log_count)
SELECT
    'checkpoint',
    sot_tags,
    status,
    'Folded ' || COUNT(*) || ' ' || status || ' log(s) for ' || sot_tags ||
        ' spanning ' || MIN(ts) || ' to ' || MAX(ts) ||
        '. Mechanical summary only - the raw agent_logs.message text is gone after this fold; an agent should UPDATE this row''s learnings with denser prose if warranted.',
    COUNT(*)
FROM agent_logs
GROUP BY sot_tags, status
HAVING COUNT(*) > 1;

-- Delete exactly the raw rows that were just folded (same grouping key).
DELETE FROM agent_logs
WHERE (sot_tags, status) IN (
    SELECT sot_tags, status
    FROM agent_logs
    GROUP BY sot_tags, status
    HAVING COUNT(*) > 1
);

COMMIT;
SQL

# Assert every compiled row this run just wrote has replaced_log_count > 1.
# (Checked after commit, outside SQL, since RAISE() cannot run in a bare SELECT -
# only inside triggers. A shell-level assert keeps this portable stdlib sqlite3.)
BAD=$(sqlite3 "$DB" "SELECT COUNT(*) FROM agent_compile_logs WHERE id > $BEFORE_COMPILE_MAX AND replaced_log_count <= 1;")
if [ "$BAD" != "0" ]; then
    echo "FATAL: checkpoint invariant violated - $BAD new row(s) with replaced_log_count <= 1" >&2
    exit 1
fi
echo "Fold complete."

echo ""
echo "=== IDX keywords at promotion threshold (frequency >= 5) [advisory, not auto-applied] ==="
sqlite3 -header -column "$DB" "SELECT keyword, frequency, description FROM sot_keywords WHERE category='IDX' AND frequency >= 5;"

echo ""
echo "=== Past failure learnings (do not retry these) ==="
sqlite3 -header -column "$DB" "SELECT ts, sot_tags, learnings FROM agent_compile_logs WHERE status='FAILURE' ORDER BY ts DESC LIMIT 10;"

echo ""
echo "Remaining manual steps (not mechanical, left to the checkpoint agent):"
echo " 1. Review the mechanical learnings above; rewrite denser prose learnings"
echo "    where the terse summary is not enough for a future agent (memory-system.md)."
echo " 2. Promote listed IDX keywords to categories if warranted (UPDATE sot_keywords; update README index)."
echo " 3. Append verified 'worked' learnings to .claude/agents/ definitions (one line each)."
