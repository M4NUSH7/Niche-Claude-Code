#!/usr/bin/env python3
"""harness_status.py - reconcile checkbox state, git gate tags, and disk reality.

Audit fixes #2 (gates violated silently), #3 (docs describe a repo that doesn't exist),
#7 (hand-maintained Active Context drifts).

Checks:
  * per terminal: phase progress (checked/total), first unchecked task
  * gate tags:  GATE checkbox checked but git tag missing        -> VIOLATION
                git tag exists but GATE checkbox unchecked       -> WARN (stale checklist)
  * sequencing: terminal has checked work while a blockedUntil
                tag is still missing (and not neverBlocked)      -> VIOLATION
  * disk:       terminal `paths` globs matching zero tracked files -> INFO
  * docs:       architecture/*.md missing a `status: target|current` header -> WARN
  * hooks:      logged fail-open / allow-unclaimed events since last run -> INFO

Usage:
  py -3 harness/harness_status.py            # full report
  py -3 harness/harness_status.py --brief    # 1 line per terminal + violations (SessionStart hook)
  py -3 harness/harness_status.py --check    # CI: exit 1 on violations
  py -3 harness/harness_status.py --write    # also regenerate:
        memory/INDEX.md            (Active Context block between harness markers)
        context/architecture/REALITY.md  (from `git ls-files` - the always-true tree)
"""
import glob
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from fnmatch import fnmatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK_START = "<!-- harness:active-context:start -->"
MARK_END = "<!-- harness:active-context:end -->"


