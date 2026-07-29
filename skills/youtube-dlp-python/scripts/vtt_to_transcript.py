#!/usr/bin/env python3
"""Convert YouTube VTT subtitle file to timestamped transcript text.

Usage: python3 vtt_to_transcript.py <file.vtt>
Output: timestamped lines to stdout, e.g. [00:01:23.456] text here
"""

import re
import sys


def to_ms(t: str) -> int:
    h, mn, rest = t.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600000 + int(mn) * 60000 + int(s) * 1000 + int(ms)


def vtt_to_transcript(vtt_path: str) -> None:
    with open(vtt_path, "r") as f:
        lines = f.readlines()

    seen: set[str] = set()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(
            r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})", line
        )
        if m:
            start, end = m.group(1), m.group(2)
            # Skip very short segments (likely artifacts)
            if to_ms(end) - to_ms(start) <= 20:
                if i + 1 < len(lines):
                    text = lines[i + 1].strip()
                    text = re.sub("<[^>]*>", "", text)
                    text = (
                        text.replace("&amp;", "&")
                        .replace("&gt;", ">")
                        .replace("&lt;", "<")
                    )
                    if text and text not in seen:
                        print(f"[{start}] {text}")
                        seen.add(text)
        i += 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file.vtt>", file=sys.stderr)
        sys.exit(1)
    vtt_to_transcript(sys.argv[1])
