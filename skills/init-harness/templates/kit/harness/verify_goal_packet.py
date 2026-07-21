#!/usr/bin/env python3
"""verify_goal_packet.py - turn a filled goal-packet YAML into a terminal decision IN CODE.

Doctrine: templates/docs/12_graph_of_loops.md Sec.2 - "checked in code, not inferred from the
final message" is the load-bearing rule. A subagent's own prose ("I think this worked!") is
never the terminal. This script IS the mechanical check: it runs each success_criteria item as
a shell command and assigns one of the five declared terminals (success, partial, failure,
ambiguity, blocked) from the actual exit codes - never from anyone's self-report.

Zero dependencies on purpose: the goal-packet template has a small, known shape (see
templates/goal-packet.template.yml), so this parses that shape directly with a tolerant
line-based parser instead of requiring PyYAML. If PyYAML happens to be installed, it is NOT
used - one parser, one behavior, on every machine this harness targets (stdlib only, no pip,
no network - see SKILL.md's toolchain policy).

Terminal-assignment logic (in code, matching 12_graph_of_loops.md Sec.2's table):
  - no runnable success_criteria (empty, or every item still looks like a template
    placeholder "<...>")                          -> ambiguity  (criteria unclear)
  - every runnable criterion passes                -> success
  - some pass, some fail, retries remain in budget  -> partial
  - some/all fail AND this attempt exhausts
    budget.max_retries:
      - packet's `inputs` are missing on disk       -> blocked   (can't proceed, human needed)
      - otherwise                                    -> failure   (attempted, unmet, no ambiguity)

Retry counter: a small JSON state file next to the packet (<packet>.state.json) tracks attempts
per packet path, so retries are BOUNDED and VISIBLE (12_graph_of_loops.md Sec.3), not just an
in-memory count the orchestrator forgets. --attempt N overrides/seeds it explicitly (e.g. from
an orchestrator that tracks attempts itself); otherwise the state file's own counter is used and
incremented on every run.

On failure/blocked/ambiguity: writes a FAILURE-shaped row into agent_compile_log (same table
harness_status.py's print_failure_recall() reads - see memory-schema.sql) so a future session's
SessionStart FAILURE-recall surfaces it without anyone remembering it happened. Guarded: skips
cleanly (reports, does not crash) if sqlite3 or the DB file is unavailable.

Usage:
  python verify_goal_packet.py <packet.yml> [--attempt N] [--db PATH] [--terminal-name NAME]

Exit codes (an orchestrator/CI branches on this, not on stdout parsing):
  0 = success
  1 = partial
  2 = failure
  3 = ambiguity
  4 = blocked
  5 = usage/parse error (packet missing, unreadable, malformed)
"""
import json
import os
import re
import subprocess
import sys
import time

EXIT_CODES = {
    "success": 0,
    "partial": 1,
    "failure": 2,
    "ambiguity": 3,
    "blocked": 4,
}

PLACEHOLDER_RE = re.compile(r"^\s*<.*>\s*$")


# ---------- tolerant goal-packet parser (stdlib only, known-shape template) ----------

