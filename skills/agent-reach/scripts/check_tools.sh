#!/bin/bash
# Zero-config channel smoke test for the agent-reach skill.
# Prints one line per channel: ok / missing / error, with a one-line reason
# or install hint. Run before relying on a channel in a new environment.
#
# Usage: bash check_tools.sh

set -u

check() {
    name="$1"
    cmd="$2"
    install_hint="$3"

    if ! eval "$cmd" >/tmp/agent-reach-check.$$ 2>&1; then
        rc=$?
        if command -v "${name}" >/dev/null 2>&1 || [ "$rc" -ne 127 ]; then
            echo "[$name] error - smoke call failed (see /tmp/agent-reach-check.$$)"
        else
            echo "[$name] missing - install: $install_hint"
        fi
        return
    fi
    echo "[$name] ok"
}

echo "agent-reach zero-config channel check"
echo "======================================"

# curl (web channel - should always be present)
if command -v curl >/dev/null 2>&1; then
    echo "[web/curl] ok"
else
    echo "[web/curl] missing - curl ships with the OS on macOS/Linux/modern Windows; install if absent"
fi

# yt-dlp (YouTube)
check "youtube/yt-dlp" "yt-dlp --version" "pipx install yt-dlp  (or: py -3 -m pip install yt-dlp)"

# gh (GitHub)
check "github/gh" "gh --version" "https://cli.github.com"

# feedparser (RSS) - probe via python3, falling back to py -3 on Windows
if command -v python3 >/dev/null 2>&1 && python3 -c "import feedparser" >/dev/null 2>&1; then
    echo "[rss/feedparser] ok"
elif command -v py >/dev/null 2>&1 && py -3 -c "import feedparser" >/dev/null 2>&1; then
    echo "[rss/feedparser] ok"
else
    echo "[rss/feedparser] missing - install: py -3 -m pip install feedparser  (or python3 -m pip install feedparser)"
fi

# mcporter + Exa (semantic search)
if command -v mcporter >/dev/null 2>&1; then
    echo "[exa/mcporter] ok (tool present; run 'mcporter call exa.web_search_exa(query: \"test\", numResults: 1)' to verify the Exa MCP registration)"
else
    echo "[exa/mcporter] missing - install: npm install -g mcporter && mcporter config add exa https://mcp.exa.ai/mcp"
fi

# V2EX - public API reachability
if curl -sf -m 8 "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0" >/dev/null 2>&1; then
    echo "[v2ex/curl] ok"
else
    echo "[v2ex/curl] error - public API unreachable (network/firewall issue, no install needed)"
fi

rm -f /tmp/agent-reach-check.$$ 2>/dev/null || true
