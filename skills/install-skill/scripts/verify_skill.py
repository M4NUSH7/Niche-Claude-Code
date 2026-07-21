#!/usr/bin/env python3
"""Verify (and optionally fix/package) a skill directory.

Usage:
  python3 verify_skill.py <skill-dir> [--fix] [--package [OUT.skill]] [--allow-unicode] [--audit]

Checks: frontmatter, name/folder match, referenced paths, ASCII policy,
script syntax, trailing-newline (truncation symptom).
--fix: auto-fix mechanical items only (unicode replacement, trailing newline).
--package: build <name>.skill zip next to the skill dir (or at OUT path).
--audit: context-cost report (tier tokens, orphans, duplicates, prune candidates).
Exit code 0 = all checks pass.
"""
import os, re, sys, glob, subprocess, zipfile, tempfile

# Never crash while REPORTING. On Windows the default stdout is cp1252, so
# printing a finding that quotes a non-ASCII byte (the very thing we flag) would
# raise UnicodeEncodeError and abort the whole run. Force UTF-8 with a safe
# fallback so the tool always finishes and prints its verdict.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except (AttributeError, ValueError):
    pass

# Keys use \uXXXX escapes so this file is pure ASCII and safe to run --fix on itself.
REPL = {
    "\u2705": "[OK]", "\u274c": "[FAIL]", "\u26a0\ufe0f": "WARNING:", "\u26a0": "WARNING:",
    "\u2713": "OK", "\u2192": "->", "\u2190": "<-", "\ufe0f": "", "\u2014": "-", "\u2013": "-",
    "\u2550": "=", "\u2022": "*", "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u2026": "...", "\u251c": "+", "\u2514": "+", "\u2502": "|", "\u2500": "-",
    "\u00a7": "section ",
}
TEXT_EXT = {".md", ".sh", ".sql", ".py", ".txt", ".yaml", ".yml", ".json"}

def text_files(root):
    for p in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        if os.path.isfile(p) and os.path.splitext(p)[1].lower() in TEXT_EXT:
            yield p


PRUNE_NAMES = {"contributing.md","changelog.md","security.md","code_of_conduct.md",
               "release-please-config.json",".gitkeep"}

