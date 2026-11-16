# Nov-29 Elections · Political Interview Transcripts

Speaker-labeled transcripts of political interviews broadcast ahead of the Spanish general elections on November 29, 2026.

---

## File naming convention

All files follow a consistent scheme across `subtitles/` and `transcripts/`:

```
{candidate}.{program}.{platform}.{language}.ext
```

Example: `ada-colau.la-revuelta.rtve.es.vtt` / `.txt`

---

## One-time setup

```bash
brew install yt-dlp
python3 -m venv venv && source venv/bin/activate
pip install -r scripts/requirements.txt --index-url https://pypi.org/simple/
```

---

## Sources

| Candidate | Program | URL | Slug |
|---|---|---|---|
| Ada Colau | La Revuelta (RTVE) | https://www.rtve.es/play/videos/la-revuelta/programa-10-11-26-ada-colau/17308865/ | `ada-colau.la-revuelta` |
| Santiago Abascal | La Revuelta (RTVE) | https://www.rtve.es/play/videos/la-revuelta/programa-09-11-26-santiago-abascal/17306884/ | `santiago-abascal.la-revuelta` |
| Pedro Sánchez | La Revuelta (RTVE) | https://www.rtve.es/play/videos/la-revuelta/programa-22-10-2026-pedro-sanchez/17279095/ | `pedro-sanchez.la-revuelta` |
| Gabriel Rufián & Irene Montero | La Revuelta (RTVE) | https://www.rtve.es/play/videos/la-revuelta/programa-27-10-2026-gabriel-rufian-irene-montero-fernandocosta-dollar-selmouni/17286287/ | `gabriel-rufian-and-irene-montero.la-revuelta` |
| Ada Colau | The Wild Project (YouTube) | https://www.youtube.com/watch?v=-ESmAhdixfo | `ada-colau.the-wild-project` |
| Alberto Núñez Feijóo | The Wild Project (YouTube) | https://www.youtube.com/watch?v=1YlGArMx_N4 | `feijoo.the-wild-project` |
| Pedro Sánchez | The Wild Project (YouTube) | https://www.youtube.com/watch?v=mStOFBvToUI | `pedro-sanchez.the-wild-project` |

