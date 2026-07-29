---
name: youtube-dlp-python
description: |
  Download YouTube video transcripts (subtitles/captions) using yt-dlp, with faster-whisper as fallback for local transcription.
  Supports manual subtitles, auto-generated captions, and Whisper transcription when the subtitle API is blocked.

  Triggers when user mentions:
  - Provides a YouTube URL and wants the transcript
  - "download transcript" or "get captions/subtitles" from a YouTube video
  - "transcribe a YouTube video" or needs text content from a video
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
~/.venv/bin/pip install yt-dlp
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

### Get Video Title

Use the video title as the output filename:

```bash
TITLE=$(yt-dlp --get-title "YOUTUBE_URL" | sed 's/[/:*?"<>|]/-/g')
```

### Derive Snake Case Filename

Convert the title to snake_case, removing special characters (`.` `,` `'` etc.), and prefix with `Youtube-Transcript-`:

```bash
SNAKE_TITLE=$(echo "$TITLE" | sed "s/[^a-zA-Z0-9 ]//g" | sed 's/  */ /g' | sed 's/ /_/g')
OUTPUT_MD="Youtube-Transcript-$SNAKE_TITLE.md"
```

Example: `From Writing Code to Managing Agents. Most Engineers Aren't Ready - Stanford University, Mihail Eric` becomes `Youtube-Transcript-From_Writing_Code_to_Managing_Agents_Most_Engineers_Arent_Ready__Stanford_University_Mihail_Eric.md`

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

### Convert VTT to Timestamped Transcript

VTT auto-generated subtitles contain duplicate lines. Extract clean text with timestamps.

Use the VTT filename from the download step (e.g. `<videoTitle>.en.vtt`).

**The first line of the output file must be a markdown link to the source video:**

```bash
echo "Source: [$TITLE](YOUTUBE_URL)" > "$OUTPUT_MD"
echo >> "$OUTPUT_MD"
python3 scripts/vtt_to_transcript.py "$TITLE.en.vtt" >> "$OUTPUT_MD"
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

# Get video title and sanitize for filename
TITLE=$(yt-dlp --get-title "$VIDEO_URL" | sed 's/[/:*?"<>|]/-/g')

# Derive snake_case output filename with Youtube-Transcript- prefix
SNAKE_TITLE=$(echo "$TITLE" | sed "s/[^a-zA-Z0-9 ]//g" | sed 's/  */ /g' | sed 's/ /_/g')
OUTPUT_MD="Youtube-Transcript-$SNAKE_TITLE.md"

# Download auto-generated English subtitles
yt-dlp --write-auto-sub --sub-langs en --skip-download --output "$TITLE" "$VIDEO_URL"

# Find the VTT file
VTT_FILE="$TITLE.en.vtt"

# Write source link as first line
echo "Source: [$TITLE]($VIDEO_URL)" > "$OUTPUT_MD"
echo >> "$OUTPUT_MD"

# Convert to timestamped transcript
python3 scripts/vtt_to_transcript.py "$VTT_FILE" >> "$OUTPUT_MD"

echo "Transcription complete: $OUTPUT_MD"
```

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

# --- Step 1: Get title and download audio ---
title = subprocess.check_output(["yt-dlp", "--get-title", VIDEO_URL], text=True).strip()
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
snake_title = re.sub(r'[^a-zA-Z0-9 ]', '', title)
snake_title = re.sub(r'\s+', '_', snake_title.strip())
output_file = f"Youtube-Transcript-{snake_title}.md"

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
- **Timestamped transcript** (`.md`): Named `Youtube-Transcript-<Snake_Case_Title>.md`. Clean text with line-level timestamps, e.g. `[00:01:23.456] text here`. Produced by both yt-dlp and Whisper paths.

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
