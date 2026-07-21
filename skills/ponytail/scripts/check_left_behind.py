#!/usr/bin/env python3
"""Assert a non-trivial change left at least one runnable check behind.

Mechanizes ponytail's own rule (SKILL.md, "Lazy code without its check is
unfinished"): non-trivial logic needs ONE runnable check nearby - a
test_*.py / *_test.py / *.test.* file, or a __main__/demo() self-check in the
changed file itself.

Usage: python check_left_behind.py <path>
  <path> - a changed file or a directory of changed files.

Exit 0 with a short OK message if a check is found nearby.
Exit 1 with a message naming what's missing if none is found.

Stdlib only. Deliberately simple: this is a nearby-file heuristic, not a
coverage tool - false negatives are expected for unconventional layouts,
that's the ceiling. ponytail: heuristic only, tighten if false positives pile up.
"""
import os
import sys

TEST_PATTERNS = ("test_", "_test.", ".test.", "spec_", "_spec.", ".spec.")
SKIP_DIRS = {".git", "node_modules", "target", ".scratch"}


def has_self_check(path):
    """A file with __main__ or demo() is its own check."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return False
    return "__main__" in text or "def demo(" in text or "assert " in text


def looks_like_test(fname):
    lower = fname.lower()
    return any(p in lower for p in TEST_PATTERNS)


def find_nearby_check(target_dir):
    for dirpath, dirnames, filenames in os.walk(target_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if looks_like_test(fname):
                return os.path.join(dirpath, fname)
    return None


def main():
    if len(sys.argv) < 2:
        print("usage: check_left_behind.py <changed-path>")
        sys.exit(2)

    target = sys.argv[1]
    if not os.path.exists(target):
        print(f"no check found: path does not exist: {target}")
        sys.exit(1)

    if os.path.isfile(target):
        if has_self_check(target):
            print(f"OK: self-check present in {target}")
            sys.exit(0)
        search_dir = os.path.dirname(os.path.abspath(target)) or "."
    else:
        search_dir = target

    hit = find_nearby_check(search_dir)
    if hit:
        print(f"OK: found check {hit}")
        sys.exit(0)

    print(
        "no check found: no test_*/*_test/*.spec file nearby and no "
        "__main__/demo()/assert self-check in the changed file. "
        "Leave one runnable check behind before closing out."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
