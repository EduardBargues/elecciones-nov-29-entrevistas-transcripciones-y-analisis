# Nov-29 Elections · Political Interview Transcripts

Speaker-labeled transcripts of four political interviews broadcast on television ahead of the Spanish general elections on November 29, 2026.

---

## Repository Contents

| File | Description |
|---|---|
| `vtt_to_transcript.py` | Python script that converts VTT subtitles into speaker-labeled transcripts |
| `subtitles/ada-colau.es.vtt` | Original subtitles — interview with Ada Colau |
| `subtitles/santiago-abascal.es.vtt` | Original subtitles — interview with Santiago Abascal |
| `subtitles/pedro-sanchez.es.vtt` | Original subtitles — interview with Pedro Sánchez |
| `subtitles/rufian-montero.es.vtt` | Original subtitles — interview with Gabriel Rufián and Irene Montero |
| `transcripts/ada-colau-transcript.txt` | Clean transcript with identified speakers |
| `transcripts/santiago-abascal-transcript.txt` | Clean transcript with identified speakers |
| `transcripts/pedro-sanchez-transcript.txt` | Clean transcript with identified speakers |
| `transcripts/rufian-montero-transcript.txt` | Clean transcript with identified speakers |
| `.claude/skills/build-political-profile/` | Claude Code skill to build a personalised political assessment profile |
| `.claude/skills/assess-candidates/` | Claude Code skill to score candidates against a saved profile |

---

## Candidate Analysis with Claude Code

