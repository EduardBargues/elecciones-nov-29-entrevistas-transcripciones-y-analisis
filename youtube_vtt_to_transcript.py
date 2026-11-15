#!/usr/bin/env python3
"""
Convert a YouTube auto-generated VTT subtitle file into clean plain text.

YouTube auto-captions use a rolling karaoke format: each block repeats the
previous line fully formed and adds new words being timed in. This script
strips all timing tags, deduplicates the rolling lines, and writes clean text.

Usage:
  python3 youtube_vtt_to_transcript.py <input.vtt> [output.txt]

Requirements:
  Python 3.8+
"""

import re
import sys
import argparse
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
TIMESTAMP_LINE_RE = re.compile(r"^\d{2}:\d{2}:\d{2}[\.,]\d+")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert YouTube auto-generated VTT to clean plain text"
    )
    parser.add_argument("input", help="Input .vtt file")
    parser.add_argument("output", nargs="?", help="Output .txt file (default: <stem>-transcript.txt)")
    return parser.parse_args()


def strip_tags(text):
    return TAG_RE.sub("", text).strip()


def extract_clean_lines(vtt_content):
    """Extract deduplicated lines from YouTube's rolling karaoke VTT format.

    Each block shows the previous completed line above and the current line
    being formed below (with word-timing tags). Taking the last non-empty
    line from each block and dropping consecutive duplicates gives the clean
    linear transcript.
    """
    result = []
    last_line = None

    for block in re.split(r"\n{2,}", vtt_content.strip()):
        raw_lines = block.strip().splitlines()
        if not raw_lines:
            continue

        first = raw_lines[0].strip()
        if first.startswith("WEBVTT") or first.startswith("Kind:") or first.startswith("Language:"):
            continue

        text_lines = []
        for line in raw_lines:
            s = line.strip()
            if not s or TIMESTAMP_LINE_RE.match(s) or re.match(r"^\d+$", s):
                continue
            clean = strip_tags(s)
            if clean:
                text_lines.append(clean)

        if not text_lines:
            continue

        current = text_lines[-1]
        if current != last_line:
            result.append(current)
            last_line = current

    return result


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    stem = input_path.stem
    if stem.endswith(".es"):
        stem = stem[:-3]
    output_path = args.output or (stem + "-transcript.txt")

    print(f"Cleaning YouTube VTT: {input_path}")
    content = input_path.read_text(encoding="utf-8")
    clean_lines = extract_clean_lines(content)
    print(f"Extracted {len(clean_lines)} unique lines")

    Path(output_path).write_text("\n".join(clean_lines) + "\n", encoding="utf-8")
    print(f"Transcript written to: {output_path}")


if __name__ == "__main__":
    main()
