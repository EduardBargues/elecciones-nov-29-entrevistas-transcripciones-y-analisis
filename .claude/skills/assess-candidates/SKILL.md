---
name: assess-candidates
description: Score all candidates in /transcripts/ against a saved political profile and produce a ranked markdown report. Usage: /assess-candidates {profile-slug}
---

Score every candidate transcript against a user's saved political profile and write a ranked markdown report.

## Setup

**Profile slug** is passed as a CLI argument (e.g. `/assess-candidates eduard-bargues`). If none is provided, ask for it.

1. Load `/political-profiles/{slug}/pp-{slug}.json`. If the file doesn't exist, tell the user and stop.
2. Find all `.txt` files in `/transcripts/`. If none are found, tell the user and stop.
3. Derive each candidate's display name from their filename: strip the path and extension, remove any `-transcript` suffix, replace hyphens with spaces, then title-case it.
   - Example: `pedro-sanchez-transcript.txt` → `Pedro Sanchez`

---

## Scoring

Read each transcript in full. For every criterion in the profile, assign:

| Score | Meaning |
|------:|---------|
| +5 | Strongly aligns — the candidate clearly shares the user's position |
| +1 to +4 | Partially aligns, with caveats or nuance |
| 0 | Topic not meaningfully addressed → mark **N/A**, exclude from weighted average |
| -1 to -4 | Partially opposed |
| -5 | Strongly opposes the user's position |

For each scored criterion (score ≠ N/A), identify **one short direct quote** from the transcript (in Spanish, verbatim) that best justifies the score.

**Weighted score formula** (per candidate, over non-N/A criteria only):

```
weighted_score = Σ(weight_i × score_i) / Σ(weight_i)
```

Result is a value in the range -5 to +5. Round to two decimal places.

When writing the narrative, use the `firmness` field as additional context: a misalignment on a firmness-5 criterion is a dealbreaker worth calling out explicitly, even if its numerical impact on the score is similar to other criteria.

---

## Output

Write the report to `/political-profiles/{slug}/assessment-{slug}-{date}.md` where `{date}` is today's date in YYYY-MM-DD format.

The entire report must be written **in Spanish**.

---

### Report format

```markdown
# Evaluación de candidatos — {profile display name}
*Perfil: {slug} · Fecha: {date}*

---

## Mejor candidato/a: {winner name} ({winner score}/5)

{2–3 sentences explaining why this candidate scored highest, naming their strongest alignments
and any notable gaps.}

---

## Tabla comparativa

| Criterio (peso) | {Candidate A} | {Candidate B} | {Candidate C} | {Candidate D} |
|:----------------|:-------------:|:-------------:|:-------------:|:-------------:|
| Vivienda (8) | +3 | -1 | N/A | +4 |
| Inmigración (6) | +1 | +5 | -2 | 0 |
| *(one row per criterion)* | | | | |
| **Puntuación total** | **+1.84** | **+2.10** | **-0.73** | **+0.45** |

*Escala: -5 (totalmente opuesto) a +5 (totalmente alineado). N/A = tema no abordado en la entrevista y excluido del cálculo.*

---

## Análisis por candidato/a

### {Candidate A} — Puntuación: {score}

{One paragraph: overall fit, standout alignments, notable gaps or dealbreakers (call out
firmness-5 misalignments explicitly).}

**Citas relevantes:**
- **{Criterion label}** ({score:+d}): "{verbatim quote from transcript}"
- **{Criterion label}** ({score:+d}): "{verbatim quote from transcript}"
*(one entry per scored criterion — omit N/A criteria)*

---

*(repeat for each candidate, ordered from highest to lowest weighted score)*
```

After writing the file, print:

> "Informe guardado en `/political-profiles/{slug}/assessment-{slug}-{date}.md`.
> El/la candidato/a mejor valorado/a es **{winner}** con una puntuación de **{winner_score}/5**."