def rebuild_master_db():
    """D1: rebuild .agents/master.db from the per-terminal tN.db shards before recall/report.

    Import is local and guarded: build_master.py lives alongside this file (both are copied
    verbatim by scaffold.sh into harness/), but a partially-synced project or an older kit copy
    without it must not crash status reporting.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import build_master
        return build_master.build(ROOT, quiet=True)
    except Exception:
        return None  # no shards, sqlite3 unavailable, or build_master.py not present - skip cleanly


def print_failure_recall(root=ROOT, dbpath=".agents/master.db"):
    """D1: surface FAILURE-status learnings from the derived master.db at SessionStart.

    Guard behavior is deliberate: absent db or table is a clean skip, not an error - a fresh
    project with no shards built yet (or sqlite3 unavailable at scaffold time) must still start
    a session normally. See 05_hooks_and_logging.md "Per-terminal memory shards + derived
    master.db (D1)".
    """
    path = os.path.join(root, dbpath)
    if not os.path.exists(path):
        return
    try:
        con = sqlite3.connect(path, timeout=5)
        rows = con.execute(
            "SELECT terminal, agent, tags, learnings FROM agent_compile_log "
            "WHERE status='FAILURE' ORDER BY ts DESC LIMIT 10"
        ).fetchall()
        con.close()
    except Exception:
        return  # table absent or db locked - skip cleanly, never crash SessionStart
    if rows:
        print("## Past failure learnings (do not retry these)")
        for terminal, agent, tags, learnings in rows:
            print(f"- [{terminal}/{agent} {tags}] {learnings}")


def load_cfg():
    with open(os.path.join(ROOT, "harness", "harness.config.json"), encoding="utf-8") as f:
        return json.load(f)


def git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20)
        return out.stdout
    except Exception:
        return ""


def parse_phases(terminal):
    """Return dict: phases=[(title, done, total)], first_unchecked, gate_lines, superseded.

    Three checkbox states, not two:
      - [ ]  open      -> the task queue (first unchecked = current task)
      - [x]  done      -> built and still standing
      - [~]  SUPERSEDED-> built, then pivoted away from. NOT progress, NOT a task.

    Without the third state a pivot has nowhere to go: leaving a killed task [x] makes
    phases.md assert work that no longer exists on disk (audit #3 through a new door),
    and reverting it to [ ] silently re-queues work we deliberately abandoned.
    Superseded lines are excluded from BOTH done and the queue, and each must link its
    pivot note (see 11_pivots.md).
    """
    path = os.path.join(ROOT, ".bld", terminal, "phases.md")
    info = {"exists": os.path.exists(path), "phases": [], "first_unchecked": None,
            "gate_lines": [], "checked": 0, "total": 0,
            "superseded": 0, "superseded_lines": [], "unlinked_superseded": []}
    if not info["exists"]:
        return info
    title, done, total = None, 0, 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            h = re.match(r"^##\s+(.*)", line)
            if h:
                if title is not None:
                    info["phases"].append((title, done, total))
                title, done, total = h.group(1).strip(), 0, 0
                continue
            m = re.match(r"^\s*-\s*\[([ xX~])\]\s*(.*)", line)
            if m:
                mark, text = m.group(1).lower(), m.group(2).strip()
                if mark == "~":
                    info["superseded"] += 1
                    info["superseded_lines"].append(text[:100])
                    # A pivot MUST be traceable to its note, or it is just a deleted task.
                    if not re.search(r"memory/decisions/\S+\.md|\[\[.+?\]\]", text):
                        info["unlinked_superseded"].append(text[:100])
                    continue  # neither progress nor queue
                checked = mark == "x"
                total += 1
                info["total"] += 1
                if checked:
                    done += 1
                    info["checked"] += 1
                elif info["first_unchecked"] is None:
                    info["first_unchecked"] = text[:100]
                if "GATE" in text.upper():
                    info["gate_lines"].append((text, checked))
    if title is not None:
        info["phases"].append((title, done, total))
    return info


def analyze(cfg):
    tags = set(git("tag", "-l").split())
    tracked = git("ls-files").splitlines()
    violations, warnings, infos = [], [], []
    terminals = {}

    for t, spec in cfg.get("terminals", {}).items():
        info = parse_phases(t)
        terminals[t] = info
        if not info["exists"]:
            infos.append(f"{t}: no .bld/{t}/phases.md yet")
            continue

        missing = [g for g in spec.get("blockedUntil", []) if g not in tags]
        if missing and info["checked"] > 0 and not spec.get("neverBlocked"):
            violations.append(
                f"{t} has {info['checked']} checked task(s) but blocking gate tag(s) "
                f"{missing} do not exist - work started before its gate opened."
            )

        for u in info.get("unlinked_superseded", []):
            violations.append(
                f"{t}: superseded task '- [~] {u}' has no pivot note link. "
                f"Every pivot must cite memory/decisions/<note>.md - an unlinked [~] is "
                f"an undocumented deletion, not a pivot (see 11_pivots.md)."
            )
        if info.get("superseded"):
            infos.append(f"{t}: {info['superseded']} superseded task(s) - excluded from progress counts.")

        for line, checked in info["gate_lines"]:
            named = [g for g in cfg.get("gates", {}) if g in line]
            for g in named:
                if checked and g not in tags:
                    violations.append(
                        f"{t}: GATE '{g}' is checked in phases.md but git tag missing. "
                        f"(If this gate was REVOKED by a pivot, mark its line '- [~]' and link the note.)"
                    )
                if not checked and g in tags:
                    warnings.append(f"{t}: git tag '{g}' exists but its GATE checkbox is unchecked (stale checklist).")

        dead = [p for p in spec.get("paths", []) if not any(fnmatch(f, p) for f in tracked)]
        if dead:
            infos.append(f"{t}: no tracked files match {dead} (domain not built yet - fine early on).")

    for doc in sorted(glob.glob(os.path.join(ROOT, "architecture", "*.md"))):
        with open(doc, encoding="utf-8", errors="ignore") as f:
            head = f.read(400)
        if not re.search(r"status:\s*(target|current)", head, re.IGNORECASE):
            warnings.append(f"{os.path.relpath(doc, ROOT)} missing 'status: target|current' header.")

    for tree in (".claude", ".agents"):
        hp = os.path.join(ROOT, tree, "logs", "hooks.jsonl")
        if os.path.exists(hp):
            with open(hp, encoding="utf-8") as f:
                events = [json.loads(l) for l in f if l.strip()]
            fo = sum(1 for e in events if e.get("action") == "fail-open")
            un = sum(1 for e in events if e.get("action") == "allow-unclaimed")
            if fo or un:
                infos.append(f"{tree}: {fo} hook fail-open(s), {un} unclaimed-path write(s) logged (see logs/hooks.jsonl).")

    return terminals, tags, violations, warnings, infos


def render(cfg, terminals, tags, violations, warnings, infos, brief=False):
    lines = []
    for t, spec in cfg.get("terminals", {}).items():
        info = terminals.get(t, {})
        if not info.get("exists"):
            lines.append(f"{t} [{spec.get('domain','?')}]: no phases file")
            continue
        cur = next(((ti, d, to) for ti, d, to in info["phases"] if d < to), None)
        phase = f"{cur[0]} ({cur[1]}/{cur[2]})" if cur else "ALL PHASES COMPLETE"
        nxt = f" | next: {info['first_unchecked']}" if info["first_unchecked"] else ""
        lines.append(f"{t} [{spec.get('domain','?')}]: {info['checked']}/{info['total']} - {phase}{nxt}")
    gate_line = "gates present: " + (", ".join(sorted(g for g in cfg.get("gates", {}) if g in tags)) or "none")
    out = ["## Harness status " + time.strftime("%Y-%m-%d %H:%M"), *lines, gate_line]
    for v in violations:
        out.append(f"VIOLATION: {v}")
    if not brief:
        out += [f"WARN: {w}" for w in warnings] + [f"INFO: {i}" for i in infos]
    return "\n".join(out)


def write_outputs(cfg, report_text):
    # memory/INDEX.md Active Context block (audit #7 - generated, not hand-written)
    idx = os.path.join(ROOT, "memory", "INDEX.md")
    os.makedirs(os.path.dirname(idx), exist_ok=True)
    block = f"{MARK_START}\n{report_text}\n{MARK_END}"
    if os.path.exists(idx):
        with open(idx, encoding="utf-8") as f:
            text = f.read()
        if MARK_START in text and MARK_END in text:
            text = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), block, text, flags=re.DOTALL)
        else:
            text += f"\n\n## Active Context (generated)\n\n{block}\n"
    else:
        text = f"# Memory Index\n\n## Active Context (generated)\n\n{block}\n"
    with open(idx, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    # context/architecture/REALITY.md (audit #3 - the always-true tree)
    tracked = git("ls-files").splitlines()
    counts = {}
    for f_ in tracked:
        top = f_.split("/", 1)[0]
        counts[top] = counts.get(top, 0) + 1
    body = "\n".join(f"- `{k}/` - {v} tracked file(s)" if "." not in k or "/" in k else f"- `{k}` "
                     for k, v in sorted(counts.items()))
    reality = os.path.join(ROOT, "context", "architecture", "REALITY.md")
    os.makedirs(os.path.dirname(reality), exist_ok=True)
    with open(reality, "w", encoding="utf-8", newline="\n") as f:
        f.write("<!-- generated by harness_status.py --write; do not edit -->\n"
                f"# REALITY - what is actually on disk ({time.strftime('%Y-%m-%d')})\n\n"
                "Architecture docs may describe the *target*; this file is the *current* tracked tree.\n"
                "When they disagree, trust this file.\n\n"
                f"{body}\n\nTotal tracked files: {len(tracked)}\n")


def main():
    cfg = load_cfg()
    terminals, tags, violations, warnings, infos = analyze(cfg)
    brief = "--brief" in sys.argv
    report = render(cfg, terminals, tags, violations, warnings, infos, brief=brief)
    print(report)

    # D1: rebuild the derived master.db from per-terminal shards, then surface FAILURE recall.
    # Runs on both --brief (the generated SessionStart hook) and plain/--write calls, so a fresh
    # session always sees current "do not retry this" rows rather than a stale or absent recall.
    rebuild_master_db()
    print_failure_recall()

    if "--write" in sys.argv:
        write_outputs(cfg, render(cfg, terminals, tags, violations, warnings, infos, brief=True))
        print("\nwrote memory/INDEX.md active-context block + context/architecture/REALITY.md")
    if "--check" in sys.argv and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
