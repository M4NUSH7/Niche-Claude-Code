#!/bin/bash
# Xiaoyuzhou podcast transcription script
# Usage: bash transcribe.sh [--polish] <xiaoyuzhou episode URL> [output file path]
# Env var: GROQ_API_KEY (required)
#
# --polish: after transcription, calls Groq Llama 3.3 70B to add Chinese
#           punctuation and reasonable paragraph breaks (Whisper's Chinese
#           punctuation support is weak; this noticeably improves readability)
#
# Requires: ffmpeg, curl, perl, python3 (or py -3 on Windows if python3 is
# the Store alias - invoke this script with bash, e.g. via Git Bash, so the
# python3 on PATH inside that shell is a real interpreter, not the Store alias)

set -e

POLISH=0
while [ $# -gt 0 ]; do
    case "$1" in
        --polish) POLISH=1; shift ;;
        --) shift; break ;;
        -h|--help)
            echo "Usage: bash transcribe.sh [--polish] <xiaoyuzhou episode URL> [output file path]"
            exit 0 ;;
        --*)
            echo "Unknown option: $1" >&2
            exit 1 ;;
        *) break ;;
    esac
done

URL="${1:?Usage: bash transcribe.sh [--polish] <xiaoyuzhou episode URL> [output file path]}"
OUTPUT="${2:-/tmp/podcast_transcript.txt}"
TMPDIR="/tmp/xiaoyuzhou_$$"

# Try env var first, then agent-reach config.yaml (if the full agent-reach
# CLI happens to be installed alongside this skill)
if [ -z "$GROQ_API_KEY" ]; then
    CONFIG_FILE="$HOME/.agent-reach/config.yaml"
    if [ -f "$CONFIG_FILE" ]; then
        GROQ_API_KEY=$(python3 -c "import yaml; print((yaml.safe_load(open('$CONFIG_FILE')) or {}).get('groq_api_key',''))" 2>/dev/null || true)
    fi
fi
GROQ_API_KEY="${GROQ_API_KEY:?Set the GROQ_API_KEY environment variable (free key: https://console.groq.com/keys)}"

# Groq API limit: 25MB per file
MAX_CHUNK_SIZE_MB=20
AUDIO_BITRATE="64k"

cleanup() {
    rm -rf "$TMPDIR"
}
trap cleanup EXIT

mkdir -p "$TMPDIR"

echo "Xiaoyuzhou podcast transcription"
echo "===================="

# Step 1: extract audio URL and title from the episode page
echo "Parsing episode page..."
PAGE=$(curl -s "$URL")
AUDIO_URL=$(echo "$PAGE" | perl -ne 'while (/(https:\/\/media\.xyzcdn\.net\/[^"]*\.(?:m4a|mp3))/gi) { print "$1\n" }' | head -1)
TITLE=$(echo "$PAGE" | perl -ne 'if (/"title":"([^"]*)"/) { print "$1\n"; last }' | head -1)

if [ -z "$AUDIO_URL" ]; then
    echo "Could not extract an audio URL from the page"
    exit 1
fi

echo "Title: $TITLE"
echo "Audio: $AUDIO_URL"

# Step 2: download audio
echo "Downloading audio..."
EXT="${AUDIO_URL##*.}"
curl -sL -o "$TMPDIR/original.$EXT" "$AUDIO_URL"
FILE_SIZE=$(ls -lh "$TMPDIR/original.$EXT" | awk '{print $5}')
echo "File size: $FILE_SIZE"

# Step 3: get duration
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$TMPDIR/original.$EXT" 2>/dev/null | cut -d. -f1)
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))
echo "Duration: ${DURATION_MIN}m ${DURATION_SEC}s"

