# agent-reach

**Zero-config internet research router - given a query or URL, pick the right free tool and run it.**

## What it does

A source-acquisition layer for research. Given a query or a URL, it routes to the right free, no-login tool and returns the raw result - it never wraps or reimplements the tool, it calls it directly.

Six zero-config channels (no key, no cookie, no login):

| Platform | Tool |
|---|---|
| Any web page | `curl` + Jina Reader (URL -> clean Markdown) |
| YouTube | `yt-dlp` (metadata, subtitles, search) |
| GitHub | `gh` (repo/code/issue/PR search + read) |
| RSS/Atom | Python `feedparser` |
| V2EX | public JSON API via `curl` |
| Web semantic search | `mcporter` + Exa MCP |

Key/cookie-gated channels (Twitter/X, Reddit, etc.) are documented as optional setup with environment-variable **names only** - never values.

## Why it works

One search engine narrows results to what it indexes and ranks. Fanning out across purpose-built tools per platform returns broader, rawer source material - and returning the tool's own output (not a summary) preserves everything for downstream synthesis. It pairs with `deep-research`: agent-reach supplies breadth and fast per-platform retrieval; deep-research verifies, cross-checks, and writes the cited report.

## How to use

Say "research X", "find sources on Y", "search YouTube/GitHub/RSS for Z", or share a URL from a supported platform. It is a user-tier skill - no model pinning, no hooks, no project setup. It only fetches/searches; it does not synthesize (hand the gathered material to deep-research or synthesize yourself).

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The channels, commands, and the deep-research pairing |
| `references/channels.md` | Per-channel commands, caveats, retry order |
| `references/key-cookie-setup.md` | Optional gated channels (env-var names only) |
| `scripts/check_tools.sh` | Smoke-test which channels are ready in this environment |
| `scripts/transcribe_xiaoyuzhou.sh` | Optional podcast transcription (needs a Whisper key) |

## Cowork edition

The `-cowork` variant drops the Windows PowerShell smoke script and uses `python3`/Linux paths for the Cowork sandbox.