def _strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def parse_goal_packet(path):
    """Parse the known goal-packet.template.yml shape without a YAML dependency.

    Handles exactly the constructs the template uses: top-level `key:` scalars/blocks,
    `key: >` folded scalars, list items ("  - ..."), and one level of nested mapping under
    a list-less block (budget.max_retries, budget.max_turns, escalation.*, terminals.declared,
    terminals.routes.*). Anything outside this known shape is best-effort ignored rather than
    raising - a verifier that crashes on an unusual comment is worse than one that under-parses
    and lets success_criteria (the field that matters) come through correctly.
    """
    with open(path, encoding="utf-8") as f:
        raw_lines = f.readlines()

    packet = {
        "objective": "",
        "success_criteria": [],
        "scope_boundaries": [],
        "inputs": [],
        "outputs": [],
        "budget": {"max_retries": None, "max_turns": None},
        "escalation": {"handoff_note": "", "decision_note_if_blocked": ""},
        "terminals": {"declared": [], "routes": {}},
    }

    top_key = None
    sub_key = None
    sub_indent = None   # indent level at which sub_key ("routes", etc.) itself was declared
    folded = False  # inside a `key: >` block scalar

    def indent_of(line):
        return len(line) - len(line.lstrip(" "))

    for raw in raw_lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ind = indent_of(line)

        # end a folded scalar once we see a new top-level key or a list item
        if folded and (ind == 0 or stripped.startswith("-")):
            folded = False

        if folded:
            # continuation of `objective: >` - only field that uses this in the template
            if top_key == "objective":
                packet["objective"] = (packet["objective"] + " " + stripped).strip()
            continue

        # top-level key (no leading space)
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if ind == 0 and m:
            top_key, val = m.group(1), m.group(2)
            sub_key = None
            sub_indent = None
            if top_key not in packet:
                top_key = None  # unknown key, ignore its body defensively
                continue
            if val.strip() == ">":
                folded = True
                packet["objective"] = ""
                continue
            if val.strip() in ("", "|"):
                continue  # block follows on subsequent indented lines
            # inline scalar value for a top-level key (rare in this template, but handle it)
            if top_key in ("success_criteria", "scope_boundaries", "inputs", "outputs"):
                continue
            continue

        if top_key is None:
            continue

        # list item under a top-level list field
        if stripped.startswith("- ") or stripped == "-":
            item = _strip_quotes(stripped[1:].strip())
            if top_key in ("success_criteria", "scope_boundaries", "inputs", "outputs"):
                packet[top_key].append(item)
            elif top_key == "terminals" and sub_key == "declared":
                # "declared: [a, b, c]" is handled below; this covers a YAML-list-style block
                for part in item.split(","):
                    part = part.strip(" []")
                    if part:
                        packet["terminals"]["declared"].append(part)
            continue

        # A line deeper-indented than an already-open nested block (e.g. "routes:") is an
        # ENTRY of that block, not a sibling key - regardless of what its own key name is.
        # This is what "success: DONE" under "routes:" under "terminals:" needs: without
        # tracking sub_indent, this line looks identical in shape to "routes:" itself and
        # gets mis-read as declaring a new sub_key instead of populating terminals.routes.
        if sub_key == "routes" and sub_indent is not None and ind > sub_indent:
            m3 = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", stripped)
            if m3 and top_key == "terminals":
                packet["terminals"]["routes"][m3.group(1)] = _strip_quotes(m3.group(2))
            continue

        # nested "sub_key: value" under budget / escalation / terminals
        m2 = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", stripped)
        if m2:
            sk, sv = m2.group(1), m2.group(2)
            sv = _strip_quotes(sv)
            if top_key == "budget":
                if sk in ("max_retries", "max_turns"):
                    try:
                        packet["budget"][sk] = int(re.sub(r"[^0-9-]", "", sv)) if sv and sv != "<n>" else None
                    except ValueError:
                        packet["budget"][sk] = None
            elif top_key == "escalation":
                if sk in ("handoff_note", "decision_note_if_blocked"):
                    packet["escalation"][sk] = sv
            elif top_key == "terminals":
                if sk == "declared":
                    inner = sv.strip("[] ")
                    packet["terminals"]["declared"] = [p.strip() for p in inner.split(",") if p.strip()]
                    sub_key, sub_indent = None, None
                elif sk == "routes":
                    sub_key, sub_indent = "routes", ind
                else:
                    sub_key, sub_indent = sk, ind
            continue

    return packet


def is_placeholder(item):
    """True for template placeholders like '<e.g. ...>' or a bare '<...>' - not a real check."""
    if not item or not item.strip():
        return True
    return bool(PLACEHOLDER_RE.match(item.strip()))


# ---------- criterion execution ----------

def extract_command(criterion):
    """Pull a runnable shell command out of a success_criteria prose item.

    The template's own examples are backtick-quoted commands embedded in a sentence, e.g.
    '`pytest tests/test_foo.py` exits 0' or '`test -f path`'. Prefer the backtick-quoted
    substring; fall back to the whole string if there are no backticks (an already-bare
    command is valid input too).
    """
    m = re.search(r"`([^`]+)`", criterion)
    if m:
        return m.group(1).strip()
    return criterion.strip()