# Step 4: transcode to low-bitrate mono MP3
echo "Transcoding..."
ffmpeg -y -i "$TMPDIR/original.$EXT" -b:a "$AUDIO_BITRATE" -ac 1 "$TMPDIR/mono.mp3" 2>/dev/null
MONO_SIZE=$(stat -c%s "$TMPDIR/mono.mp3" 2>/dev/null || stat -f%z "$TMPDIR/mono.mp3")
echo "Transcoded size: $(echo "$MONO_SIZE / 1024 / 1024" | bc)MB"

# Step 5: split by size if needed
MAX_BYTES=$((MAX_CHUNK_SIZE_MB * 1024 * 1024))

if [ "$MONO_SIZE" -le "$MAX_BYTES" ]; then
    # No split needed
    cp "$TMPDIR/mono.mp3" "$TMPDIR/chunk_0.mp3"
    NUM_CHUNKS=1
    echo "No split needed"
else
    # Compute number of chunks
    NUM_CHUNKS=$(( (MONO_SIZE / MAX_BYTES) + 1 ))
    CHUNK_DURATION=$(( DURATION / NUM_CHUNKS + 10 ))  # +10s buffer
    echo "Splitting into $NUM_CHUNKS chunks (~$((CHUNK_DURATION / 60)) min each)..."

    for i in $(seq 0 $((NUM_CHUNKS - 1))); do
        START=$((i * CHUNK_DURATION))
        ffmpeg -y -i "$TMPDIR/mono.mp3" -ss "$START" -t "$CHUNK_DURATION" -c copy "$TMPDIR/chunk_${i}.mp3" 2>/dev/null
        CHUNK_SIZE=$(ls -lh "$TMPDIR/chunk_${i}.mp3" | awk '{print $5}')
        echo "   chunk $((i+1))/$NUM_CHUNKS: $CHUNK_SIZE"
    done
fi

# Step 6: transcribe via Groq Whisper API
echo "Transcribing (Groq Whisper large-v3)..."

for i in $(seq 0 $((NUM_CHUNKS - 1))); do
    echo -n "   chunk $((i+1))/$NUM_CHUNKS... "

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        https://api.groq.com/openai/v1/audio/transcriptions \
        -H "Authorization: Bearer $GROQ_API_KEY" \
        -F file="@$TMPDIR/chunk_${i}.mp3" \
        -F model="whisper-large-v3" \
        -F language="zh" \
        -F prompt="This is a Mandarin Chinese podcast recording. Output a transcript with full Chinese punctuation." \
        -F response_format="text")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" != "200" ]; then
        echo "API error (HTTP $HTTP_CODE)"
        echo "$BODY"

        # Back off and retry once on rate limit
        if [ "$HTTP_CODE" = "429" ]; then
            # Extract wait time from the error body, default 2 minutes
            WAIT_SEC=$(echo "$BODY" | perl -ne 'if (/in (\d+)m/) { print "$1\n"; exit }')
            WAIT_SEC=${WAIT_SEC:-2}
            WAIT_SEC=$((WAIT_SEC * 60 + 30))
            echo "   Rate limited, waiting ${WAIT_SEC}s before retry..."
            sleep "$WAIT_SEC"
            RESPONSE=$(curl -s -w "\n%{http_code}" \
                https://api.groq.com/openai/v1/audio/transcriptions \
                -H "Authorization: Bearer $GROQ_API_KEY" \
                -F file="@$TMPDIR/chunk_${i}.mp3" \
                -F model="whisper-large-v3" \
                -F language="zh" \
                -F prompt="This is a Mandarin Chinese podcast recording. Output a transcript with full Chinese punctuation." \
                -F response_format="text")
            HTTP_CODE=$(echo "$RESPONSE" | tail -1)
            BODY=$(echo "$RESPONSE" | sed '$d')

            if [ "$HTTP_CODE" != "200" ]; then
                echo "   Retry failed"
                exit 1
            fi
        else
            exit 1
        fi
    fi

    echo "$BODY" > "$TMPDIR/transcript_${i}.txt"
    CHARS=$(wc -m < "$TMPDIR/transcript_${i}.txt")
    echo "OK ($CHARS chars)"
