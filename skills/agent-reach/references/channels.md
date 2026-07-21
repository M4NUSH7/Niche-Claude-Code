# Channel reference - zero-config platforms

Detailed commands, caveats, and retry chains for each zero-config channel.
Translated and adapted from the upstream agent-reach reference docs
(originally Chinese-only); commands are unchanged, notes are in English.

## Web pages (Jina Reader)

```bash
curl -s "https://r.jina.ai/<URL>"
```

Works for almost any public web page - returns clean Markdown. No API key,
no rate-limit registration. This is the default fallback for any URL that
does not match a more specific channel below.

If you need finer control over output format (retain images, plain text
instead of Markdown) and have `mcporter` with a web-reader MCP configured:

```bash
mcporter call 'web-reader.webReader(url: "<URL>")'
mcporter call 'web-reader.webReader(url: "<URL>", retain_images: true)'
mcporter call 'web-reader.webReader(url: "<URL>", return_format: "text")'
```

This is optional - the plain `curl` form above covers most cases.

## YouTube (yt-dlp)

Metadata:

```bash
yt-dlp --dump-json "<URL>"
```

Subtitles (downloads only the subtitle track, not the video):

```bash
yt-dlp --write-sub --write-auto-sub --sub-lang "en" --skip-download -o "/tmp/%(id)s" "<URL>"
cat /tmp/<VIDEO_ID>.*.vtt
```

Comments (best-effort, scraped from the web page - not the YouTube Data API,
so some comments may be missing):

```bash
yt-dlp --write-comments --skip-download --write-info-json \
  --extractor-args "youtube:max_comments=20" \
  -o "/tmp/%(id)s" "<URL>"
# Comments land in the "comments" field of the .info.json file
```

Search:

```bash
yt-dlp --dump-json "ytsearch5:<query>"
```

Notes:
- Manually uploaded subtitles extract reliably; auto-generated subtitles can
  contain duplicated lines across cue boundaries and may need post-processing.
- If a video has no subtitles at all, the only fallback is audio
  transcription (Whisper via a free Groq key) - this needs the
  key/cookie-gated setup in `references/key-cookie-setup.md`; it is not
  zero-config.

## GitHub (gh CLI)

```bash
# Auth (optional - unlocks higher rate limits and private repos)
gh auth login
gh auth status

# Search
gh search repos "<query>" --sort stars --limit 10
gh search code "<query>" --language python

# Repos
gh repo view <owner>/<repo>
gh repo clone <owner>/<repo>

# Issues
gh issue list -R <owner>/<repo> --state open
gh issue view <number> -R <owner>/<repo>

# Pull requests
gh pr list -R <owner>/<repo> --state open
gh pr view <number> -R <owner>/<repo>

# Actions / CI
gh run list --repo <owner>/<repo> --limit 10
gh run view <run-id> --repo <owner>/<repo> --log-failed

# Releases
gh release list -R <owner>/<repo>

# Raw API
gh api /user
gh api repos/<owner>/<repo>

# JSON output (for filtering with --jq)
gh issue list --repo <owner>/<repo> --json number,title --jq '.[] | "\(.number): \(.title)"'
```

Public repos are readable and searchable with zero setup. `gh auth login`
unlocks fork/issue/PR write operations and raises rate limits - only run it
if the user asks for those.

## RSS / Atom feeds (feedparser)

```python
py -3 -c "
import feedparser
for e in feedparser.parse('<FEED_URL>').entries[:5]:
    print(f'{e.title} - {e.link}')
"
```

Use for blogs, news sources, and podcast feeds that expose an RSS/Atom URL.
Requires `feedparser` (`py -3 -m pip install feedparser` if missing) - no
key, no login.

## Bilibili - out of scope for this skill

Not ported. Upstream's most reliable path (`bili-cli`) is a third-party CLI
that needs a separate install, and full subtitle extraction needs a desktop
Chrome session via OpenCLI (login-backed, not zero-config); yt-dlp itself
is blocked by Bilibili with HTTP 412. None of that is zero-config end to
end, so it is excluded from this staged skill. If needed later, see the
upstream project's `agent_reach/skill/references/video.md` (Chinese) or
`docs/README_en.md` "Supported Platforms" table for the current tool
choice.

## V2EX (public JSON API)

No authentication needed - direct calls to the public API.

```bash
# Hot topics
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"

# Node topics (node_name examples: python, tech, jobs, qna, programmers)
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" -H "User-Agent: agent-reach/1.0"

# Topic detail (topic_id from URL https://www.v2ex.com/t/<id>)
curl -s "https://www.v2ex.com/api/topics/show.json?id=<TOPIC_ID>" -H "User-Agent: agent-reach/1.0"

# Topic replies
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=<TOPIC_ID>&page=1" -H "User-Agent: agent-reach/1.0"

# User profile
curl -s "https://www.v2ex.com/api/members/show.json?username=<USERNAME>" -H "User-Agent: agent-reach/1.0"
```

Node list: https://www.v2ex.com/planes

Note: V2EX's public API has no full-text search endpoint. For keyword
search, use Exa with `site:v2ex.com`, or fetch
`https://www.v2ex.com/?q=<query>` through the web channel (Jina Reader).

## Exa (semantic web/code search via mcporter)

```bash
mcporter call 'exa.web_search_exa(query: "<query>", numResults: 5)'
mcporter call 'exa.get_code_context_exa(query: "<code question>", tokensNum: 3000)'
```

Free, no API key - Exa's MCP endpoint (`https://mcp.exa.ai/mcp`) is public.
One-time setup if `mcporter` or the `exa` MCP registration is missing:

```bash
npm install -g mcporter
mcporter config add exa https://mcp.exa.ai/mcp
```

Verify:

```bash
mcporter call 'exa.web_search_exa(query: "test", numResults: 1)'
```

Strong for English-language and technical/code content. Also usable as a
search fallback for platforms without a public search API (e.g. V2EX,
Reddit) via `includeDomains`:

```bash
mcporter call 'exa.web_search_exa(query: "<query>", numResults: 5, includeDomains: ["reddit.com"])'
```

## Choosing a tool for a given need

| Need | Tool |
|------|------|
| General web page | Jina Reader (`curl r.jina.ai`) |
| Need image retention / output format control | web-reader MCP |
| Blog/news/podcast feed | feedparser |
| English/technical/code search | Exa |
| Repo/code search | gh CLI |
| Video subtitles (YouTube) | yt-dlp |
| Chinese tech-forum discussion | V2EX public API |