This repository includes two [Claude Code](https://claude.ai/code) skills that let you assess candidates against your own political values: first you build a personal profile (which topics matter to you and what stance you are looking for), then the system reads the transcripts and scores each candidate against that profile.

**Requirement:** Claude Code installed (`npm install -g @anthropic-ai/claude-code`).

### Step 1 — Build your political profile

```
/build-political-profile Your Name
```

The skill runs a structured interview around 16 topics extracted directly from the transcripts (housing, immigration, climate and energy, territorial question, etc.). For each topic you select, it asks:

- **Importance (1–10):** how much weight this topic carries for you.
- **Position:** what stance you are looking for in a candidate, in your own words.
- **Firmness (1–5):** whether this is a preference (1) or a dealbreaker (5).

After the predefined topics you can add any topic not on the list. The profile is saved to:

```
political-profiles/{your-name}/pp-{your-name}.json
```

> This folder is in `.gitignore` — your criteria are private and never pushed to the repository.

If a profile already exists for that name, the skill will ask whether you want to rebuild it from scratch or edit specific criteria.

### Step 2 — Score the candidates

```
/assess-candidates {your-name}
```

The skill loads your profile and reads all transcripts in `transcripts/`. For each candidate and each criterion you chose, it assigns a score from **-5 to +5** (0 means the topic was not addressed in the interview) and includes a direct quote from the transcript to justify the score.

The resulting report is saved to:

```
political-profiles/{your-name}/assessment-{your-name}-{date}.md
```

The report contains:

1. **Best candidate** — who fits your profile best and why.
2. **Comparison table** — rows by topic, columns by candidate, weighted total score.
3. **Per-candidate analysis** — a summary paragraph and supporting quotes for each candidate.

---

## Methodology

### Step 1 — Downloading subtitles with `yt-dlp`

Television broadcasters publish official subtitles in [WebVTT](https://www.w3.org/TR/webvtt1/) format to comply with accessibility requirements.

We used [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) to download only the Spanish subtitle file, without downloading the video:

```bash
yt-dlp --write-subs --skip-download --sub-langs "es" -o "<name>" "<EPISODE_URL>"
```

This produces an `.es.vtt` file containing the full subtitles for the episode.

### Step 2 — Processing the VTT with `vtt_to_transcript.py`

The raw VTT format contains timestamps, HTML color tags, and duplicate lines that need to be cleaned up. The script does the following:

1. **Parses VTT blocks**, extracting text and timestamps from each subtitle block.
2. **Automatically detects the interview start.**
3. **Classifies each line** by speaker based on color tags.
4. **Merges consecutive lines** from the same speaker into a single turn.
5. **Removes consecutive duplicates** (a common artifact in HLS streaming subtitles).
6. **Writes the transcript** to a `.txt` file in `[Speaker] Text` format.

```bash
python3 vtt_to_transcript.py <file.es.vtt> --guest "Guest Full Name"
```

---

## VTT Subtitle Color System

The key insight the entire process depends on is that **VTT files encode speaker identity through CSS color tags**. This is a standard television subtitling convention to aid on-screen readability.

The programme uses the following color scheme:

| VTT Tag | Speaker |
|---|---|
| `<c.yellow>text</c>` | David Broncano (host) |
| `<c.green>text</c>` | Collaborator / co-host |
| `<c.magenta>text</c>` | Collaborator / co-host |
| *(no color tag)* | Main guest (from the interview start onwards) |

Example of a raw VTT block:

```
00:36:49.788 --> 00:36:51.291 line:77%
No sabía si sacar el tema o no.

00:36:51.292 --> 00:36:52.316 line:77%
<c.yellow>Puedes sacarlo.</c>
```

The uncolored line is the guest; the yellow line is Broncano.

---

## Automatic Interview Start Detection

Each episode has an opening segment in which Broncano talks with his team, the audience, or collaborators before introducing the guest. During that pre-interview phase, **uncolored lines do not belong to the guest** but to other people on set.

To avoid attributing those lines to the guest, the script automatically detects when the interview begins:

> It searches for the first yellow text block (Broncano) that contains the guest's name as a whole word (using `\b` word boundaries to avoid partial matches, such as «ada» inside «nada»).

The timestamp of that block is used as a **cutoff**: all uncolored lines before that moment are discarded, and those after it are attributed to the guest.

```
Interview start detected at 00:24:08  ← Ada Colau
Interview start detected at 00:06:53  ← Santiago Abascal
Interview start detected at 00:04:44  ← Pedro Sánchez
Interview start detected at 00:04:56  ← Rufián / Montero
```

---

## Special Cases and Decisions

### Pedro Sánchez interview — Candela Peña's appearance

Towards the end of the episode (from turn 577 onwards), actress Candela Peña joins Broncano and Pedro Sánchez on set for an informal segment. Since she also speaks without a color tag, her lines would be incorrectly attributed to Sánchez.

**Decision:** the transcript is truncated at turn 576, just before Broncano introduces her. The segment with Candela Peña is not politically relevant for analysis and is discarded.

### Gabriel Rufián and Irene Montero interview — two uncolored guests

Both politicians share the episode and, like any single guest, their lines appear without a color tag in the VTT. The broadcaster does not assign them different colors.

**Decision:** since it is impossible to automatically distinguish who is speaking in each uncolored line, all guest turns are labeled `[Rufián / Montero]`, indicating that the line belongs to one of the two without being able to specify which.

Additionally, rappers Fernando Costa and Dollar Selmouni (authors of the show's theme song) appear at the end of the episode. The transcript is truncated before their introduction (turn 473) for the same reason as with Candela Peña.

---

## Known Limitations

- **Residual stage directions:** some parenthetical labels such as `(PÚBLICO)` or `(ININTELIGIBLE)` appear mixed with real speech in the same VTT block, so the stage direction filter does not remove them completely.
- **Mixed turns:** during moments of simultaneous multiple speech, several voices appear in the same uncolored block and the script groups them under the same active speaker.
- **Interview start heuristic:** detection relies on the first mention of the guest's name in yellow text. If the name appears earlier in a different context (e.g. a reference to a previous interview), the cutoff could be set too early.
- **Unnamed collaborators:** green and magenta lines are generically labeled `[Colaborador]` without identifying which team member they belong to.

---

## Using the Script with Other Episodes

The script is reusable with any programme that uses the same VTT color scheme:

```bash
# 1. Download subtitles
yt-dlp --write-subs --skip-download --sub-langs "es" -o "<name>" "<URL>"

# 2. Generate transcript
python3 vtt_to_transcript.py <name>.es.vtt --guest "Full Name"

# With two guests (combined label)
python3 vtt_to_transcript.py <name>.es.vtt --guest "Guest 1 / Guest 2"
```

**Requirements:** Python 3.8+ and `yt-dlp` (`brew install yt-dlp` on macOS).

---

## Source

The videos and subtitles are the property of their respective broadcasters and are publicly available on their platforms. This repository contains only the derived transcripts for analysis and research purposes.
