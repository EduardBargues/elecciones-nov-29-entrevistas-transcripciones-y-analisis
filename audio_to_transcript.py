#!/usr/bin/env python3
"""
Transcribe a YouTube video or local audio file with speaker diarization.

Uses Whisper for transcription and pyannote.audio for speaker attribution.
Outputs a labeled transcript in [Speaker] Text format, compatible with the
existing transcripts in this repository.

Usage:
  python3 audio_to_transcript.py <url_or_file> [output.txt]
                                 [--model SIZE] [--host NAME] [--guest NAME]
                                 [--language LANG] [--num-speakers N]

Setup:
  pip install openai-whisper pyannote.audio torch torchaudio yt-dlp
  1. Create a free account at https://huggingface.co
  2. Accept model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
  3. Create an access token at https://huggingface.co/settings/tokens
  4. export HF_TOKEN="hf_..."

Notes:
  - Recommended model for Spanish: 'large-v3' (most accurate) or 'medium' (faster)
  - On CPU, expect ~2x realtime for 'medium' and ~4x for 'large-v3'
    (a 90-min interview takes roughly 3–6 hours without a GPU)
  - ffmpeg is required for audio conversion: brew install ffmpeg
"""

import sys
import os
import re
import argparse
import subprocess
import tempfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video with speaker diarization via Whisper + pyannote"
    )
    parser.add_argument("input", help="YouTube URL or path to a local audio/video file")
    parser.add_argument("output", nargs="?", help="Output .txt file (default: <stem>-transcript.txt)")
    parser.add_argument(
        "--model", default="medium",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size (default: medium)"
    )
    parser.add_argument("--language", default="es", help="Language code (default: es)")
    parser.add_argument("--host", default="Host", help="Name for the first/most frequent speaker (usually the host)")
    parser.add_argument("--guest", required=True, help="Name for the interview guest")
    parser.add_argument("--num-speakers", type=int, default=2, help="Expected number of speakers (default: 2)")
    return parser.parse_args()


def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


def download_audio(url, output_dir):
    """Download audio from a YouTube URL using yt-dlp."""
    print(f"Downloading audio from: {url}")
    output_template = str(Path(output_dir) / "audio.%(ext)s")
    result = subprocess.run(
        ["yt-dlp", "--extract-audio", "--audio-format", "wav",
         "--audio-quality", "0", "-o", output_template, url],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"yt-dlp error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    for ext in ("wav", "m4a", "mp3", "opus", "webm", "ogg"):
        candidate = Path(output_dir) / f"audio.{ext}"
        if candidate.exists():
            print(f"Audio saved to: {candidate}")
            return str(candidate)

    print("Error: could not locate downloaded audio file.", file=sys.stderr)
    sys.exit(1)


def transcribe(audio_path, model_name, language):
    """Transcribe audio with Whisper. Returns a list of segment dicts."""
    try:
        import whisper
    except ImportError:
        print("Error: 'openai-whisper' not installed. Run: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)

    print("Transcribing — this may take a while on CPU...")
    result = model.transcribe(audio_path, language=language, verbose=False)
    segments = result["segments"]
    print(f"Transcribed {len(segments)} segments")
    return segments


def diarize(audio_path, num_speakers):
    """Run speaker diarization with pyannote. Returns list of (start, end, speaker) tuples."""
    try:
        from pyannote.audio import Pipeline
        import torch
    except ImportError:
        print("Error: 'pyannote.audio' not installed. Run: pip install pyannote.audio torch", file=sys.stderr)
        sys.exit(1)

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("Error: HF_TOKEN environment variable not set.", file=sys.stderr)
        print("  1. Accept model terms: https://huggingface.co/pyannote/speaker-diarization-3.1", file=sys.stderr)
        print("  2. Create a token:     https://huggingface.co/settings/tokens", file=sys.stderr)
        print("  3. export HF_TOKEN=\"hf_...\"", file=sys.stderr)
        sys.exit(1)

    print("Loading pyannote diarization pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )

    print("Running speaker diarization...")
    diarization = pipeline(audio_path, num_speakers=num_speakers)

    turns = [
        (turn.start, turn.end, speaker)
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]
    print(f"Found {len(turns)} speaker turns")
    return turns


def assign_speakers(segments, turns):
    """Assign the best-matching speaker to each Whisper segment by overlap."""
    labeled = []
    for seg in segments:
        overlap = {}
        for t_start, t_end, speaker in turns:
            o = max(0.0, min(seg["end"], t_end) - max(seg["start"], t_start))
            if o > 0:
                overlap[speaker] = overlap.get(speaker, 0.0) + o
        speaker = max(overlap, key=overlap.get) if overlap else "SPEAKER_00"
        labeled.append((speaker, seg["text"].strip()))
    return labeled


def name_speakers(labeled, host_name, guest_name):
    """Map pyannote speaker IDs to human names.

    Heuristic: the speaker who accumulates the most total time is the host
    (the interviewer typically speaks more in aggregate across a long interview).
    If that heuristic feels wrong for a specific interview, swap --host and --guest.
    """
    from collections import Counter
    counts = Counter(s for s, _ in labeled)
    most_frequent = counts.most_common(1)[0][0]

    name_map = {most_frequent: host_name}
    for speaker in counts:
        if speaker != most_frequent:
            name_map[speaker] = guest_name

    return [(name_map.get(s, s), t) for s, t in labeled]


def merge_consecutive(labeled):
    """Merge adjacent segments from the same speaker into a single turn."""
    merged = []
    for speaker, text in labeled:
        if merged and merged[-1][0] == speaker:
            merged[-1] = (speaker, merged[-1][1] + " " + text)
        else:
            merged.append((speaker, text))
    return merged


def main():
    args = parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        if is_url(args.input):
            audio_path = download_audio(args.input, tmpdir)
            default_stem = "transcript"
        else:
            audio_path = args.input
            if not Path(audio_path).exists():
                print(f"Error: file not found: {audio_path}", file=sys.stderr)
                sys.exit(1)
            default_stem = Path(audio_path).stem

        output_path = args.output or (default_stem + "-transcript.txt")

        segments = transcribe(audio_path, args.model, args.language)
        turns = diarize(audio_path, args.num_speakers)
        labeled = assign_speakers(segments, turns)
        labeled = name_speakers(labeled, args.host, args.guest)
        labeled = merge_consecutive(labeled)

        lines = [f"[{speaker}] {text}" for speaker, text in labeled]
        Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

        print(f"Transcript written to: {output_path} ({len(labeled)} turns)")


if __name__ == "__main__":
    main()
