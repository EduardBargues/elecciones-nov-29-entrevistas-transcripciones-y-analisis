#!/usr/bin/env python3
"""
Transcribe a YouTube video or local audio file with speaker diarization.

Uses Whisper for transcription and pyannote.audio for speaker attribution.
Outputs a labeled transcript in [Speaker] Text format, compatible with the
existing transcripts in this repository.

Usage:
  python3 audio_to_transcript.py <url_or_file> [--model SIZE] [--language LANG] [--num-speakers N]

Output is written to transcripts/<input-stem>.txt automatically.

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
import time
from pathlib import Path


def get_audio_duration(audio_path):
    """Return audio duration in seconds, or None if unreadable."""
    try:
        import wave
        with wave.open(audio_path, 'r') as wf:
            return wf.getnframes() / wf.getframerate()
    except Exception:
        return None


def fmt_duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video with speaker diarization via Whisper + pyannote"
    )
    parser.add_argument("input", help="YouTube URL or path to a local audio/video file")
    parser.add_argument(
        "--model", default="medium",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size (default: medium)"
    )
    parser.add_argument("--language", default="es", help="Language code (default: es)")
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


def transcribe(audio_path, model_name, language, audio_duration=None):
    """Transcribe audio with Whisper. Returns a list of segment dicts."""
    try:
        import whisper
    except ImportError:
        print("Error: 'openai-whisper' not installed. Run: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)

    realtime_factors = {"tiny": 0.1, "base": 0.2, "small": 0.5, "medium": 2.0,
                        "large": 4.0, "large-v2": 4.0, "large-v3": 4.0}
    if audio_duration:
        factor = realtime_factors.get(model_name, 2.0)
        est = fmt_duration(audio_duration * factor)
        print(f"Transcribing ({fmt_duration(audio_duration)} of audio, ~{est} estimated on CPU)...")
    else:
        print("Transcribing — this may take a while on CPU...")

    t0 = time.time()
    result = model.transcribe(audio_path, language=language, verbose=False)
    segments = result["segments"]
    print(f"Transcription done in {fmt_duration(time.time() - t0)} — {len(segments)} segments")
    return segments


def diarize(audio_path, num_speakers):
    """Run speaker diarization with pyannote. Returns list of (start, end, speaker) tuples."""
    try:
        import torchaudio
        if not hasattr(torchaudio, 'list_audio_backends'):
            torchaudio.list_audio_backends = lambda: ["soundfile"]
        # torchaudio 2.11+ defaults to torchcodec which may not be installed;
        # fall back to soundfile for audio loading.
        try:
            torchaudio.load("__probe__")
        except ImportError:
            import soundfile as _sf
            import torch as _torch
            def _sf_load(uri, frame_offset=0, num_frames=-1, *args, **kwargs):
                stop = None if num_frames == -1 else frame_offset + num_frames
                data, sr = _sf.read(
                    str(uri), start=frame_offset, stop=stop,
                    dtype="float32", always_2d=True
                )
                return _torch.tensor(data.T), sr
            torchaudio.load = _sf_load
        except Exception:
            pass
        if not hasattr(torchaudio, 'info'):
            import soundfile as _sf
            def _sf_info(path, *args, **kwargs):
                i = _sf.info(str(path))
                return torchaudio.AudioMetaData(
                    sample_rate=i.samplerate,
                    num_frames=i.frames,
                    num_channels=i.channels,
                    bits_per_sample=16,
                    encoding="PCM_S",
                )
            torchaudio.info = _sf_info
        if not hasattr(torchaudio, 'AudioMetaData'):
            try:
                from torchaudio.backend.common import AudioMetaData
            except ImportError:
                from dataclasses import dataclass
                @dataclass
                class AudioMetaData:
                    sample_rate: int
                    num_frames: int
                    num_channels: int
                    bits_per_sample: int
                    encoding: str
            torchaudio.AudioMetaData = AudioMetaData
        import torch
        try:
            import lightning_fabric.utilities.cloud_io as _cloud_io
            _orig_load = _cloud_io._load
            def _patched_load(path_or_url, map_location=None, **kwargs):
                kwargs['weights_only'] = False
                return _orig_load(path_or_url, map_location=map_location, **kwargs)
            _cloud_io._load = _patched_load
        except Exception:
            pass
        import huggingface_hub
        _real_download = huggingface_hub.hf_hub_download
        def _patched_download(*args, **kwargs):
            if 'use_auth_token' in kwargs:
                kwargs['token'] = kwargs.pop('use_auth_token')
            return _real_download(*args, **kwargs)
        huggingface_hub.hf_hub_download = _patched_download
        from pyannote.audio import Pipeline
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
    import huggingface_hub
    huggingface_hub.login(token=hf_token, add_to_git_credential=False)
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")

    print("Running speaker diarization (~1x realtime on CPU)...")
    t0 = time.time()
    diarization = pipeline(audio_path, num_speakers=num_speakers)

    turns = [
        (turn.start, turn.end, speaker)
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]
    print(f"Diarization done in {fmt_duration(time.time() - t0)} — {len(turns)} speaker turns")
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


def name_speakers(labeled):
    """Map pyannote speaker IDs to Speaker 1, Speaker 2, … by frequency."""
    from collections import Counter
    counts = Counter(s for s, _ in labeled)
    name_map = {
        speaker: f"Speaker {i + 1}"
        for i, (speaker, _) in enumerate(counts.most_common())
    }
    return [(name_map[s], t) for s, t in labeled]


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

        output_dir = Path("transcripts")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / (Path(audio_path).with_suffix(".txt").name)

        audio_duration = get_audio_duration(audio_path)
        segments = transcribe(audio_path, args.model, args.language, audio_duration)
        turns = diarize(audio_path, args.num_speakers)
        labeled = assign_speakers(segments, turns)
        labeled = name_speakers(labeled)
        labeled = merge_consecutive(labeled)

        lines = [f"[{speaker}] {text}" for speaker, text in labeled]
        Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

        print(f"Transcript written to: {output_path} ({len(labeled)} turns)")


if __name__ == "__main__":
    main()
