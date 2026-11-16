---
name: generate-transcript-from-subtitles
description: Convert a VTT subtitle file into a speaker-labeled transcript. Usage: /generate-transcript-from-subtitles <filename.vtt>
---

Convert a VTT subtitle file into a transcript using `scripts/subtitles_to_transcript.py`.

## Invocation

The subtitle filename is passed as a CLI argument (e.g. `/generate-transcript-from-subtitles ada-colau.la-revuelta.rtve.es.vtt`).

If no argument is provided, list all `.vtt` files found in `subtitles/` and show the correct usage, then stop.

---

## Step 1 — Resolve the input file

The argument may be:
- A bare filename: `ada-colau.la-revuelta.rtve.es.vtt` → look for it under `subtitles/`
- A path: `subtitles/ada-colau.la-revuelta.rtve.es.vtt` → use as-is

If the file cannot be found, tell the user and stop.

---

## Step 2 — Set up the Python environment

Check whether the `venv/` directory exists in the repository root.

If it does **not** exist, run these commands in order:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --index-url https://pypi.python.org/simple -r scripts/requirements.txt
```

If `venv/` already exists, skip setup entirely.

---

## Step 3 — Derive guest arguments

Parse the candidate slug from the **first dot-separated segment** of the filename.

Convert the slug to a display name:
1. Split on `-and-` to detect multiple guests.
2. For each part, replace hyphens with spaces and title-case every word.

Examples:
- `ada-colau` → `--guest "Ada Colau"`
- `pedro-sanchez` → `--guest "Pedro Sanchez"`
- `gabriel-rufian-and-irene-montero` → `--guest "Gabriel Rufian" --guest2 "Irene Montero"`

Guest arguments apply **only to RTVE files** (the third dot-segment of the filename is `rtve`). For YouTube files omit `--guest` entirely — the script ignores it but omitting keeps the call clean.

---

## Step 4 — Run the script

```bash
venv/bin/python3 scripts/subtitles_to_transcript.py subtitles/<filename> [--guest "Name"] [--guest2 "Name"]
```

The script writes the transcript automatically to `transcripts/<same-name>.txt`.

---

## Step 5 — Report

After the script exits, confirm to the user where the transcript was saved.