def run_criterion(criterion, cwd):
    """Run one success_criteria item as a shell check. Returns (passed, output)."""
    cmd = extract_command(criterion)
    if not cmd:
        return False, "empty command"
    try:
        # shell=True on purpose: criteria are shell snippets ("test -f x", "grep -q y z",
        # "pytest tests/test_foo.py") - shlex-only argv splitting would break redirection,
        # globs, and && chains that are legitimate in a success_criteria line.
        proc = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()[:2000]
    except Exception as e:
        return False, f"error running criterion: {e}"


# ---------- retry-counter state file (visible, bounded - Sec.3) ----------

def state_path_for(packet_path):
    return packet_path + ".state.json"


def load_state(packet_path):
    p = state_path_for(packet_path)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"attempts": 0, "history": []}


def save_state(packet_path, state):
    p = state_path_for(packet_path)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


# ---------- ledger write (D1) ----------

def find_db(explicit_db, root):
    if explicit_db:
        return explicit_db
    for candidate in (
        os.path.join(root, ".agents", "master.db"),
    ):
        if os.path.exists(candidate):
            return candidate
    return os.path.join(root, ".agents", "master.db")


def write_failure_row(db_path, terminal_name, agent, tags, learnings):
    """Write a FAILURE-shaped agent_compile_log row. Guarded: report, never crash, if sqlite3
    or the DB path is unavailable - matching harness_status.py's own guard doctrine."""
    try:
        import sqlite3
    except ImportError:
        return False, "sqlite3 module unavailable - skipped ledger write (report-only)"
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.isdir(db_dir):
        return False, f"DB directory {db_dir} absent - skipped ledger write (report-only)"
    try:
        con = sqlite3.connect(db_path, timeout=10)
        con.execute(
            "CREATE TABLE IF NOT EXISTS agent_compile_log ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " ts TEXT, terminal TEXT, agent TEXT, tags TEXT, status TEXT, learnings TEXT,"
            " replaced_log_count INTEGER DEFAULT 0)"
        )
        con.execute(
            "INSERT INTO agent_compile_log (ts, terminal, agent, tags, status, learnings) "
            "VALUES (?, ?, ?, ?, 'FAILURE', ?)",
            (time.strftime("%Y-%m-%dT%H:%M:%S"), terminal_name, agent, tags, learnings),
        )
        con.commit()
        con.close()
        return True, "wrote FAILURE row to agent_compile_log"
    except Exception as e:
        return False, f"ledger write failed: {e}"


# ---------- terminal assignment ----------

def assign_terminal(packet, results, attempt, max_retries):
    """Decide the terminal FROM RESULTS, never from prose. Returns (terminal, reason)."""
    runnable = [r for r in results if not r["placeholder"]]
    if not runnable:
        return "ambiguity", "no runnable success_criteria (empty or all placeholders)"

    passed = [r for r in runnable if r["passed"]]
    failed = [r for r in runnable if not r["passed"]]

    if not failed:
        return "success", "all success_criteria passed"

    if passed:
        # some pass, some fail
        budget_exhausted = max_retries is not None and attempt >= max_retries
        if not budget_exhausted:
            return "partial", f"{len(passed)}/{len(runnable)} criteria passed, retries remain"
        # budget exhausted with partial progress - still resolves to blocked/failure below
    else:
        budget_exhausted = max_retries is not None and attempt >= max_retries
        if not budget_exhausted:
            return "partial", f"0/{len(runnable)} criteria passed yet, retries remain"

    # Budget exhausted (or no budget declared but nothing passed and this is being scored
    # as a terminal attempt): decide blocked vs failure from whether declared `inputs` exist.
    missing_inputs = [i for i in packet.get("inputs", [])
                      if not is_placeholder(i) and not os.path.exists(i)]
    if missing_inputs:
        return "blocked", f"budget exhausted; missing declared inputs: {missing_inputs}"
    return "failure", f"budget exhausted; {len(failed)}/{len(runnable)} criteria still failing"


# ---------- main ----------

