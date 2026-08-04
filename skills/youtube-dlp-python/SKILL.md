---
name: youtube-dlp-python
description: |
  Download YouTube video transcripts (subtitles/captions) using yt-dlp, with faster-whisper as fallback for local transcription.
  Supports manual subtitles, auto-generated captions, and Whisper transcription when the subtitle API is blocked.
  Optionally fetches YouTube comments (top/most-recent sorted) via yt-dlp.

  Triggers when user mentions:
  - Provides a YouTube URL and wants the transcript
  - "download transcript" or "get captions/subtitles" from a YouTube video
author: Jansen Lin
license: MIT
allowed-tools: Bash,Read,Write
---

# YouTube Transcript Downloader

Download transcripts (subtitles/captions) from YouTube videos. Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) as the primary tool for subtitle retrieval, with [faster-whisper](https://github.com/SYSTRAN/faster-whisper) as fallback for local transcription when the subtitle API is blocked or no subtitles exist.

## Design Philosophy

Always try yt-dlp subtitles first — they are instant and free. Only fall back to faster-whisper when:

- Subtitle API returns HTTP 429/403 (common on cloud/VPS/datacenter IPs)
- No subtitles exist for the video (e.g. very old content)

yt-dlp handles subtitles via YouTube's timedtext API. faster-whisper downloads the audio track and transcribes locally on CPU — slower but reliable.

## Pre-Check

### yt-dlp

**IMPORTANT: Follow these steps IN ORDER. Do NOT install until all PATH resolution steps have been tried.**

#### Step 1: Check if yt-dlp is in PATH

```bash
which yt-dlp || command -v yt-dlp
```

If found → skip to [faster-whisper](#faster-whisper).

#### Step 2: Reload shell environment and re-check (macOS)

On macOS, VS Code's terminal may not auto-load `~/.zshrc`, so environment variables (like PATH additions for `~/.venv`) are missing. **Always try this before checking other paths:**

```bash
source ~/.zshrc && which yt-dlp
```

If found → skip to [faster-whisper](#faster-whisper).

#### Step 3: Check if yt-dlp exists in ~/.venv

```bash
test -f ~/.venv/bin/yt-dlp && echo "found"
```

If found → add to PATH for this session:

```bash
export PATH="$HOME/.venv/bin:$PATH"
```

#### Step 4: Only install if Steps 1-3 all failed

```bash
~/.venv/bin/pip install -U "yt-dlp[default]"
export PATH="$HOME/.venv/bin:$PATH"
```

### faster-whisper

faster-whisper is needed for the [Audio + Whisper fallback](#fallback-subtitle-api-blocked-http-429) path. Verify it before attempting the fallback.

#### Step 1: Check if faster-whisper is importable

```bash
python3 -c "from faster_whisper import WhisperModel; print('ready')"
```

If ready → skip to [Usage](#usage).

#### Step 2: Check in ~/.venv

```bash
~/.venv/bin/python3 -c "from faster_whisper import WhisperModel; print('ready')"
```

If ready in ~/.venv → activate the venv:

```bash
source ~/.venv/bin/activate
```

#### Step 3: Only install if Steps 1-2 both failed

```bash
~/.venv/bin/pip install faster-whisper
```

This also installs PyAV (`av`) automatically as a dependency. Verify after:

```bash
~/.venv/bin/python3 -c "from faster_whisper import WhisperModel; import av; print('ready')"
```

## Usage

### Check Available Subtitles

**ALWAYS do this first** before attempting to download:

```bash
yt-dlp --list-subs "YOUTUBE_URL"
```

### Get Video Title and Channel

Use the video title and channel name to build the output filename:

```bash
TITLE=$(yt-dlp --get-title "YOUTUBE_URL" | sed 's/[/:*?"<>|]/-/g')
CHANNEL=$(yt-dlp --print channel "YOUTUBE_URL" | sed 's/^NA$//')
```

### Derive Snake Case Filename

Convert the channel and title to snake_case (removing special characters like `.` `,` `'`, preserving unicode), then combine as `Youtube-<channel>-<title>`:

```bash
snake_case() {
  echo "$1" | sed 's/[^[:alnum:]]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//'
}
CHANNEL_SNAKE=$(snake_case "$CHANNEL")
SNAKE_TITLE=$(snake_case "$TITLE")
OUTPUT_MD="Youtube-${CHANNEL_SNAKE:+$CHANNEL_SNAKE-}$SNAKE_TITLE.md"
```

Example: channel `EO`, title `From Writing Code to Managing Agents. Most Engineers Aren't Ready - Stanford University, Mihail Eric` becomes `Youtube-EO-From_Writing_Code_to_Managing_Agents_Most_Engineers_Arent_Ready_Stanford_University_Mihail_Eric.md`

### Download Manual Subtitles (Preferred)

Highest quality, human-created:

```bash
yt-dlp --write-sub --sub-langs en --skip-download --output "$TITLE" "YOUTUBE_URL"
```

### Download Auto-Generated Subtitles (Fallback)

If manual subtitles aren't available:

```bash
yt-dlp --write-auto-sub --sub-langs en --skip-download --output "$TITLE" "YOUTUBE_URL"
```

Both commands create a `.vtt` file named `<videoTitle>.en.vtt`.

## Post-Processing

> **`$SKILL_DIR`**: the directory containing this SKILL.md file.

### Convert VTT to Timestamped Transcript

VTT auto-generated subtitles contain duplicate lines. Extract clean text with timestamps.

Use the VTT filename from the download step (e.g. `<videoTitle>.en.vtt`).

**The first line of the output file must be a markdown link to the source video:**

```bash
echo "Source: [$TITLE](YOUTUBE_URL)" > "$OUTPUT_MD"
echo >> "$OUTPUT_MD"
python3 "$SKILL_DIR/scripts/vtt_to_transcript.py" "$TITLE.en.vtt" >> "$OUTPUT_MD"
```
```
Source: [The AI Native Engineer](https://www.youtube.com/watch?v=xxxxx)

[00:00:01.670] there is this emergence of kind of like
[00:00:03.990] a new I would say class of like engineer
[00:00:05.884] which is like the AI native engineer
```

### Complete Workflow

```bash
VIDEO_URL="YOUTUBE_URL"
OUTPUT_DIR="/Users/jansen/OpenWork"

cd "$OUTPUT_DIR"

# Get video title and channel, sanitize for filename
TITLE=$(yt-dlp --get-title "$VIDEO_URL" | sed 's/[/:*?"<>|]/-/g')
CHANNEL=$(yt-dlp --print channel "$VIDEO_URL" | sed 's/^NA$//')

# Derive snake_case output filename as Youtube-<channel>-<title>
snake_case() {
  echo "$1" | sed 's/[^[:alnum:]]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//'
}
CHANNEL_SNAKE=$(snake_case "$CHANNEL")
SNAKE_TITLE=$(snake_case "$TITLE")
OUTPUT_MD="Youtube-${CHANNEL_SNAKE:+$CHANNEL_SNAKE-}$SNAKE_TITLE.md"

# Download auto-generated English subtitles
yt-dlp --write-auto-sub --sub-langs en --skip-download --output "$TITLE" "$VIDEO_URL"

# Find the VTT file
VTT_FILE="$TITLE.en.vtt"

# Write source link as first line
echo "Source: [$TITLE]($VIDEO_URL)" > "$OUTPUT_MD"
echo >> "$OUTPUT_MD"

# Convert to timestamped transcript
python3 "$SKILL_DIR/scripts/vtt_to_transcript.py" "$VTT_FILE" >> "$OUTPUT_MD"

echo "Transcription complete: $OUTPUT_MD"
```

## Optional Feature: Fetch Comments (Read-Only)

yt-dlp can fetch the comment section directly from YouTube's comment API — no scraping needed. Useful for reading top/highly-liked comments, gauging audience reaction, or analyzing the comment section. **This feature does not download any video/subtitle files.**

### Quick Start (single command, no files written)

Pipe `--dump-single-json` straight to Python for parsing — avoids any file-write permission issues and leaves no artifacts:

```bash
yt-dlp --skip-download --write-comments --dump-single-json --no-warnings \
  --extractor-args "youtube:comment_sort=top;max_comments=80" "YOUTUBE_URL" 2>/dev/null \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
comments=d.get('comments') or []
print(f'comments: {len(comments)}')
for i,c in enumerate(comments):
    print(f'### {i+1} | likes={c.get(\"like_count\",0)} | {c.get(\"author\",\"\")}')
    print(c.get('text',''))
    print()
"
```

**CRITICAL GOTCHAS** (each was hit in the field — do not skip):

1. **You MUST pass `--write-comments`.** Without it, the `comments` field comes back empty (`[]`) even when `max_comments` is set. This is the #1 mistake.
2. **`comment_sort` accepts `top` (default) or `newest`.** `top` returns the highest-liked comments — what users usually want.
3. **`max_comments`** caps the number pulled. Values of 40–100 work well. Note: total available is often larger (e.g. 141 comments in the section) but extraction may stop earlier depending on API.
4. **`--dump-single-json` writes to stdout** — prefer it over `--write-info-json` (which writes a file and may fail on permission-restricted dirs like root-owned `/tmp`). If you DO want a file, run in a user-writable dir.
5. **Expected warnings**: "No supported JavaScript runtime could be found" and "ffmpeg not found" are harmless for comment fetching — both are only needed for format/format-download paths. Ignore them.

### Verifying After Fetch

- If `comments: 0` → see gotcha #1 above. Do NOT retry with different flags blindly.
- If extraction hangs or times out on a very large comment section, lower `max_comments` (e.g. 20) or retry once.

## Fallback: Subtitle API Blocked (HTTP 429)

When yt-dlp subtitle download fails with `HTTP Error 429: Too Many Requests`, the YouTube timedtext subtitle API is blocked for this IP. This is common on cloud/VPS/datacenter environments where YouTube pre-blocks non-residential IP ranges. **The video download itself is NOT affected** — audio downloads go through a different CDN endpoint.

**There is no fix for this yt-dlp-side.** The only reliable fallback is:

1. Download the audio track with yt-dlp
2. Transcribe locally with faster-whisper + PyAV

### Prerequisites for Whisper Fallback

faster-whisper must be available. Follow the [faster-whisper Pre-Check](#faster-whisper) steps before proceeding. Quick verification:

```bash
python3 -c "from faster_whisper import WhisperModel; import av; print('ready')"
```

### Audio Download + Whisper Transcription Workflow

Use a single Python script for the entire pipeline — download audio, transcribe, output formatted markdown:

```bash
cd "$OUTPUT_DIR"

python3 << 'PYEOF'
import subprocess, re, time, os

VIDEO_URL = "YOUTUBE_URL"

# --- Step 1: Get title/channel and download audio ---
title = subprocess.check_output(["yt-dlp", "--get-title", VIDEO_URL], text=True).strip()
channel = subprocess.check_output(["yt-dlp", "--print", "channel", VIDEO_URL], text=True).strip()
if channel == "NA":
    channel = ""
safe_title = re.sub(r'[/:*?"<>|]', '-', title)
audio_file = f"{safe_title}.webm"

print(f"Downloading audio: {title}")
subprocess.run(["yt-dlp", "-f", "bestaudio", "--output", audio_file, VIDEO_URL], check=True)

# --- Step 2: Transcribe with faster-whisper ---
from faster_whisper import WhisperModel
import av  # noqa: F401 — used by faster-whisper internally

print("Transcribing...")
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_file, language="en", beam_size=5, vad_filter=True)
print(f"Detected: {info.language} (p={info.language_probability:.2f})")

# --- Step 3: Write output ---
snake_case = lambda s: '_'.join(re.findall(r'\w+', s))
snake_title = snake_case(title)
snake_channel = snake_case(channel)
prefix = f"Youtube-{snake_channel}-" if snake_channel else "Youtube-"
output_file = f"{prefix}{snake_title}.md"

with open(output_file, 'w') as f:
    f.write(f"Source: [{title}]({VIDEO_URL})\n\n")
    for seg in segments:
        h, m, s = int(seg.start // 3600), int((seg.start % 3600) // 60), seg.start % 60
        timestamp = f"[{h:02d}:{m:02d}:{s:06.3f}]"
        f.write(f"{timestamp} {seg.text.strip()}\n")

# --- Step 4: Clean up audio ---
os.remove(audio_file)
print(f"Done → {output_file}")
PYEOF
```

**Model selection guidance:**
- `small` (~460MB): Best for clear English speech, ~5s per minute of audio on CPU. Default choice for YouTube talk/presentation content.
- `medium` (~1.5GB): Better for accented speech or mild background noise. ~2-3x slower.
- `large-v3` (~3GB): Best for noisy environments, non-English, or multi-speaker. ~4-5x slower. Not worth it for clean single-speaker English.

## Output Formats

- **VTT format** (`.vtt`): Raw subtitle file with word-level timing markup (yt-dlp subtitle download only)
- **Timestamped transcript** (`.md`): Named `Youtube-<Channel>-<Snake_Case_Title>.md`, e.g. `Youtube-Tina_Huang-MCP_In_26_Minutes_Model_Context_Protocol.md`. Clean text with line-level timestamps, e.g. `[00:01:23.456] text here`. Produced by both yt-dlp and Whisper paths.

## Common Issues

| Error | Solution |
|-------|----------|
| `command not found: yt-dlp` | Run `source ~/.zshrc` first, then check common Python bin paths |
| `No subtitles for requested languages` | Try `--write-auto-sub` instead of `--write-sub` |
| `HTTP Error 429: Too Many Requests` | Subtitle API blocked on this IP (common on cloud/VPS). Do NOT retry — use [Audio + Whisper fallback](#fallback-subtitle-api-blocked-http-429) immediately. |
| `HTTP Error 403: Forbidden` on subtitle | Same as 429 — IP/subnet is pre-blocked. Use Whisper fallback. |
| `ModuleNotFoundError: No module named 'faster_whisper'` | Run through the [faster-whisper Pre-Check](#faster-whisper) steps |
| `ModuleNotFoundError: No module named 'av'` | PyAV missing — run `~/.venv/bin/pip install faster-whisper` (installs `av` as dependency) |
| Python 3.9 deprecated | Upgrade to Python 3.10+ |
| `Cannot write video metadata to JSON file` | Running in a permission-restricted dir (e.g. root-owned `/tmp`). Use `--dump-single-json` piped to stdout instead of `--write-info-json` |
