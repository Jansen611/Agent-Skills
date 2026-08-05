#!/usr/bin/env python3
"""Fetch YouTube comments (read-only, writes no files).

Gotchas learned in the field:
- MUST pass --write-comments, otherwise the comments field comes back empty.
- Prefer --dump-single-json piped to stdout over --write-info-json to avoid
  file-write permission errors in restricted dirs.
- "No supported JavaScript runtime could be found" and "ffmpeg not found"
  warnings are harmless for comment fetching.
- If extraction hangs/times out on a huge section, lower --max or retry once.

Usage:
    python3 fetch_comments.py <VIDEO_URL> [--sort top|newest] [--max 80]
"""

import argparse
import json
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--sort", choices=["top", "newest"], default="top",
        help="Comment sort order (default: top, i.e. highest-liked).",
    )
    parser.add_argument(
        "--max", type=int, default=80,
        help="Max comments to pull (default: 80).",
    )
    args = parser.parse_args()

    cmd = [
        "yt-dlp", "--skip-download", "--write-comments", "--dump-single-json",
        "--no-warnings",
        "--extractor-args",
        f"youtube:comment_sort={args.sort};max_comments={args.max}",
        args.url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    d = json.loads(proc.stdout)
    comments = d.get("comments") or []
    print(f"comments: {len(comments)}")
    for i, c in enumerate(comments):
        print(f"### {i + 1} | likes={c.get('like_count', 0)} | {c.get('author', '')}")
        print(c.get("text", ""))
        print()


if __name__ == "__main__":
    main()
