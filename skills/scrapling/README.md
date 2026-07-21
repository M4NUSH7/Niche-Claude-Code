# scrapling

**Scrape the web with anti-bot bypass, stealth browsing, spiders, and adaptive parsing.**

## What it does

Wraps the [Scrapling](https://github.com/D4Vinci/Scrapling) Python library (this is the library author's own agent-skill, repackaged for install). It handles everything from a single request to a full concurrent crawl:

- **Fetchers** that bypass anti-bot systems (Cloudflare Turnstile) out of the box - `Fetcher` (HTTP), `DynamicFetcher` (full browser automation), `StealthyFetcher` (stealth headless).
- **Adaptive parser** that relocates your selected elements when a page's structure changes.
- **Spider framework** - concurrent multi-session crawls with pause/resume and automatic proxy rotation.
- **CLI** (`scrapling extract get/fetch/stealthy-fetch`) for no-code extraction straight to Markdown/HTML/text, with CSS selectors.

## Why it works

`web_fetch` and plain `curl` fail on modern, protected sites - JS-rendered content, Cloudflare, anti-bot fingerprinting. Scrapling escalates gracefully: try `get` (fast HTTP), then `fetch` (browser), then `stealthy-fetch` (anti-bot) - same speed, more capability. The adaptive parser means a scraper does not silently break the next time the site ships a redesign. Use `--ai-targeted` on CLI commands to sanitize hidden elements and protect against prompt injection.

## How to use

Fires when asked to scrape/crawl/extract from websites, when `web_fetch` fails, when a site has anti-bot protection, or to write Python scrapers/spiders.

Install (cross-platform, verified): `uv tool install "scrapling[all]"` then `scrapling install` (fetches browser binaries). Scrapling is a pip library - scoop only installs the python/uv toolchain, not Scrapling itself.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | CLI + code overview, escalation guidance, guardrails |
| `references/fetching/*.md` | static / dynamic / stealthy fetching + choosing between them |
| `references/parsing/*.md` | selection, adaptive parsing, main classes |
| `references/spiders/*.md` | spider architecture, sessions, proxy rotation, templates |
| `references/integrations/scrapy.md` | using Scrapling's parser inside Scrapy |
| `references/migrating_from_beautifulsoup.md` | API comparison |
| `examples/*.py` | runnable fetcher/dynamic/stealthy/spider examples |

## Guardrails

Only scrape content you are authorized to access; respect robots.txt and ToS (`robots_txt_obey = True`); do not bypass paywalls/auth without permission; never scrape personal/sensitive data.

---

**Related:** a point tool; when you need to research across platforms rather than scrape one site, see [agent-reach](../agent-reach/). See the [root README](../../README.md) for how the skills interlock and navigate.
