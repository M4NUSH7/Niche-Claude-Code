#!/usr/bin/env bash
# Advisory complexity/duplication spine check via lizard.
# Not a hard fail: if lizard isn't installed, print the setup hint and exit 0.
#
# Usage: scripts/check.sh [path ...]   (default path: .)

set -u

if ! command -v lizard >/dev/null 2>&1; then
    echo "lizard not installed - run: pip install lizard"
    exit 0
fi

targets=("$@")
if [ "${#targets[@]}" -eq 0 ]; then
    targets=(".")
fi

lizard -C 15 -L 60 -a 5 -Eduplicate -w "${targets[@]}"