def audit(root):
    """Context-cost audit. Tokens estimated as chars/4. Never modifies files."""
    est=lambda p: os.path.getsize(p)//4
    skill_md=os.path.join(root,"SKILL.md")
    all_md=[p for p in glob.glob(os.path.join(root,"**","*.md"),recursive=True)]
    routing=" ".join(open(p,encoding="utf-8",errors="replace").read() for p in all_md)
    desc=""
    t=open(skill_md,encoding="utf-8").read()
    m=re.search(r"^description:\s*(.+?)$",t.split("---",2)[1],re.M|re.S)
    if m: desc=m.group(1)
    print(f"== tier costs (est. tokens) ==")
    print(f"description (EVERY session): {len(desc)//4}")
    print(f"SKILL.md body (every trigger): {est(skill_md)-len(desc)//4}")
    refs=sorted(glob.glob(os.path.join(root,"references","*")))
    for p in refs:
        n=est(p); toc="" 
        body=open(p,encoding="utf-8",errors="replace").read()
        if body.count("\n")>300 and not re.search(r"contents|^## ",body[:500],re.I|re.M): toc="  [>300 lines, consider TOC]"
        print(f"reference {os.path.basename(p)} (on read): {n}{toc}")
    zero=[d for d in ("scripts","bin","assets","templates") if os.path.isdir(os.path.join(root,d))]
    if zero: print("zero-context tiers (never loaded):",", ".join(zero))
    # orphans: no inbound mention anywhere (dir mention covers children)
    print("== orphans / prune candidates ==")
    hits=0
    for p in glob.glob(os.path.join(root,"**","*"),recursive=True):
        if not os.path.isfile(p): continue
        rel=os.path.relpath(p,root).replace(os.sep,"/")
        if rel=="SKILL.md" or rel.split("/")[0] in ("bin",): continue
        base=os.path.basename(rel).lower()
        if base in PRUNE_NAMES or re.match(r"readme_[a-z]{2}\.md$",base):
            print(f"PRUNE-CANDIDATE (upstream meta / non-English): {rel}"); hits+=1; continue
        mentioned = rel in routing or any((d+"/") in routing for d in [os.path.dirname(rel)] if d)
        if not mentioned and rel.endswith(".md"):
            print(f"ORPHAN (no inbound pointer): {rel}"); hits+=1
    if not hits: print("none")
    # cross-file duplicate paragraphs
    print("== duplicate paragraphs across files ==")
    seen={}; dups=0
    for p in all_md:
        body=open(p,encoding="utf-8",errors="replace").read()
        for para in body.split("\n\n"):
            key=re.sub(r"\s+"," ",para).strip().lower()
            if len(key)<80: continue
            if key in seen and seen[key]!=p:
                print(f"DUP: {os.path.relpath(seen[key],root)} <-> {os.path.relpath(p,root)}: \"{key[:60]}...\""); dups+=1
            else: seen[key]=p
    if not dups: print("none")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    root = args[0].rstrip("/\\")
    fix = "--fix" in args
    allow_unicode = "--allow-unicode" in args
    package = "--package" in args
    out = None
    if package:
        i = args.index("--package")
        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            out = args[i + 1]
    failures = []
    warnings = []
    if "--audit" in args:
        audit(root); sys.exit(0)

    # 1. frontmatter
    skill_md = os.path.join(root, "SKILL.md")
    if not os.path.isfile(skill_md):
        print("[FAIL] no SKILL.md"); sys.exit(1)
    t = open(skill_md, encoding="utf-8").read()
    name = None
    if not t.startswith("---"):
        failures.append("SKILL.md: no frontmatter")
    else:
        fm = t.split("---", 2)[1]
        m_name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
        m_desc = re.search(r"^description:", fm, re.M)
        if not m_name: failures.append("frontmatter: missing name")
        if not m_desc: failures.append("frontmatter: missing description")
        if m_name:
            name = m_name.group(1)
            if name != os.path.basename(root):
                failures.append(f"name '{name}' != folder '{os.path.basename(root)}'")

    # 2. referenced paths exist
    refs = set(re.findall(r"`((?:references|scripts|templates|bin|modules|assets)/[\w./ -]+?)`", t))
    for r in refs:
        if not os.path.exists(os.path.join(root, r)):
            failures.append(f"referenced path missing: {r}")

    # 3. ASCII policy + 4. trailing newline
    for f in text_files(root):
        s = open(f, encoding="utf-8", errors="replace").read()
        changed = False
        if not allow_unicode:
            for k, v in REPL.items():
                if k in s: s = s.replace(k, v); changed = True
            rest = set(re.findall(r"[^\x00-\x7F]", s))
            if rest and fix:
                s = re.sub(r"[^\x00-\x7F]", "", s); changed = True; rest = set()
            if rest:
                failures.append(f"non-ascii in {os.path.relpath(f, root)}: {sorted(rest)[:8]}")
        if s and not s.endswith("\n"):
            if fix:
                s += "\n"; changed = True
                print(f"[WARN] missing trailing newline in {os.path.relpath(f, root)} - POSSIBLE TRUNCATION, verify the file tail is complete before trusting this fix")
            else: failures.append(f"no trailing newline (truncation?): {os.path.relpath(f, root)}")
        if changed and fix:
            open(f, "w", encoding="utf-8").write(s)
            print(f"[fixed] {os.path.relpath(f, root)}")
        elif changed and not fix:
            failures.append(f"unicode needs --fix: {os.path.relpath(f, root)}")

    # 5. script syntax
    # Find a bash that actually launches. Some Windows shims (Git/WSL relay) resolve
    # as `bash` on PATH but error `execvpe(/bin/bash) failed` on ANY script - that is
    # an environment defect, not a script syntax error. Probe with a trivial script;
    # if no working bash exists, WARN (do not FAIL) so real syntax errors still gate
    # while a broken shim does not block a valid package.
    def _find_working_bash():
        cands = ["bash"]
        for p in (r"C:\Program Files\Git\bin\bash.exe",
                  r"C:\Program Files\Git\usr\bin\bash.exe",
                  "/usr/bin/bash", "/bin/bash"):
            if p not in cands:
                cands.append(p)
        probe = os.path.join(tempfile.gettempdir(), "_vs_bashprobe.sh")
        try:
            open(probe, "w").write("echo ok\n")
        except OSError:
            probe = None
        for b in cands:
            try:
                if probe:
                    r = subprocess.run([b, "-n", probe], capture_output=True)
                    if r.returncode == 0:
                        return b
            except (OSError, FileNotFoundError):
                continue
        return None
    sh_files = glob.glob(os.path.join(root, "scripts", "*.sh"))
    if sh_files:
        _bash = _find_working_bash()
        if _bash is None:
            warnings.append("no working bash found (broken/absent shim) - skipped .sh syntax checks")
        else:
            for f in sh_files:
                r = subprocess.run([_bash, "-n", f], capture_output=True)
                if r.returncode != 0:
                    failures.append(f"bash -n failed: {os.path.basename(f)}: {r.stderr.decode()[:120]}")
    for f in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
        try:
            compile(open(f, encoding="utf-8").read(), f, "exec")
        except SyntaxError as e:
            failures.append(f"python syntax: {os.path.relpath(f, root)}: {e}")
    for f in glob.glob(os.path.join(root, "scripts", "*.sql")):
        try:
            import sqlite3
            sqlite3.connect(":memory:").executescript(open(f, encoding="utf-8").read())
        except Exception as e:
            failures.append(f"sql failed: {os.path.basename(f)}: {e}")

    # report
    for x in warnings: print("[WARN]", x)
    for x in failures: print("[FAIL]", x)
    print("PASS" if not failures else f"{len(failures)} failure(s)")

    # 6. package
    if package and not failures:
        out = out or os.path.join(os.path.dirname(root), (name or os.path.basename(root)) + ".skill")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for r2, _, files in os.walk(root):
                for fn in files:
                    p = os.path.join(r2, fn)
                    arc = os.path.join(os.path.basename(root), os.path.relpath(p, root))
                    # Preserve/force an exec bit for bundled binaries and shell scripts so
                    # they are runnable on extraction in a Linux sandbox (Cowork). Windows
                    # zip creation drops Unix perms; without this a bundled bin/rtk lands as
                    # 0o644 and needs a manual chmod. arc uses '/' inside the zip regardless of OS.
                    arc_posix = arc.replace(os.sep, "/")
                    is_exec = ("/bin/" in "/" + arc_posix) or arc_posix.endswith(".sh")
                    zi = zipfile.ZipInfo.from_file(p, arc_posix)
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    mode = 0o755 if is_exec else 0o644
                    zi.external_attr = (mode & 0xFFFF) << 16
                    with open(p, "rb") as fh:
                        z.writestr(zi, fh.read())
        print("packaged:", out, f"({os.path.getsize(out)//1024} KB)")
    sys.exit(0 if not failures else 1)

if __name__ == "__main__":
    main()
