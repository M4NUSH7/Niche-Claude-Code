---
name: agent-reach
description: >
  Use when the user wants to research a topic, find sources, or search a
  platform by name - web pages, YouTube, GitHub, RSS/Atom feeds, V2EX, or Exa
  semantic search. Also when the user shares a URL from one of these platforms
  and wants it read, summarized, or checked for related content. Routes each
  request to the right zero-config CLI/API (curl+Jina Reader, yt-dlp, gh,
  feedparser, mcporter+Exa, V2EX) so results come back as raw source material,
  not narrowed by one search engine. Pairs with deep-research: use agent-reach
  first to gather from multiple platforms, then hand the material to
  deep-research (or synthesize yourself). NOT for: writing the final
  report/analysis/translation (it only fetches/searches); posting, commenting,
  or any write action; Twitter/X, Reddit, Facebook, Instagram, LinkedIn,
  XiaoHongShu, Xueqiu, or Bilibili unless cookies or a login session are
  already set up (see "Key/cookie-gated channels") - confirm setup first.
allowed-tools: Bash, Read, Grep, Glob, WebFetch, WebSearch
metadata:
  tier: user
  upstream: https://github.com/Panniantong/agent-reach
  upstream_commit: 1494c2ab239e7355a77e7cceaf3271453a1f34b5
---

# Agent Reach - zero-config internet research router

Source-acquisition layer for research: given a query or URL, this skill picks
the right free, no-login tool and runs it. It never wraps or reimplements the
upstream tool - it calls `curl`, `gh`, `yt-dlp`, `feedparser`, or `mcporter`
directly and returns what they return.

**This is a user-tier skill, not a harness component.** It does not pin a
model, run hooks, or require project setup - it works in any repo or none.

## When to use this vs. deep-research

- **agent-reach** = breadth + speed. Fan out across platforms quickly, pull
  raw pages/threads/transcripts/repos, no synthesis.
- **deep-research** = depth + trust. Takes sources (including ones this skill
  gathered), verifies claims adversarially, cites, and writes the report.

For "research X" requests: use agent-reach to gather from 2-4 relevant
platforms in parallel, then either synthesize directly or invoke deep-research
on the combined material if the user wants a rigorous, cited writeup.

## Zero-config channels (no key, no cookie, no login)

These six work immediately if the underlying tool is on PATH. Check once
per session with `scripts/check_tools.sh` (or `.ps1` on Windows) rather than
guessing.

| Platform | Tool | Install if missing |
|----------|------|---------------------|
| Any web page | `curl` + Jina Reader | none (curl is preinstalled everywhere) |
| YouTube | `yt-dlp` | `pipx install yt-dlp` or `py -3 -m pip install yt-dlp` |
| GitHub | `gh` (GitHub CLI) | https://cli.github.com |
| RSS/Atom feeds | Python `feedparser` | `py -3 -m pip install feedparser` |
| V2EX | public JSON API via `curl` | none |
| Web semantic search | `mcporter` + Exa MCP | `npm install -g mcporter && mcporter config add exa https://mcp.exa.ai/mcp` |

Bilibili is intentionally not included: upstream's most reliable path
(`bili-cli`) is a separately-maintained third-party CLI, and full subtitle
extraction needs a login-backed desktop Chrome session (OpenCLI) - neither
is zero-config end to end. See `references/channels.md` for pointers if you
need it later.

Run the smoke test before relying on a channel in a new environment:

```bash
bash scripts/check_tools.sh        # macOS / Linux / Git Bash on Windows
# or
powershell -File scripts/check_tools.ps1   # native Windows shell
```

It prints one line per channel: `ok` (tool responds), `missing` (not on
PATH - install command shown), or `error` (installed but failed the smoke
call, e.g. network down).

### Commands

