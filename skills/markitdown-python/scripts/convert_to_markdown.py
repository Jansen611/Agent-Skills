#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

from markitdown import MarkItDown


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a supported input to Markdown.")
    parser.add_argument("input", help="Input file path or URL")
    parser.add_argument("-o", "--output", help="Output Markdown path")
    return parser.parse_args()


def get_output_path(input_value: str, output_value: str | None) -> Path:
    if output_value:
        return Path(output_value)

    parsed_url = urlparse(input_value)
    if parsed_url.scheme in {"http", "https"}:
        raise ValueError("--output is required when the input is a URL.")

    return Path(input_value).with_suffix(".md")


def main() -> int:
    arguments = parse_arguments()
    output_path = get_output_path(arguments.input, arguments.output)
    result = MarkItDown().convert(arguments.input)
    text = result.text_content.replace("\x00", "")

    if not text.strip():
        raise ValueError("Markdown output is empty.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8", newline="")

    if output_path.stat().st_size == 0:
        raise ValueError("Markdown output is empty.")

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
