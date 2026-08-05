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

Download transcripts from YouTube. Primary: yt-dlp subtitles (instant, free). Fallback: faster-whisper local transcription when the subtitle API is blocked or no subtitles exist.

All Python scripts live in `$SKILL_DIR/scripts/`.

## Decision

1. Check subtitles first: `yt-dlp --list-subs "URL"`. If any exist → **Path A (yt-dlp subtitles)**.
2. If subtitle download fails with `HTTP 429/403` (timedtext API blocked on this IP, common on cloud/VPS/datacenter) or no subtitles exist → **Path B (Whisper fallback)**. Do NOT retry — retrying is futile; audio downloads use a different CDN and are unaffected.

## Environment Check

```bash
# yt-dlp: try PATH, then macOS ~/.zshrc, then ~/.venv; install only if all fail.
# (macOS: VS Code's terminal may not load ~/.zshrc, so source it manually.)
source ~/.zshrc 2>/dev/null
export PATH="$HOME/.venv/bin:$PATH"
command -v yt-dlp >/dev/null || ~/.venv/bin/pip install -U "yt-dlp[default]"

# faster-whisper (installs PyAV automatically) -- only needed for Path B
~/.venv/bin/python3 -c "from faster_whisper import WhisperModel; import av" 2>/dev/null \
  || ~/.venv/bin/pip install faster-whisper
```

## Output Location

Let the caller decide: user-specified path > AGENTS.md convention > current working directory. Do NOT hardcode a machine-specific path.

Filename is always `Youtube-<Channel>-<Snake_Case_Title>.md`, and **the first line must be** `Source: [Title](URL)`.

## Path A: yt-dlp Subtitles (Preferred)

```bash
VIDEO_URL="YOUTUBE_URL"

# 1. Check subtitles -- read full output, don't grep (a lang under auto captions won't work with --write-sub)
yt-dlp --list-subs "$VIDEO_URL"

# 2. Get title/channel and derive snake_case filename
TITLE=$(yt-dlp --get-title "$VIDEO_URL" | sed 's/[/:*?"<>|]/-/g')
CHANNEL=$(yt-dlp --print channel "$VIDEO_URL" | sed 's/^NA$//')
snake_case() { echo "$1" | sed 's/[^[:alnum:]]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//'; }
CHANNEL_SNAKE=$(snake_case "$CHANNEL")
SNAKE_TITLE=$(snake_case "$TITLE")
OUTPUT_MD="Youtube-${CHANNEL_SNAKE:+$CHANNEL_SNAKE-}$SNAKE_TITLE.md"

# 3. Download subtitles -- manual first (--write-sub), fall back to auto (--write-auto-sub).
#    Copy the EXACT lang code from the --list-subs output. Manual subtitles are
#    listed under "Available subtitles", auto captions under "Available automatic
#    captions" -- and their codes DIFFER (e.g. zh-Hans manual vs zh-Hans-zh-Hans auto).
#    Use the flag that matches the section you picked.
yt-dlp --write-sub --sub-langs <lang> --skip-download --output "$TITLE" "$VIDEO_URL"
#    → on HTTP 429/403 do NOT retry; try the auto path (correct auto lang code), else Path B.

# 4. Verify the .vtt was actually written before converting. If missing, the
#    flag/lang-code combo was wrong (see step 3) or the subtitle API is blocked.
ls "$TITLE.<lang>.vtt"

# 5. Convert VTT to timestamped transcript
echo "Source: [$TITLE]($VIDEO_URL)" > "$OUTPUT_MD"
echo >> "$OUTPUT_MD"
python3 "$SKILL_DIR/scripts/vtt_to_transcript.py" "$TITLE.<lang>.vtt" >> "$OUTPUT_MD"
```

Note: the bash `snake_case` strips non-ASCII. For CJK/non-ASCII titles, prefer Path B's naming (Python `\w+` keeps Unicode), or sanitize the title in Python.

## Path B: Whisper Fallback (HTTP 429/403 or No Subtitles)

```bash
python3 "$SKILL_DIR/scripts/whisper_fallback.py" "YOUTUBE_URL" [--lang zh] [--model small] [--outdir .]
```

- `--lang`: source language (e.g. `zh`, `en`). Default: **auto-detect** from audio — do not force English; pick per video (CJK videos → `zh`).
- `--model`: `small` (default, ~460MB, ~5s per min of audio, fine for clean speech) → `medium` (accent/noise, 2-3x slower) → `large-v3` (complex/noisy/multi-speaker, 4-5x slower).
- The script downloads audio → transcribes on CPU → writes the `.md` → deletes the audio.

## Optional: Fetch Comments (Read-Only)

```bash
python3 "$SKILL_DIR/scripts/fetch_comments.py" "YOUTUBE_URL" [--sort top|newest] [--max 80]
```

No files written. Gotchas are documented in the script's docstring.

## Output Formats

- `.vtt`: raw subtitle file with timing markup (Path A only)
- `.md`: `Youtube-<Channel>-<Snake_Case_Title>.md` with line-level timestamps `[00:01:23.456] text here` (both paths)

## Common Issues

| Error | Solution |
|-------|----------|
| `command not found: yt-dlp` | `source ~/.zshrc`, then check `~/.venv/bin` |
| `No subtitles for requested languages` | flag/lang-code mismatch: manual subs (`--write-sub`) are under "Available subtitles", auto (`--write-auto-sub`) under "Available automatic captions" with different codes (`zh-Hans` vs `zh-Hans-zh-Hans`). Copy the exact code from `--list-subs`. |
| `HTTP Error 429/403` on subtitle | Do NOT retry → Path B (Whisper fallback) |
| Exit code is 0 even on failure | yt-dlp returns 0 for both "no subtitles" and 429. Do NOT trust exit codes — verify the `.vtt` file exists (step 4) and read the error text. |
| `ModuleNotFoundError: faster_whisper` / `av` | `~/.venv/bin/pip install faster-whisper` (installs `av`) |
| `Cannot write video metadata to JSON file` | Restricted dir → `--dump-single-json` to stdout |
