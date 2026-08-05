#!/usr/bin/env python3
"""Audio + faster-whisper fallback for YouTube transcripts.

Use when yt-dlp subtitle download fails with HTTP 429/403 (IP/subnet blocked)
or no subtitles exist. Downloads the audio track, transcribes locally on CPU,
writes a timestamped markdown transcript, then deletes the audio.

Usage:
    python3 whisper_fallback.py <VIDEO_URL> [--lang zh] [--model small] [--outdir .]

    --lang    Source language for transcription (e.g. zh, en). Default: auto-detect.
    --model   Whisper model size: tiny/base/small/medium/large-v3. Default: small.
    --outdir  Output directory. Default: current working directory.

Output: <outdir>/Youtube-<channel>-<snake_case_title>.md
First line is a markdown link to the source video.
"""

import argparse
import os
import re
import subprocess

from faster_whisper import WhisperModel
import av  # noqa: F401 -- used by faster-whisper internally


def snake_case(s: str) -> str:
    return "_".join(re.findall(r"\w+", s))


def run(args: argparse.Namespace) -> None:
    title = subprocess.check_output(
        ["yt-dlp", "--get-title", args.url], text=True
    ).strip()
    channel = subprocess.check_output(
        ["yt-dlp", "--print", "channel", args.url], text=True
    ).strip()
    if channel == "NA":
        channel = ""

    safe_title = re.sub(r'[/:*?"<>|]', "-", title)
    audio_file = f"{safe_title}.webm"

    print(f"Downloading audio: {title}")
    subprocess.run(
        ["yt-dlp", "-f", "bestaudio", "--output", audio_file, args.url],
        check=True,
    )

    print(f"Transcribing with faster-whisper ({args.model})...")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio_file,
        language=args.lang,  # None -> auto-detect from audio
        beam_size=5,
        vad_filter=True,
    )
    print(f"Detected: {info.language} (p={info.language_probability:.2f})")

    snake_title = snake_case(title)
    snake_channel = snake_case(channel)
    prefix = f"Youtube-{snake_channel}-" if snake_channel else "Youtube-"
    output_file = os.path.join(args.outdir, f"{prefix}{snake_title}.md")

    with open(output_file, "w") as f:
        f.write(f"Source: [{title}]({args.url})\n\n")
        for seg in segments:
            h, m, s = int(seg.start // 3600), int((seg.start % 3600) // 60), seg.start % 60
            timestamp = f"[{h:02d}:{m:02d}:{s:06.3f}]"
            f.write(f"{timestamp} {seg.text.strip()}\n")

    os.remove(audio_file)
    print(f"Done → {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--lang",
        default=None,
        help="Source language for transcription (e.g. zh, en). Default: auto-detect.",
    )
    parser.add_argument(
        "--model",
        default="small",
        help="Whisper model size: tiny/base/small/medium/large-v3 (default: small).",
    )
    parser.add_argument(
        "--outdir",
        default=".",
        help="Output directory (default: current working directory).",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
