# Optional setup - key/cookie-gated channels

These channels are NOT zero-config. Only walk a user through one of these if
they explicitly ask for that platform. Never ask the user to paste a raw
secret into a place that gets logged or committed; env vars are named here
by NAME ONLY - never put a value in a file, a chat transcript that gets
saved, or a git-tracked location.

Security note from upstream: for cookie/browser-session platforms (Twitter,
XiaoHongShu, Facebook, Instagram), recommend the user use a secondary/
dedicated account rather than their main one - non-browser API calls can
trigger a platform's automation detection, and a cookie grants full account
access if it ever leaks.

## Twitter/X (search, timeline, full tweet/thread reading)

Basic tweet reading already works zero-config through the web channel
(`curl https://r.jina.ai/<tweet URL>`). Search and authenticated reads need
`twitter-cli` plus a cookie.

1. Install: `pipx install twitter-cli` (v0.8.5+)
2. Get a cookie: install the Cookie-Editor browser extension, log into
   x.com, click the extension -> Export -> copy the header string.
3. Set environment variables (names only - fill in locally, never in a
   shared file):
   - `TWITTER_AUTH_TOKEN`
   - `TWITTER_CT0`
   (Some tool versions instead read `AUTH_TOKEN` / `CT0` - check
   `twitter --help` if the first pair doesn't take.)
4. Verify: `twitter search "test" -n 1`

Retry chain if search fails (stop at the first success):
1. Retry once - transient failures are common.
2. `pipx upgrade twitter-cli && twitter search "test" -n 1`
3. Fall back to OpenCLI if the desktop has it and a browser session:
   `opencli twitter search "test" -f yaml`
4. Fall back to stable read-only commands: `twitter feed -n 20`,
   `twitter user-posts @<username> -n 20`

Proxy (only needed on networks that block x.com):
```bash
export HTTP_PROXY="http://user:pass@host:port"
export HTTPS_PROXY="http://user:pass@host:port"
```

## Reddit (no zero-config path - anonymous JSON endpoints are blocked)

Two backend options, both require a logged-in session:

**OpenCLI (desktop, reuses an already-logged-in Chrome session):**
```bash
opencli reddit search "<query>" -f yaml
opencli reddit read <POST_ID> -f yaml
```
Requires Chrome open with the OpenCLI extension installed, and the user
already logged into reddit.com in that browser.

**rdt-cli (server/headless, needs its own login step):**
```bash
pipx install 'git+https://github.com/public-clis/rdt-cli.git'
rdt login    # extracts cookies from a local browser, or prompts for manual cookie entry on a headless box
rdt search "<query>" --limit 10
rdt read <POST_ID>
```

Networks that block Reddit outright (some corporate/regional networks) need
a residential proxy in addition to login - see upstream docs for proxy
env vars if this applies.

## Facebook / Instagram (OpenCLI, desktop only)

Both reuse the user's already-logged-in Chrome session via the OpenCLI
browser extension - there is no server/headless path.

1. Install the OpenCLI Chrome extension from the Chrome Web Store.
2. Verify the extension is connected: `opencli doctor` (look for
   "Extension: connected").
3. Log into facebook.com / instagram.com in that same Chrome profile.
4. Use:
   ```bash
   opencli facebook search "<query>" -f yaml
   opencli facebook profile <username> -f yaml
   opencli facebook groups -f yaml
   opencli instagram search "<query>" -f yaml    # user search, not full-text
   opencli instagram user <username> -f yaml     # a specific user's recent posts
   ```

Facebook Groups only exposes the list/recent-activity of groups the logged-in
account can already see - not arbitrary group posts. Instagram `search` is a
user search, not a keyword search over posts; find the username first, then
call `instagram user`.

## XiaoHongShu (multi-backend)

- **Desktop:** OpenCLI, same browser-session pattern as Facebook/Instagram
  above (`opencli xiaohongshu search "<query>" -f yaml`).
- **Server/headless:** `xiaohongshu-mcp` - QR-code login on first run, then
  MCP calls (`mcporter call 'xiaohongshu.search_feeds(keyword: "<query>")'
  --timeout 120000`). First call downloads a headless browser (~150MB); keep
  the long timeout.

Never read a note by a bare ID - XiaoHongShu enforces an `xsec_token` that
only comes from a search/feed result; always search first, then read the
full URL/ID from that result.

## LinkedIn

```bash
pip install linkedin-scraper-mcp
```

Needs a visible browser to log in once (`linkedin-scraper-mcp --login
--no-headless`), then runs as an MCP server:

```bash
linkedin-scraper-mcp --transport streamable-http --port 8001
mcporter config add linkedin http://localhost:8001/mcp
```

On a headless server, this needs a VNC session for the one-time login. Until
set up, fall back to the zero-config web channel for public LinkedIn pages:

```bash
curl -s "https://r.jina.ai/https://linkedin.com/in/<username>"
```

## Xueqiu (stock quotes, Chinese market)

Needs a cookie from a logged-in xueqiu.com browser session (the anonymous
API returns HTTP 400). No CLI tool - the cookie is consumed directly by the
Xueqiu channel logic if using the full agent-reach install; without it,
fall back to the web channel for public pages.

## Xiaoyuzhou podcast transcription (Whisper via Groq)

Not a platform-read channel - this is audio transcription for podcast
episodes that have no transcript.

Prerequisites:
1. `ffmpeg` on PATH (`brew install ffmpeg` / `apt install ffmpeg` / Windows:
   download from ffmpeg.org and add to PATH).
2. A free Groq API key: https://console.groq.com/keys (no credit card).
3. Set the environment variable (name only): `GROQ_API_KEY`. Optional
   fallback if Groq is rate-limited: `OPENAI_API_KEY`.

Run:
```bash
bash scripts/transcribe_xiaoyuzhou.sh --polish "https://www.xiaoyuzhoufm.com/episode/<EPISODE_ID>"
```

`--polish` runs an extra Groq Llama call to add punctuation/paragraph breaks
to the raw Whisper transcript (Whisper's Chinese punctuation is weak without
it); adds a few seconds per episode, use only when needed.

Verify the key works:
```bash
curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY" -o /dev/null -w "%{http_code}"
# expect 200
```

Free tier: roughly 2 hours of audio per hour, then a 15-minute cooldown -
fine for normal podcast-listening volumes. For episodes over ~2 hours,
process in batches.
