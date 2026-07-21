#!/usr/bin/env python3
"""Harvest `ponytail:` deferral comments into a markdown debt ledger.

Mechanizes commands/ponytail-debt.md. Walks a tree, skips .git/node_modules/
target/.scratch, finds comment markers matching (#|//) ponytail: <text>, and
prints one markdown table row per hit: file:line, the deferral text, and a
no-trigger flag when the comment names no upgrade path (no comma).

Usage: python harvest_debt.py [path]   (default path: .)

Stdlib only. Reads and prints, changes nothing.
"""
import os
import re
import sys

SKIP_DIRS = {".git", "node_modules", "target", ".scratch"}
# A real debt marker is a code comment whose opener is immediately followed by
# `ponytail:` - `# ponytail: ...`, `// ponytail: ...`, `-- ponytail: ...`.
# Requiring the token to be adjacent to the opener (<=1 space) avoids matching
# the literal "ponytail:" buried in prose or Markdown headings, e.g.
# "# ponytail: markers" written as documentation about the marker itself.
MARKER_RE = re.compile(r"(?:#|//|--|;)[ \t]?ponytail:[ \t]*(.+)", re.IGNORECASE)
# Markdown ATX headings start with 1-6 '#' then a space - never a code comment.
MD_HEADING_RE = re.compile(r"^\s*#{1,6}\s")

# Text-like extensions worth scanning; skip binaries by extension allowlist
# kept intentionally short and simple (YAGNI: extend if a project needs it).
SKIP_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".exe", ".dll",
    ".so", ".pyc", ".lock",
}


def find_markers(root):
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SKIP_EXT:
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, start=1):
                        # A Markdown heading line is prose, not a code comment -
                        # skip it so documentation about the marker never counts.
                        if MD_HEADING_RE.match(line):
                            continue
                        m = MARKER_RE.search(line)
                        if not m:
                            continue
                        # Skip markers shown as inline-code examples in prose:
                        # a backtick anywhere before the marker means it is
                        # documentation of the syntax (e.g. "use `# ponytail: X`"),
                        # not a real deferral comment. Real code comments have no
                        # backtick preceding the opener on the line.
                        if "`" in line[: m.start()]:
                            continue
                        text = m.group(1).strip().rstrip("`)")
                        rows.append((path, lineno, text))
            except (OSError, UnicodeDecodeError):
                continue
    return rows


def render_table(rows, root):
    if not rows:
        print("No ponytail: debt. Clean ledger.")
        return
    print("| file:line | deferral | no-trigger |")
    print("|---|---|---|")
    no_trigger = 0
    for path, lineno, text in rows:
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        has_trigger = "," in text
        flag = "" if has_trigger else "no-trigger"
        if not has_trigger:
            no_trigger += 1
        cell = text.replace("|", "\\|")
        print(f"| {rel}:{lineno} | {cell} | {flag} |")
    print()
    print(f"{len(rows)} markers, {no_trigger} with no trigger.")


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    rows = find_markers(root)
    render_table(rows, root)


if __name__ == "__main__":
    main()
