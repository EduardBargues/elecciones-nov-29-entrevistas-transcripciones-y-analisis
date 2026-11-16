#!/usr/bin/env python3
"""
Convert a VTT subtitle file into a speaker-labeled transcript.

Detects the source platform (rtve or youtube) from the filename and applies
the appropriate processing logic automatically. Output is written to the
transcripts/ directory with the same filename but a .txt extension.

Filename convention:
  {candidate}.{program}.{platform}.{language}.vtt
  e.g. ada-colau.the-wild-project.youtube.es.vtt
       pedro-sanchez.la-revuelta.rtve.es.vtt

Usage:
  python3 subtitles_to_transcript.py <input.vtt> [--guest NAME] [--guest2 NAME]

  --guest is required for RTVE files: it identifies the guest so the script
  knows when the interview starts (Broncano's first line mentioning the guest).
  --guest is ignored for YouTube files, which have no speaker information.
"""

import sys
import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a VTT subtitle file into a speaker-labeled transcript"
    )
    parser.add_argument("input", help="Input .vtt file")
    parser.add_argument("--guest", default="Guest", help="Guest name — required for RTVE files")
    parser.add_argument("--guest2", default=None, help="Second guest name — RTVE only")
    return parser.parse_args()


def detect_platform(input_path):
    """Extract platform from the third dot-separated segment of the filename."""
    parts = Path(input_path).name.split(".")
    return parts[2].lower() if len(parts) >= 3 else None


def derive_output(input_path):
    """Replace .vtt with .txt and place in transcripts/."""
    output_name = Path(input_path).with_suffix(".txt").name
    output_dir = Path("transcripts")
    output_dir.mkdir(exist_ok=True)
    return output_dir / output_name


def main():
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    platform = detect_platform(input_path)
    output_path = derive_output(input_path)

    if platform == "rtve":
        from rtve_vtt_to_transcript import parse_vtt, merge_consecutive, deduplicate, write_transcript
        entries = parse_vtt(input_path, guest_name=args.guest, guest2_name=args.guest2)
        turns = merge_consecutive(entries, guest_name=args.guest, guest2_name=args.guest2)
        turns = deduplicate(turns)
        write_transcript(turns, output_path)
        print(f"Transcript written to: {output_path} ({len(turns)} turns)")

    elif platform == "youtube":
        from youtube_vtt_to_transcript import extract_clean_lines, join_into_paragraphs
        content = input_path.read_text(encoding="utf-8")
        clean_lines = extract_clean_lines(content)
        paragraphs = join_into_paragraphs(clean_lines, paragraph_size=4)
        output_path.write_text("\n\n".join(paragraphs) + "\n", encoding="utf-8")
        print(f"Transcript written to: {output_path} ({len(paragraphs)} paragraphs)")

    else:
        print(f"Error: unrecognised platform '{platform}' in filename '{input_path.name}'.", file=sys.stderr)
        print("Expected format: {{candidate}}.{{program}}.{{platform}}.{{language}}.vtt", file=sys.stderr)
        print("Supported platforms: rtve, youtube", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
