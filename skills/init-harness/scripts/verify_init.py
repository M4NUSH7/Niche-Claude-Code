#!/usr/bin/env python3
"""verify_init.py - prove the harness WORKS. Behavioral, not existential.

"The files exist" is not verification. The failure mode this catches is a harness whose hooks
are wired, whose config is valid, whose tree is perfect - and whose guards never fire because
the interpreter cannot start. That harness looks installed and enforces nothing.

So every check here asserts BEHAVIOUR: the guard actually blocks, the tag actually gates,
the logger actually writes a row.

Usage: verify_init.py [project-root]     # exit 0 = proven, 1 = not
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ".")
PASS, FAIL = [], []


def cfg():
    with open(os.path.join(ROOT, "harness", "harness.config.json"), encoding="utf-8") as f:
        return json.load(f)


def hook(py, script, payload, env=None):
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run([py, os.path.join(ROOT, ".claude", "hooks", script)],
                       input=json.dumps(payload), capture_output=True, text=True, cwd=ROOT, env=e, timeout=30)
    return p.returncode, p.stdout.strip()


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}{(' - ' + detail) if detail and not cond else ''}")
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))


def main():
    c = cfg()
    py = c.get("toolchain", {}).get("python") or c.get("python")
    print(f"=== verifying {ROOT}\n=== interpreter {py}\n")

    # 0. The interpreter runs at all. Everything below is meaningless if this fails.
    print("[0] interpreter")
    rc = subprocess.run([py, "-c", "print('ok')"], capture_output=True, text=True).returncode
    check("interpreter executes", rc == 0, "hooks would fail ABSENT: no block, no log, no trace")
    if rc != 0:
        print("\nABORT: nothing below can pass.")
        return 1

    # 1. Read guard - audit #5. Must block unbounded AND over-limit reads.
    print("[1] read guard (audit #5)")
    max_lines = c.get("readGuard", {}).get("maxLines", 500)
    big = os.path.join(tempfile.mkdtemp(), "big.md")
    with open(big, "w", encoding="utf-8") as f:
        f.write("\n".join(f"line {i}" for i in range(max_lines * 2)))
    rc, _ = hook(py, "big_read_guard.py", {"tool_input": {"file_path": big}})
    check("blocks unbounded read of oversized file", rc == 1)
    rc, _ = hook(py, "big_read_guard.py", {"tool_input": {"file_path": big, "limit": max_lines * 20}})
    check(f"blocks limit > maxLines ({max_lines}) - the audit #5 bypass", rc == 1)
    rc, _ = hook(py, "big_read_guard.py", {"tool_input": {"file_path": big, "limit": max_lines // 2}})
    check("allows windowed read", rc == 0)

    # 2. Gate guard - audit #2. Gates must be mechanical, not prose.
    print("[2] gate guard (audit #2)")
    terminals = c.get("terminals", {})
    check("at least one terminal has neverBlocked:true",
          any(s.get("neverBlocked") for s in terminals.values()),
          "a stalled gate stalls the whole build with no never_blocked terminal - see decision-guide.md Sec.1")
    gated = next((t for t, s in terminals.items()
                  if s.get("blockedUntil") and not s.get("neverBlocked")), None)
    if gated:
        spec = terminals[gated]
        target = spec["paths"][0].replace("**", "probe.ts").replace("//", "/")
        tags = subprocess.run(["git", "tag", "-l"], cwd=ROOT, capture_output=True, text=True).stdout.split()
        missing = [t for t in spec["blockedUntil"] if t not in tags]
        rc, _ = hook(py, "gate_guard.py", {"tool_input": {"file_path": target}},
                     {"HARNESS_TERMINAL": gated})
        if missing:
            check(f"{gated} blocked while gate {missing} missing", rc == 1)
        else:
            check(f"{gated} allowed once gate exists", rc == 0)
        other = next((t for t in terminals if t != gated), None)
        if other:
            rc, _ = hook(py, "gate_guard.py",
                         {"tool_input": {"file_path": terminals[other]["paths"][0].replace("**", "x.ts")}},
                         {"HARNESS_TERMINAL": gated})
            check(f"{gated} blocked from {other}'s domain", rc == 1)
    else:
        # FAIL LOUD, not a silent SKIP: a degenerate/single-terminal topology with no gate and
        # no cross-domain boundary means the gate probe proves nothing about this harness. A
        # harness whose gate mechanism was never exercised is unproven, not "not applicable."
        check("gate probe exercised at least one gated/cross-domain case", False,
              "no terminal has both blockedUntil and neverBlocked:false - either this is "
              "intentionally single-terminal (fine) and should say so explicitly in the config "
              "comment, or the topology is degenerate and the gate mechanism is unproven")

    # 2b. Worktree write-gate (C1/C3) - each configured terminal should have its own git
    # worktree + branch (the DEFAULT write sandbox), and gate_guard.py must still block a write
    # into a sensitivePaths glob regardless of worktrees. Report-only on the worktree half if
    # git/git-worktree is unavailable in this verify environment - "report the gap" doctrine,
    # not a design-around.
    print("[2b] worktree write-gate (C1/C3)")
    git_ok = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                            cwd=ROOT, capture_output=True, text=True).returncode == 0
    if not git_ok:
        print("  REPORT  not a git work tree here - worktree probe skipped (report, not a "
              "hard failure: this environment may not be the project's actual git checkout).")
    else:
        # `git branch --list` shows nothing on a brand-new repo with zero commits (unborn HEAD) -
        # `git worktree list` is the source of truth for "does this worktree+branch pair exist"
        # even pre-first-commit, since `git worktree add -b` creates the branch as part of adding
        # the worktree itself.
        wt_list = subprocess.run(["git", "worktree", "list"], cwd=ROOT,
                                 capture_output=True, text=True).stdout
        missing_wt = []
        for t in terminals:
            wt_dir = os.path.join(ROOT, ".claude", "worktrees", t)
            branch_ok = f"[harness/{t}]" in wt_list
            if not (os.path.isdir(wt_dir) and branch_ok):
                missing_wt.append(t)
        if missing_wt:
            print(f"  REPORT  {len(missing_wt)}/{len(terminals)} terminal(s) missing a worktree "
                  f"and/or branch harness/tN: {missing_wt}. Not a hard failure - scaffold.sh "
                  f"skips worktree creation cleanly pre-first-commit or if 'git worktree add' "
                  f"fails; re-run scaffold.sh after an initial commit to create them.")
        else:
            check(f"all {len(terminals)} terminal(s) have a worktree dir + harness/tN branch",
                  True)

    sensitive = c.get("sensitivePaths", [])
    if sensitive and terminals:
        probe_terminal = next(iter(terminals))
        probe_path = sensitive[0].replace("**", "probe.ts").replace("//", "/")
        rc, _ = hook(py, "gate_guard.py", {"tool_input": {"file_path": probe_path}},
                     {"HARNESS_TERMINAL": probe_terminal})
        check("gate_guard.py still blocks a sensitivePaths write (the boundary a worktree "
              "cannot express)", rc == 1)
    else:
        print("  REPORT  no sensitivePaths configured or no terminals - sensitivePaths block "
              "probe skipped.")

    # 3. Logger - audit #8. The hot path must actually write.
    print("[3] logger (audit #8)")
    rc, _ = hook(py, "log_tool_use.py",
                 {"tool_name": "Verify", "tool_response": "probe"}, {"CLAUDE_AGENT_NAME": "verify"})
    jl = os.path.join(ROOT, ".claude", "logs", "verify", "verify.jsonl")
    check("PostToolUse writes a JSONL row", rc == 0 and os.path.exists(jl))

    # 4. Drift + orphans - audit #1.
    print("[4] sync drift (audit #1)")
    p = subprocess.run([py, os.path.join(ROOT, "harness", "sync_harness.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    check("--check reports OK (no drift, no orphans)", p.returncode == 0,
          (p.stdout or p.stderr).strip()[:160])

    # 5. Status reconciliation - audit #2/#7 + pivots.
    print("[5] status reconciliation")
    p = subprocess.run([py, os.path.join(ROOT, "harness", "harness_status.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    check("checkboxes/tags/disk reconcile", p.returncode == 0, (p.stdout or "").strip()[:160])

    # 6. Pivot mechanism present.
    print("[6] pivot mechanism")
    check("pivot template installed",
          os.path.exists(os.path.join(ROOT, "memory", "decisions", "_pivot-template.md")))
    check("pivots configured (human-gated)",
          c.get("pivots", {}).get("requireHumanApproval") is True)

    # 7. Model routing (J1/A3) - static proof only. A subagent can't be truly spawned from
    # inside this script, so this checks the one thing that CAN be checked mechanically: the
    # stamped frontmatter model IDs agree with the config. That is necessary but NOT sufficient -
    # see the runtime instruction block this prints.
    print("[7] model routing (static: frontmatter == config)")
    models_cfg = c.get("models", {})
    agents_dir = os.path.join(ROOT, ".claude", "agents")
    frontmatter_checked = 0
    if os.path.isdir(agents_dir):
        for fn in sorted(os.listdir(agents_dir)):
            if not fn.endswith(".md"):
                continue
            name = fn[:-3]
            spec = c.get("agents", {}).get(name)
            if not spec:
                continue
            expected_model = models_cfg.get(spec.get("role", "workhorse"))
            with open(os.path.join(agents_dir, fn), encoding="utf-8") as f:
                text = f.read()
            m = re.search(r"^model:\s*(\S+)\s*$", text, re.MULTILINE)
            frontmatter_checked += 1
            check(f"{name}.md frontmatter model == config-resolved ({expected_model})",
                  bool(m) and m.group(1) == expected_model,
                  f"found {m.group(1) if m else 'MISSING'!r}")
    check("at least one agent frontmatter checked", frontmatter_checked > 0,
          "no .claude/agents/*.md matched a config agent - run sync_harness.py first")
    print("  NOTE: this is a STATIC proof (frontmatter vs config), not a runtime one. The rule")
    print("  only binds if you do NOT pass model: at spawn - Agent tool's model: is a TIER ALIAS")
    print("  (sonnet/opus/haiku -> latest of tier) and SILENTLY OVERRIDES the stamped pin.")
    print("  Runtime verification (operator must do this, not self-report):")
    print("    1. Spawn the agent with subagent_type set and NO model: argument.")
    print("    2. Ask it to state its own model via /debug or by naming itself - never trust")
    print("       the agent's own claim in prose; /debug shows the actual resolved model.")
    print("    3. Assert the /debug-reported model == models[role] in harness.config.json.")

    # 8. Effort validation (A1) - every stamped effort is in the valid enum and <= maxEffort.
    print("[8] effort validation")
    effort_enum = ("low", "medium", "high", "xhigh", "max")
    max_effort = c.get("maxEffort", "high")
    check("maxEffort is valid and not 'max'",
          max_effort in effort_enum and max_effort != "max", f"maxEffort={max_effort!r}")
    max_rank = effort_enum.index(max_effort) if max_effort in effort_enum else -1
    for name, spec in c.get("agents", {}).items():
        effort = spec.get("effort")
        valid = effort in effort_enum
        check(f"agents.{name}.effort ({effort!r}) is valid", valid)
        if valid:
            check(f"agents.{name}.effort <= maxEffort", effort_enum.index(effort) <= max_rank,
                  f"{effort!r} > {max_effort!r}")

    # 9. Network reachability - REPORT the gap, do not design around it. This is the one probe
    # in the harness that is allowed to fail soft: connectivity is an environment fact, not a
    # harness defect, and the doctrine is "report the gap, don't design around it."
    print("[9] network reachability (report-only, never hard-fails)")
    net_host, net_port = "github.com", 443
    try:
        import socket
        s = socket.create_connection((net_host, net_port), timeout=3)
        s.close()
        print(f"  REPORT  reachable: {net_host}:{net_port}")
    except Exception as e:
        print(f"  REPORT  UNREACHABLE: {net_host}:{net_port} ({e}). "
              f"Installers/network-gated steps will need manual handling in this environment.")

    # 10. D1 - per-terminal memory shards + derived master.db + FAILURE recall (report, don't
    # hard-fail: sqlite3 may be unavailable in the verify environment, or scaffold.sh's shard-init
    # step may have been skipped - see 05_hooks_and_logging.md "Per-terminal memory shards").
    print("[10] memory shards + derived master.db (D1)")
    import glob as _glob
    shard_dir = os.path.join(ROOT, c.get("memory", {}).get("shardDir", ".agents/logs"))
    shard_pattern = c.get("memory", {}).get("shardPattern", "t*.db")
    shards = sorted(_glob.glob(os.path.join(shard_dir, shard_pattern)))
    terminals_cfg = c.get("terminals", {})
    if not shards:
        print(f"  REPORT  no shards found at {shard_dir}/{shard_pattern} (sqlite3 unavailable at "
              f"scaffold time, or scaffold.sh has not been run yet). Not a hard failure - the "
              f"master.db + FAILURE recall simply have nothing to derive from yet.")
    else:
        try:
            import sqlite3
            all_queryable = True
            for shard in shards:
                con = sqlite3.connect(shard, timeout=5)
                con.execute("SELECT 1 FROM agent_log LIMIT 1")
                con.execute("SELECT 1 FROM agent_compile_log LIMIT 1")
                con.close()
            check(f"{len(shards)} shard(s) exist and are queryable (agent_log, agent_compile_log)",
                  True)
        except Exception as e:
            all_queryable = False
            check("shards exist and are queryable", False, str(e))
        missing_terms = [t for t in terminals_cfg
                         if not os.path.exists(os.path.join(shard_dir, f"{t}.db"))]
        check("every configured terminal has a shard", not missing_terms,
              f"missing: {missing_terms}" if missing_terms else "")

        # Smoke-test build_master.py: seed a shard, build master, query it back.
        try:
            sys.path.insert(0, os.path.join(ROOT, "harness"))
            import build_master
            n_shards, n_log, n_compile = build_master.build(ROOT, quiet=True)
            master_path = os.path.join(ROOT, c.get("memory", {}).get("db", ".agents/master.db"))
            con = sqlite3.connect(master_path, timeout=5)
            row_count = con.execute("SELECT COUNT(*) FROM agent_compile_log").fetchone()[0]
            con.close()
            check("build_master.py rebuilds master.db from shards",
                  n_shards == len(shards) and os.path.exists(master_path),
                  f"n_shards={n_shards} expected={len(shards)}")
            # Idempotency: re-run must not change the row count.
            build_master.build(ROOT, quiet=True)
            con = sqlite3.connect(master_path, timeout=5)
            row_count_2 = con.execute("SELECT COUNT(*) FROM agent_compile_log").fetchone()[0]
            con.close()
            check("build_master.py is idempotent (re-run does not duplicate rows)",
                  row_count == row_count_2, f"{row_count} != {row_count_2}")
            # The FAILURE recall query itself must run without error (report-only on rows found -
            # an empty result is a correct, clean answer for a fresh harness, not a failure).
            con = sqlite3.connect(master_path, timeout=5)
            con.execute(
                "SELECT terminal, agent, tags, learnings FROM agent_compile_log "
                "WHERE status='FAILURE' ORDER BY ts DESC LIMIT 10"
            ).fetchall()
            con.close()
            check("FAILURE recall query runs against master.db", True)
        except Exception as e:
            check("build_master.py / FAILURE recall smoke test", False, str(e))

    # 11. Goal-packet verifier (12_graph_of_loops.md Sec.2) - proves the terminal is assigned
    # IN CODE from actual criteria results, never inferred from a self-report. Builds a tiny
    # throwaway goal-packet with one passing criterion and one failing criterion, runs
    # harness/verify_goal_packet.py against it, and asserts the terminal it returns is one
    # that reflects a genuine mixed result (partial while budget remains, or failure/blocked
    # once budget is exhausted) - never `success`. Report-only (not a hard failure) if the
    # script or sqlite3 is unavailable in this environment, matching the D1 guard doctrine.
    print("[11] goal-packet verifier (12_graph_of_loops.md Sec.2)")
    verifier_script = os.path.join(ROOT, "harness", "verify_goal_packet.py")
    if not os.path.exists(verifier_script):
        print("  REPORT  harness/verify_goal_packet.py not present - run scaffold.sh's kit-copy "
              "step (this file lives in templates/kit/harness/) before this probe can run.")
    else:
        try:
            probe_dir = tempfile.mkdtemp()
            existing = os.path.join(probe_dir, "exists.txt")
            with open(existing, "w", encoding="utf-8") as f:
                f.write("verify_init probe file\n")
            packet_path = os.path.join(probe_dir, "probe-packet.yml")
            with open(packet_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(
                    "objective: >\n"
                    "  verify_init probe: one passing criterion, one failing criterion.\n\n"
                    "success_criteria:\n"
                    f"  - \"`test -f {existing}` exits 0\"\n"
                    "  - \"`test -f nonexistent-probe-file.never` exits 0\"\n\n"
                    "scope_boundaries:\n"
                    "  - \"probe only - not real work\"\n\n"
                    "inputs:\n"
                    f"  - \"{existing}\"\n\n"
                    "outputs:\n"
                    "  - \"n/a\"\n\n"
                    "budget:\n"
                    "  max_retries: 0\n"
                    "  max_turns: 1\n\n"
                    "escalation:\n"
                    "  handoff_note: \"memory/handoff/session/verify-init-probe.md\"\n"
                    "  decision_note_if_blocked: \"memory/decisions/verify-init-probe.md\"\n\n"
                    "terminals:\n"
                    "  declared: [success, partial, failure, ambiguity, blocked]\n"
                    "  routes:\n"
                    "    success: \"DONE\"\n"
                    "    partial: \"retry\"\n"
                    "    failure: \"memory/handoff/\"\n"
                    "    ambiguity: \"memory/handoff/\"\n"
                    "    blocked: \"memory/handoff/\"\n"
                )
            probe_db = os.path.join(probe_dir, "master.db")
            p = subprocess.run(
                [py, verifier_script, packet_path, "--attempt", "1", "--db", probe_db,
                 "--terminal-name", "verify-init-probe"],
                capture_output=True, text=True, cwd=ROOT, timeout=60,
            )
            out = p.stdout or ""
            m = re.search(r"^terminal:\s*(\w+)", out, re.MULTILINE)
            terminal = m.group(1) if m else None
            # budget.max_retries=0 with attempt=1 means budget is already exhausted on this one
            # run, so the mixed pass/fail result must resolve straight to failure or blocked -
            # never success (one criterion genuinely fails) and never a silent partial (budget
            # exhausted). This is the mechanical proof that DoD is assigned in code: a self-report
            # would happily claim "done", the script cannot, because it actually ran `test -f`.
            check("verify_goal_packet.py assigns a non-success terminal from mixed real results",
                  terminal in ("failure", "blocked"),
                  f"terminal={terminal!r}, exit={p.returncode}, stdout={out[-300:]!r}")
            try:
                import sqlite3
                con = sqlite3.connect(probe_db, timeout=5)
                rows = con.execute(
                    "SELECT status, learnings FROM agent_compile_log WHERE terminal='verify-init-probe'"
                ).fetchall()
                con.close()
                check("FAILURE-shaped ledger row written for the probe's non-success terminal",
                      any(r[0] == "FAILURE" for r in rows),
                      f"rows={rows}")
            except Exception as e:
                print(f"  REPORT  sqlite3 unavailable or DB unreadable - ledger-row assertion "
                      f"skipped ({e}). Terminal-assignment result above still stands.")
        except Exception as e:
            print(f"  REPORT  goal-packet verifier probe could not run cleanly ({e}) - "
                  f"report-only, not a hard failure.")

    print(f"\n=== {len(PASS)} passed, {len(FAIL)} failed ===")
    if FAIL:
        print("\nFAILED:")
        for f in FAIL:
            print(f"  - {f}")
        print("\nA harness that does not block is decorative. Fix before building on it.")
        return 1
    print("Harness PROVEN: guards block, gates gate, logger logs.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"verify_init: {e}")
        sys.exit(1)
