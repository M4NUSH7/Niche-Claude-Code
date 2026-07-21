#!/usr/bin/env python3
"""preflight.py - verify the toolchain by EXECUTING it, before anything is generated.

Why this exists (the bug it was written for):
  The harness template pinned `py -3` for every hook. On a machine without the py launcher
  that command exits 127 - the hook process never starts. It does not fail *open*, it fails
  *absent*: no block, no log row, no audit trail. Every guard becomes decorative and NOTHING
  REPORTS IT. Bare `python` is no safer: it may resolve to the Microsoft Store stub or to an
  unrelated app's venv.

So: never trust a configured value. Run it.

Policy: tools the harness shells out to install to the GLOBAL/user toolchain (scoop on Windows,
`uv python install` for Python) - never vendored in-project, never a foreign venv.

Usage:
  python preflight.py            # report; exit 1 if anything required is unusable
  python preflight.py --json     # machine-readable (the skill reads this)
"""
import json
import os
import shutil
import subprocess
import sys

# What a hook actually imports. If any of these are missing the interpreter is useless to us.
HOOK_IMPORTS = "import sqlite3,json,glob,re,subprocess,fnmatch,shutil;print('ok')"


def run(cmd, timeout=30):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 127, "", str(e)


def is_store_stub(path):
    """The Microsoft Store python.exe shim: exists, is executable, does nothing useful."""
    return "windowsapps" in (path or "").lower()


def python_candidates():
    """Ordered best-first. uv-managed standalone CPython is the gold standard: a real
    interpreter, owned by no project, on the user toolchain."""
    out = []
    rc, so, _ = run(["uv", "python", "list", "--only-installed"])
    if rc == 0:
        for line in so.splitlines():
            for tok in line.split():
                if tok.lower().endswith("python.exe") or tok.endswith("/bin/python3"):
                    out.append(tok)
    for name in ("python3", "python", "py"):
        p = shutil.which(name)
        if p:
            out.append(p)
    # de-dupe, drop Store stubs entirely - they are the trap, not a fallback
    seen, ranked = set(), []
    for p in out:
        k = os.path.normcase(p)
        if k in seen or is_store_stub(p):
            continue
        seen.add(k)
        ranked.append(p)
    # prefer non-venv, uv-managed
    ranked.sort(key=lambda p: (0 if "uv" in p.lower() and "venv" not in p.lower() else 1,
                              1 if "venv" in p.lower() else 0))
    return ranked


def verify_python(path):
    """A pinned interpreter must: execute, import what hooks need, do WAL, and not be a venv."""
    rc, so, se = run([path, "-c", HOOK_IMPORTS])
    if rc != 0 or "ok" not in so:
        return False, f"cannot execute or missing stdlib (rc={rc}) {se[:120]}"
    rc, so, _ = run([path, "-c",
                     "import sys;print('VENV' if sys.prefix!=sys.base_prefix else 'BASE')"])
    if so == "VENV":
        return False, "is a VIRTUALENV - belongs to another project; use a standalone interpreter"
    rc, so, _ = run([path, "-c",
                     "import sqlite3,tempfile,os;d=tempfile.mkdtemp();"
                     "c=sqlite3.connect(os.path.join(d,'t.db'));"
                     "print(c.execute('PRAGMA journal_mode=WAL').fetchone()[0])"])
    if "wal" not in so.lower():
        return False, "sqlite3 cannot enable WAL (fold_logs.py requires it)"
    return True, "ok"


INSTALL_HINT = {
    "python": "uv python install 3.11    # standalone CPython on the user toolchain, NOT a venv",
    "git": "scoop install git",
    "sqlite3": "scoop install sqlite",
    "rtk": "scoop install rtk    # or see token-efficiency/references/install.md",
}


def main():
    as_json = "--json" in sys.argv
    report = {"python": None, "tools": {}, "ok": True, "errors": [], "notes": []}

    # --- Python: the one that matters ---
    chosen = None
    for cand in python_candidates():
        ok, why = verify_python(cand)
        if ok:
            chosen = cand
            break
        report["notes"].append(f"rejected {cand}: {why}")
    if chosen:
        report["python"] = chosen
    else:
        report["ok"] = False
        report["errors"].append(
            "No usable Python found. Every candidate was a Store stub, a venv, or unusable.\n"
            "  Install one globally:  " + INSTALL_HINT["python"])

    # --- The rest of the toolchain: global shims, verified by execution ---
    for tool, probe in (("git", ["--version"]), ("sqlite3", ["-version"]), ("rtk", ["--version"])):
        path = shutil.which(tool)
        if not path:
            report["tools"][tool] = None
            msg = f"{tool} not on PATH. Install globally:  {INSTALL_HINT[tool]}"
            if tool == "rtk":
                report["notes"].append(msg + "   (optional: 60-90% command-output compression)")
            else:
                report["ok"] = False
                report["errors"].append(msg)
            continue
        rc, so, se = run([path, *probe])
        report["tools"][tool] = {"path": path, "version": (so or se).splitlines()[0] if (so or se) else "?"}
        if rc != 0:
            report["ok"] = False
            report["errors"].append(f"{tool} found at {path} but failed to run.")

    if report["tools"].get("rtk"):
        rc, so, se = run(["rtk", "gain"])
        if rc != 0:
            report["notes"].append("`rtk gain` failed - likely the WRONG rtk "
                                   "(Rust Type Kit is a different project).")

    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print("=== preflight ===")
        print(f"python : {report['python'] or 'NONE USABLE'}")
        for t, v in report["tools"].items():
            print(f"{t:7}: {v['path'] + '  ' + v['version'] if v else 'MISSING'}")
        for n in report["notes"]:
            print(f"note   : {n}")
        for e in report["errors"]:
            print(f"ERROR  : {e}")
        print("=== " + ("OK - safe to generate" if report["ok"] else "FAILED - fix the above first") + " ===")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