def main(argv):
    if len(argv) < 1 or argv[0].startswith("-"):
        print("usage: verify_goal_packet.py <packet.yml> [--attempt N] [--db PATH] "
              "[--terminal-name NAME]", file=sys.stderr)
        return 5

    packet_path = argv[0]
    if not os.path.isfile(packet_path):
        print(f"verify_goal_packet: packet not found: {packet_path}", file=sys.stderr)
        return 5

    attempt_override = None
    db_override = None
    terminal_name = "unknown"
    i = 1
    while i < len(argv):
        if argv[i] == "--attempt" and i + 1 < len(argv):
            try:
                attempt_override = int(argv[i + 1])
            except ValueError:
                print(f"verify_goal_packet: --attempt expects an int, got {argv[i+1]!r}",
                      file=sys.stderr)
                return 5
            i += 2
        elif argv[i] == "--db" and i + 1 < len(argv):
            db_override = argv[i + 1]
            i += 2
        elif argv[i] == "--terminal-name" and i + 1 < len(argv):
            terminal_name = argv[i + 1]
            i += 2
        else:
            i += 1

    try:
        packet = parse_goal_packet(packet_path)
    except Exception as e:
        print(f"verify_goal_packet: failed to parse {packet_path}: {e}", file=sys.stderr)
        return 5

    packet_dir = os.path.dirname(os.path.abspath(packet_path)) or "."

    # ---- visible, bounded retry counter (Sec.3) ----
    state = load_state(packet_path)
    if attempt_override is not None:
        attempt = attempt_override
    else:
        attempt = state.get("attempts", 0) + 1
    max_retries = packet["budget"].get("max_retries")

    # ---- run each success_criteria item ----
    results = []
    for crit in packet["success_criteria"]:
        if is_placeholder(crit):
            results.append({"criterion": crit, "placeholder": True, "passed": False, "output": ""})
            continue
        passed, output = run_criterion(crit, packet_dir)
        results.append({"criterion": crit, "placeholder": False, "passed": passed, "output": output})

    terminal, reason = assign_terminal(packet, results, attempt, max_retries)

    # ---- persist the visible retry state ----
    state["attempts"] = attempt
    state.setdefault("history", []).append({
        "attempt": attempt,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "terminal": terminal,
        "reason": reason,
    })
    save_state(packet_path, state)

    # ---- report ----
    print(f"=== verify_goal_packet: {packet_path} (attempt {attempt}"
          f"{f'/{max_retries}' if max_retries is not None else ''}) ===")
    print(f"objective: {packet['objective'] or '(none parsed)'}")
    for r in results:
        if r["placeholder"]:
            tag = "SKIP (placeholder)"
        else:
            tag = "PASS" if r["passed"] else "FAIL"
        print(f"  [{tag}] {r['criterion']}")
        if not r["placeholder"] and r["output"]:
            first_line = r["output"].splitlines()[0] if r["output"].splitlines() else ""
            if first_line:
                print(f"         -> {first_line}")

    routes = packet.get("terminals", {}).get("routes", {})
    route = routes.get(terminal, "(no route declared for this terminal in the packet)")
    print(f"terminal: {terminal}  ({reason})")
    print(f"route: {route}")

    # ---- ledger write on non-success terminals ----
    if terminal in ("failure", "blocked", "ambiguity"):
        root = packet_dir
        for _ in range(6):
            if os.path.isdir(os.path.join(root, ".agents")):
                break
            parent = os.path.dirname(root)
            if parent == root:
                break
            root = parent
        db_path = find_db(db_override, root)
        failed_names = [r["criterion"] for r in results if not r["placeholder"] and not r["passed"]]
        learnings = (
            f"terminal={terminal}; attempt={attempt}"
            f"{f'/{max_retries}' if max_retries is not None else ''}; "
            f"reason={reason}; failed_criteria={failed_names}"
        )
        if terminal == "blocked":
            learnings += "; blocked, awaiting human"
        wrote, detail = write_failure_row(
            db_path, terminal_name, "verifier",
            f"goal-packet:{os.path.basename(packet_path)}", learnings,
        )
        print(f"ledger: {detail}")

    return EXIT_CODES[terminal]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
