---
name: generate-political-profile-from-transcript
description: Generate a political profile from an interview transcript. Usage: /generate-political-profile-from-transcript <transcript-file>
---

Generate a JSON + prose political profile of the interview candidate from a transcript file. The profile captures political positions expressed during the interview, with supporting quotes, written in Spanish.

## Invocation

One argument is required: the transcript file (bare filename or path).

If missing, show usage and stop:

```
Usage: /generate-political-profile-from-transcript <transcript-file>

Example:
  /generate-political-profile-from-transcript ada-colau.la-revuelta.rtve.es.txt
  /generate-political-profile-from-transcript transcripts/pedro-sanchez.the-wild-project.youtube.es.txt
```

---

## Step 1 — Resolve the input file

The argument may be:
- A bare filename: `ada-colau.la-revuelta.rtve.es.txt` → look for it under `transcripts/`
- A path: `transcripts/ada-colau.la-revuelta.rtve.es.txt` → use as-is

If the file cannot be found, tell the user and stop.

---

## Step 2 — Derive metadata from the filename

The filename follows the convention `{candidate}.{program}.{platform}.{language}.txt`.

Extract:
- **slug**: the filename without `.txt` — e.g. `ada-colau.la-revuelta.rtve.es`
- **candidate name**: first dot-segment, hyphens → spaces, title-cased. Handle `-and-` as a separator for joint guests:
  - `ada-colau` → `Ada Colau`
  - `pedro-sanchez` → `Pedro Sanchez`
  - `gabriel-rufian-and-irene-montero` → `Gabriel Rufian & Irene Montero`
- **program**: second dot-segment, hyphens → spaces, title-cased — e.g. `La Revuelta`, `The Wild Project`
- **platform**: third dot-segment — `rtve` or `youtube`

---

## Step 3 — Read the transcript

Read the full transcript file.

**RTVE format** — every line is prefixed with `[Speaker Name]`. Lines prefixed with `[Broncano]` or `[Colaborador]` are the host/co-host. All other prefixed lines are the candidate(s). Read host lines for context (they frame questions and challenges) but extract positions only from candidate lines.

**YouTube format** — no speaker labels. The text is a continuous mix of interviewer questions and candidate answers. Analyze the full text to extract the candidate's positions.

---

## Step 4 — Extract political topics and positions

Identify all substantive political or ideological topics discussed in the interview. Topics must be **dynamically extracted** from what was actually covered — do not impose a fixed list. If a topic was not discussed, do not include it.

For each topic:
- Write a **position statement** (2–4 sentences in Spanish) summarising the candidate's expressed view
- Select **1–3 verbatim quotes** in Spanish from the transcript that best support the position. Quotes must be exact text from the file.

Aim for 5–10 topics per interview depending on depth of coverage.

---

## Step 5 — Write the JSON profile

Create `political-profiles/transcripts/{slug}/` if it does not exist.

Write to `political-profiles/transcripts/{slug}/{slug}.json`:

```json
{
  "candidate": "<candidate name>",
  "program": "<program name>",
  "platform": "<platform>",
  "source_file": "transcripts/<filename>",
  "topics": [
    {
      "topic": "<topic name in Spanish>",
      "position": "<position statement in Spanish>",
      "quotes": [
        "<verbatim quote 1>",
        "<verbatim quote 2>"
      ]
    }
  ]
}
```

---

## Step 6 — Write the prose profile

Write to `political-profiles/transcripts/{slug}/{slug}.md`:

```markdown
# Perfil político: {candidate name}
**Programa**: {program} · **Fecha de análisis**: {today's date}

## Resumen

<3–5 sentence overview of the candidate's overall ideological positioning as expressed in this interview>

## Posiciones por tema

### {Topic 1}
<2–4 sentence narrative of the position, weaving in the most illustrative quote>

### {Topic 2}
...
```

---

## Step 7 — Report

Tell the user:
- How many topics were extracted
- The paths of both output files
