---
name: download-subtitles-from-url
description: Download the Spanish subtitle file from an RTVE or YouTube URL. Usage: /download-subtitles-from-url <URL> <candidate>.<program>
---

Download a VTT subtitle file from a video URL and save it to `subtitles/` using the repository naming convention.

## Invocation

Two arguments are required:
1. The video URL (RTVE or YouTube)
2. A slug in the form `{candidate}.{program}` — e.g. `ada-colau.la-revuelta`

If either argument is missing, show the correct usage and stop:

```
Usage: /download-subtitles-from-url <URL> <candidate>.<program>

Example:
  /download-subtitles-from-url https://www.rtve.es/.../17308865/ ada-colau.la-revuelta
  /download-subtitles-from-url https://www.youtube.com/watch?v=... pedro-sanchez.the-wild-project
```

---

## Step 1 — Install yt-dlp if absent

Check whether `yt-dlp` is available:

```bash
which yt-dlp
```

If not found, install it:

```bash
brew install yt-dlp
```

---

## Step 2 — Detect platform from the URL

| URL contains | Platform |
|---|---|
| `rtve.es` | `rtve` |
| `youtube.com` or `youtu.be` | `youtube` |

If the domain is not recognised, tell the user and stop.

---

## Step 3 — Build the output filename

Combine the slug argument and the detected platform (do **not** include the language — `yt-dlp` appends it automatically):

```
{candidate}.{program}.{platform}
```

Example: `ada-colau.la-revuelta` + `rtve` → `ada-colau.la-revuelta.rtve`

The output path passed to `yt-dlp` will be `subtitles/{candidate}.{program}.{platform}`.
`yt-dlp` will produce `subtitles/{candidate}.{program}.{platform}.es.vtt`.

---

## Step 4 — Download the subtitle file

**RTVE** (official subtitles only):
```bash
yt-dlp --write-subs --skip-download --sub-langs "es" \
  -o "subtitles/{candidate}.{program}.{platform}" "<URL>"
```

**YouTube** (official subtitles, auto-generated as fallback):
```bash
yt-dlp --write-subs --write-auto-subs --skip-download --sub-langs "es" \
  -o "subtitles/{candidate}.{program}.{platform}" "<URL>"
```

---

## Step 5 — Report

Confirm the file saved to `subtitles/{candidate}.{program}.{platform}.es.vtt` (yt-dlp appends `.es.vtt` to the output template automatically).

If `yt-dlp` exits with an error or no subtitle file is found, report the error clearly and stop.
