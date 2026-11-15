#!/usr/bin/env python3
"""
Convert an RTVE VTT subtitle file into a speaker-labeled transcript.

Color convention (RTVE La Revuelta):
  <c.yellow>  = Broncano (host)
  <c.green>   = collaborator/co-host
  <c.magenta> = collaborator/co-host
  no color    = guest (after interview start only)

Everything before the interview start is discarded. The interview start is
detected automatically as the first yellow block mentioning the guest name.

Usage:
  python3 vtt_to_transcript.py <input.vtt> [output.txt] [--guest NAME] [--guest2 NAME]
"""

import re
import sys
import argparse
from pathlib import Path

HOST_NAME = "Broncano"

COLOR_RE = re.compile(r"<c\.(\w+)>")
TIMESTAMP_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d+)")


def parse_args():
    parser = argparse.ArgumentParser(description="Convert RTVE VTT to speaker-labeled transcript")
    parser.add_argument("input", help="Input .vtt file")
    parser.add_argument("output", nargs="?", help="Output .txt file (default: <input>-transcript.txt)")
    parser.add_argument("--guest", default="Guest", help="Name of the guest (uncolored lines after interview start)")
    parser.add_argument("--guest2", default=None, help="Name of a second guest (activates name-based speaker switching)")
    return parser.parse_args()


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text).strip()


def detect_color(raw_line):
    match = COLOR_RE.search(raw_line)
    return match.group(1) if match else None


def timestamp_to_seconds(ts_line):
    """Convert 'HH:MM:SS.mmm --> ...' to float seconds, or None."""
    m = TIMESTAMP_RE.match(ts_line.strip())
    if not m:
        return None
    h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return h * 3600 + mi * 60 + s + ms / 1000.0


def split_blocks(content):
    """Return list of (start_seconds, [text_lines]) for each VTT block."""
    blocks = []
    for block in re.split(r"\n{2,}", content.strip()):
        lines = block.strip().splitlines()
        if not lines or lines[0].startswith("WEBVTT") or lines[0].startswith("NOTE"):
            continue

        start_ts = None
        text_lines = []
        for line in lines:
            if TIMESTAMP_RE.match(line.strip()):
                if start_ts is None:
                    start_ts = timestamp_to_seconds(line)
            elif re.match(r"^\d+$", line.strip()):
                continue
            else:
                text_lines.append(line)

        if start_ts is not None and text_lines:
            blocks.append((start_ts, text_lines))

    return blocks


def build_name_pattern(name):
    words = [w for w in name.split() if len(w) > 2]
    return re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in words) + r")\b",
        re.IGNORECASE,
    )


def find_interview_start(blocks, guest_name, guest2_name=None):
    """Return the timestamp of the first yellow block mentioning any guest."""
    patterns = [build_name_pattern(guest_name)]
    if guest2_name:
        patterns.append(build_name_pattern(guest2_name))
    for ts, text_lines in blocks:
        combined = " ".join(text_lines)
        if "<c.yellow>" not in combined:
            continue
        clean = strip_tags(combined)
        if any(p.search(clean) for p in patterns):
            return ts
    return None


def classify_line(raw_line, active_guest="guest"):
    """Return (speaker_key, clean_text) or (None, None) to discard."""
    raw_line = raw_line.strip()
    if not raw_line:
        return None, None

    if re.match(r"^\([^)]*\)$", raw_line) or raw_line.startswith("#"):
        return None, None

    color = detect_color(raw_line)
    text = strip_tags(raw_line)

    if not text:
        return None, None

    if color == "yellow":
        return "host", text
    if color in ("green", "magenta"):
        return "collaborator", text
    return active_guest, text


def parse_vtt(filepath, guest_name, guest2_name=None):
    content = Path(filepath).read_text(encoding="utf-8")
    blocks = split_blocks(content)
    interview_start = find_interview_start(blocks, guest_name, guest2_name)

    if interview_start is not None:
        h = int(interview_start // 3600)
        m = int((interview_start % 3600) // 60)
        s = int(interview_start % 60)
        print(f"Interview start detected at {h:02d}:{m:02d}:{s:02d}")
    else:
        print("Warning: could not detect interview start — no output will be generated")
        return []

    guest1_pattern = build_name_pattern(guest_name)
    guest2_pattern = build_name_pattern(guest2_name) if guest2_name else None
    active_guest = "guest"

    entries = []
    for ts, text_lines in blocks:
        if ts < interview_start:
            continue

        if guest2_pattern:
            # Scan yellow lines first to detect who Broncano is addressing
            for raw in text_lines:
                if "<c.yellow>" in raw:
                    clean = strip_tags(raw)
                    if guest2_pattern.search(clean):
                        active_guest = "guest2"
                    elif guest1_pattern.search(clean):
                        active_guest = "guest"

        for raw in text_lines:
            key, text = classify_line(raw, active_guest)
            if key and text:
                entries.append((key, text))

    return entries


def merge_consecutive(entries, guest_name, guest2_name=None):
    key_to_name = {
        "host": HOST_NAME,
        "guest": guest_name,
        "guest2": guest2_name or guest_name,
        "collaborator": "Colaborador",
        "other": "Other",
    }
    merged = []
    prev_key, buffer = None, []

    for key, text in entries:
        if key == prev_key:
            buffer.append(text)
        else:
            if prev_key is not None:
                merged.append((key_to_name[prev_key], " ".join(buffer)))
            prev_key, buffer = key, [text]

    if prev_key is not None:
        merged.append((key_to_name[prev_key], " ".join(buffer)))

    return merged


def deduplicate(turns):
    result = []
    prev = None
    for turn in turns:
        if turn != prev:
            result.append(turn)
            prev = turn
    return result


def write_transcript(turns, output_path):
    lines = [f"[{speaker}] {text}" for speaker, text in turns]
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or input_path.with_suffix("").stem + "-transcript.txt"

    entries = parse_vtt(input_path, guest_name=args.guest, guest2_name=args.guest2)
    turns = merge_consecutive(entries, guest_name=args.guest, guest2_name=args.guest2)
    turns = deduplicate(turns)
    write_transcript(turns, output_path)

    print(f"Transcript written to: {output_path}")
    print(f"Total turns: {len(turns)}")


if __name__ == "__main__":
    main()