```bash
# Web page -> clean Markdown (works for almost any URL)
curl -s "https://r.jina.ai/<URL>"

# YouTube - metadata
yt-dlp --dump-json "<URL>"

# YouTube - subtitles (writes .vtt to /tmp, then read it)
yt-dlp --write-sub --write-auto-sub --sub-lang "en" --skip-download -o "/tmp/%(id)s" "<URL>"
cat /tmp/<VIDEO_ID>.*.vtt

# YouTube - search
yt-dlp --dump-json "ytsearch5:<query>"

# GitHub - search repos / code
gh search repos "<query>" --sort stars --limit 10
gh search code "<query>" --language python

# GitHub - read a repo, issue, or PR
gh repo view <owner>/<repo>
gh issue view <number> -R <owner>/<repo>
gh pr view <number> -R <owner>/<repo>

# RSS/Atom feed -> latest entries
py -3 -c "
import feedparser
for e in feedparser.parse('<FEED_URL>').entries[:5]:
    print(f'{e.title} - {e.link}')
"

# V2EX - public JSON API, no auth
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" -H "User-Agent: agent-reach/1.0"
curl -s "https://www.v2ex.com/api/topics/show.json?id=<TOPIC_ID>" -H "User-Agent: agent-reach/1.0"
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=<TOPIC_ID>&page=1" -H "User-Agent: agent-reach/1.0"

# Exa - AI semantic web search / code-context search
mcporter call 'exa.web_search_exa(query: "<query>", numResults: 5)'
mcporter call 'exa.get_code_context_exa(query: "<code question>", tokensNum: 3000)'
```

Full per-channel notes (caveats, retry order, output-format tips): see
`references/channels.md`.

## Windows notes

- Docs upstream say `python3` - on Windows this can silently resolve to the
  Microsoft Store alias instead of a real interpreter (`python3 --version`
  opens the Store, or `where python3` points into
  `...\AppData\Local\Microsoft\WindowsApps\`). Use `py -3` instead, or the
  venv's own `python.exe`.
- The OpenCLI-backed channels (Reddit, Facebook, Instagram, XiaoHongShu
  desktop path) need a real desktop Chrome session with an extension
  installed - they do not work headless or from a cron/scheduled job. Skip
  them in non-interactive contexts; use the zero-config channels above
  instead.
- `gh` and `yt-dlp` are plain executables and work the same on Windows once
  on PATH; no shell-syntax changes needed for the commands above.

## Optional setup: key/cookie-gated channels

Not included in the zero-config set above - only mention these if the user
asks for that specific platform, and confirm they want to do the one-time
setup first. Never ask for or store a credential value yourself; only name
the environment variable and point to the upstream guide.

| Platform | Needs | Env var(s) (names only) | Verify with |
|----------|-------|---------------------------|--------------|
| Twitter/X search/timeline | Cookie export (Cookie-Editor) + `twitter-cli` | `TWITTER_AUTH_TOKEN`, `TWITTER_CT0` | `twitter search "test" -n 1` |
| Reddit | Browser login session (no anonymous API) via OpenCLI, or `rdt-cli` + cookie | none required for OpenCLI path | `rdt search "test" --limit 1` or `opencli reddit search "test" -f yaml` |
| Facebook / Instagram | Desktop Chrome + OpenCLI extension, logged in | none (reuses browser session) | `opencli facebook search "test" -f yaml` |
| XiaoHongShu | Desktop Chrome + OpenCLI, or server QR login via `xiaohongshu-mcp` | none (OpenCLI); QR for server | `opencli xiaohongshu search "test" -f yaml` |
| LinkedIn | `linkedin-scraper-mcp` login session | none | `mcporter call 'linkedin.get_person_profile(linkedin_url: "https://linkedin.com/in/test")'` |
| Xueqiu (stocks) | Browser cookie from a logged-in xueqiu.com session | none | see upstream `docs/troubleshooting.md` equivalent (Xueqiu section) |
| Xiaoyuzhou podcast transcription | `ffmpeg` + free Groq API key | `GROQ_API_KEY` (fallback `OPENAI_API_KEY`) | `curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY" -o /dev/null -w "%{http_code}"` (expect `200`) |

Setup guidance for each (where to get a free key, how to export a cookie,
what the retry chain looks like) is in `references/key-cookie-setup.md`.
The Xiaoyuzhou transcription script itself is bundled at
`scripts/transcribe_xiaoyuzhou.sh` (requires `ffmpeg` and `GROQ_API_KEY`).

## Workspace rules

Never write output files into the user's project/workspace directory. Use
`/tmp/` (or the OS temp dir on Windows) for transient output such as
downloaded subtitles or transcripts.

## Standing rules

1. **Announce the route**: say "using agent-reach, platform X via tool Y"
   before running a command, so the user can see which backend served the
   request.
2. **Combine platforms for broad research**: e.g. Exa for general web +
   GitHub for code + YouTube for tutorials + V2EX for Chinese-language
   tech-community perspectives - gather in parallel, then synthesize (or
   hand off to deep-research).
3. **On failure, check `references/channels.md` for that channel's retry
   order** before giving up or guessing a different command.
4. **Do not attempt key/cookie-gated channels** unless the user confirms
   they already completed that channel's one-time setup.