done

# Step 6.5 (optional): use Llama 3.3 70B to add punctuation/paragraphs
if [ "$POLISH" = "1" ]; then
    echo "Polishing (Llama 3.3 70B adding punctuation + paragraphs)..."
    for i in $(seq 0 $((NUM_CHUNKS - 1))); do
        echo -n "   chunk $((i+1))/$NUM_CHUNKS... "
        IN_FILE="$TMPDIR/transcript_${i}.txt" \
        OUT_FILE="$TMPDIR/polished_${i}.txt" \
        GROQ_API_KEY="$GROQ_API_KEY" \
        python3 <<'PY'
import json, os, sys, urllib.request, urllib.error

KEY = os.environ["GROQ_API_KEY"]
IN = os.environ["IN_FILE"]
OUT = os.environ["OUT_FILE"]

MODEL = "llama-3.3-70b-versatile"
MAX_DEPTH = 3
PROMPT_TMPL = (
    "The following is a raw speech-to-text transcript of a Mandarin Chinese "
    "podcast segment. Because Whisper's Chinese punctuation support is weak, "
    "the text has almost no punctuation. Do exactly one thing: insert Chinese "
    "punctuation at appropriate positions and break into reasonable "
    "paragraphs.\n\n"
    "Strict requirements:\n"
    "- Do not modify, delete, or add any Chinese/English/numeric characters\n"
    "- Do not rewrite, polish for style, or summarize\n"
    "- Do not add any explanation, preamble, or postscript\n"
    "- Output only the full text with punctuation and paragraphs added\n\n"
    "Original text:\n{}"
)

def call_groq(text):
    body = json.dumps({
        "model": MODEL,
        "temperature": 0.2,
        "max_completion_tokens": 8192,
        "messages": [{"role": "user", "content": PROMPT_TMPL.format(text)}],
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            "User-Agent": "agent-reach-xiaoyuzhou/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.load(r)
    return (
        resp["choices"][0]["message"]["content"].strip(),
        resp["choices"][0].get("finish_reason"),
    )

def polish(text, depth=0):
    try:
        out, fr = call_groq(text)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"polish HTTP {e.code}: {e.read().decode(errors='replace')[:200]}\n")
        return text  # fallback to raw
    except Exception as e:
        sys.stderr.write(f"polish error: {e}\n")
        return text
    if fr != "length" or depth >= MAX_DEPTH:
        return out
    # Output was truncated: split in half and recurse
    mid = len(text) // 2
    return polish(text[:mid], depth + 1) + polish(text[mid:], depth + 1)

content = open(IN, encoding="utf-8").read().strip()
result = polish(content)
open(OUT, "w", encoding="utf-8").write(result + "\n")
print(f"OK ({len(result)} chars)")
PY
    done
fi

# Step 7: merge output
echo "Merging transcript..."

{
    echo "# $TITLE"
    echo ""
    echo "Source: $URL"
    echo "Duration: ${DURATION_MIN}m ${DURATION_SEC}s"
    echo "Transcribed: $(date '+%Y-%m-%d %H:%M')"
    if [ "$POLISH" = "1" ]; then
        echo "Polish: Groq Llama 3.3 70B"
    fi
    echo ""
    echo "---"
    echo ""

    for i in $(seq 0 $((NUM_CHUNKS - 1))); do
        if [ "$POLISH" = "1" ] && [ -f "$TMPDIR/polished_${i}.txt" ]; then
            cat "$TMPDIR/polished_${i}.txt"
        else
            cat "$TMPDIR/transcript_${i}.txt"
        fi
        echo ""
    done
} > "$OUTPUT"

TOTAL_CHARS=$(wc -m < "$OUTPUT")
echo ""
echo "Done."
echo "Output: $OUTPUT"
echo "Total chars: $TOTAL_CHARS"
echo "===================="
