# Zero-config channel smoke test for the agent-reach skill (native Windows PowerShell).
# Prints one line per channel: ok / missing / error, with a one-line reason
# or install hint. Run before relying on a channel in a new environment.
#
# Usage: powershell -File check_tools.ps1

Write-Output "agent-reach zero-config channel check"
Write-Output "======================================"

function Test-Cmd {
    param(
        [string]$Label,
        [string]$Exe,
        [string[]]$ProbeArgs,
        [string]$InstallHint
    )
    $found = Get-Command $Exe -ErrorAction SilentlyContinue
    if (-not $found) {
        Write-Output "[$Label] missing - install: $InstallHint"
        return
    }
    try {
        & $Exe @ProbeArgs *> $null
        Write-Output "[$Label] ok"
    } catch {
        Write-Output "[$Label] error - smoke call failed: $($_.Exception.Message)"
    }
}

# curl (web channel - bundled with Windows 10 1803+)
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if ($curl) {
    Write-Output "[web/curl] ok"
} else {
    Write-Output "[web/curl] missing - Windows 10 1803+ ships curl.exe; update Windows or install curl"
}

# yt-dlp (YouTube)
Test-Cmd -Label "youtube/yt-dlp" -Exe "yt-dlp" -ProbeArgs @("--version") -InstallHint "pipx install yt-dlp  (or: py -3 -m pip install yt-dlp)"

# gh (GitHub)
Test-Cmd -Label "github/gh" -Exe "gh" -ProbeArgs @("--version") -InstallHint "https://cli.github.com"

# feedparser (RSS) - use py -3, NOT python3 (python3 on Windows is often the Microsoft Store alias)
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    try {
        & py -3 -c "import feedparser" *> $null
        Write-Output "[rss/feedparser] ok"
    } catch {
        Write-Output "[rss/feedparser] missing - install: py -3 -m pip install feedparser"
    }
} else {
    Write-Output "[rss/feedparser] missing - Python Launcher (py) not found; install Python from python.org, then: py -3 -m pip install feedparser"
}

# mcporter + Exa (semantic search)
$mcporter = Get-Command mcporter -ErrorAction SilentlyContinue
if ($mcporter) {
    Write-Output "[exa/mcporter] ok (tool present; run: mcporter call 'exa.web_search_exa(query: \"test\", numResults: 1)' to verify the Exa MCP registration)"
} else {
    Write-Output "[exa/mcporter] missing - install: npm install -g mcporter ; mcporter config add exa https://mcp.exa.ai/mcp"
}

# V2EX - public API reachability
try {
    $resp = Invoke-WebRequest -Uri "https://www.v2ex.com/api/topics/hot.json" -Headers @{ "User-Agent" = "agent-reach/1.0" } -TimeoutSec 8 -UseBasicParsing
    if ($resp.StatusCode -eq 200) {
        Write-Output "[v2ex/curl] ok"
    } else {
        Write-Output "[v2ex/curl] error - unexpected status $($resp.StatusCode)"
    }
} catch {
    Write-Output "[v2ex/curl] error - public API unreachable (network/firewall issue, no install needed)"
}
