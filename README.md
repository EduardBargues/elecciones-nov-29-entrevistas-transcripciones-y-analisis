# Elecciones 29-N · Transcripciones de entrevistas políticas

Transcripciones con identificación de hablante de cuatro entrevistas políticas emitidas en RTVE antes de las elecciones generales del 29 de noviembre de 2026.

---

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `vtt_to_transcript.py` | Script Python que convierte subtítulos VTT de RTVE en transcripciones etiquetadas por hablante |
| `subtitles/ada-colau.es.vtt` | Subtítulos originales descargados de RTVE — entrevista con Ada Colau |
| `subtitles/santiago-abascal.es.vtt` | Subtítulos originales — entrevista con Santiago Abascal |
| `subtitles/pedro-sanchez.es.vtt` | Subtítulos originales — entrevista con Pedro Sánchez |
| `subtitles/rufian-montero.es.vtt` | Subtítulos originales — entrevista con Gabriel Rufián e Irene Montero |
| `transcripts/ada-colau-transcript.txt` | Transcripción limpia con hablantes identificados |
| `transcripts/santiago-abascal-transcript.txt` | Transcripción limpia con hablantes identificados |
| `transcripts/pedro-sanchez-transcript.txt` | Transcripción limpia con hablantes identificados |
| `transcripts/rufian-montero-transcript.txt` | Transcripción limpia con hablantes identificados |
| `.claude/skills/build-political-profile/` | Skill de Claude Code para construir un perfil político personalizado |
| `.claude/skills/assess-candidates/` | Skill de Claude Code para puntuar candidatos contra un perfil guardado |

---

## Análisis de candidatos con Claude Code

Este repositorio incluye dos skills de [Claude Code](https://claude.ai/code) que permiten evaluar a los candidatos de forma personalizada: primero construyes tu propio perfil político (qué temas te importan y qué postura buscas), y después el sistema lee las transcripciones y puntúa a cada candidato contra ese perfil.

**Requisito:** tener Claude Code instalado (`npm install -g @anthropic-ai/claude-code`).

### Paso 1 — Construir tu perfil político

```
/build-political-profile Tu Nombre
```

El skill te hace una entrevista estructurada en torno a 16 temas extraídos directamente de las transcripciones (vivienda, inmigración, cambio climático, cuestión territorial, etc.). Para cada tema que selecciones, te pregunta:

- **Importancia (1–10):** cuánto peso tiene este tema para ti.
- **Posición:** qué postura buscas en un candidato, con tus propias palabras.
- **Firmeza (1–5):** si es un deseo (1) o una línea roja (5).

Al terminar puedes añadir temas propios que no estén en la lista. El perfil se guarda en:

```
political-profiles/{tu-nombre}/pp-{tu-nombre}.json
```

> Esta carpeta está en `.gitignore` — tus criterios son privados y nunca se suben al repositorio.

Si ya tienes un perfil guardado, el skill te preguntará si quieres reconstruirlo desde cero o editar criterios concretos.

### Paso 2 — Puntuar a los candidatos

```
/assess-candidates {tu-nombre}
```

El skill lee tu perfil y todas las transcripciones en `transcripts/`. Para cada candidato y cada criterio que seleccionaste, asigna una puntuación de **-5 a +5** (donde 0 significa que el tema no fue abordado en la entrevista) e incluye una cita directa de la transcripción que justifica la puntuación.

El informe resultante se guarda en:

```
political-profiles/{tu-nombre}/assessment-{tu-nombre}-{fecha}.md
```

El informe contiene:

1. **Mejor candidato/a** — quién encaja mejor con tu perfil y por qué.
2. **Tabla comparativa** — filas por tema, columnas por candidato, puntuación ponderada final.
3. **Análisis por candidato** — párrafo de valoración y citas relevantes para cada uno.

---

## Metodología

### Paso 1 — Descarga de subtítulos con `yt-dlp`

Los vídeos están alojados en la plataforma de RTVE (`rtve.es/play`). RTVE publica subtítulos oficiales en formato [WebVTT](https://www.w3.org/TR/webvtt1/) para cumplir con los requisitos de accesibilidad de la televisión pública.

Usamos [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) para descargar únicamente el archivo de subtítulos en español, sin descargar el vídeo:

```bash
yt-dlp --write-subs --skip-download --sub-langs "es" -o "<nombre>" "<URL_DEL_EPISODIO>"
```

Esto genera un archivo `.es.vtt` con los subtítulos completos del episodio.

### Paso 2 — Procesado del VTT con `vtt_to_transcript.py`

El formato VTT crudo contiene marcas de tiempo, etiquetas de color HTML y líneas duplicadas que hay que limpiar. El script hace lo siguiente:

1. **Parsea los bloques VTT** extrayendo texto y marcas de tiempo de cada bloque de subtítulo.
2. **Detecta el inicio de la entrevista** automáticamente.
3. **Clasifica cada línea** por hablante según las etiquetas de color.
4. **Fusiona líneas consecutivas** del mismo hablante en un único turno de palabra.
5. **Elimina duplicados** consecutivos idénticos (artefacto habitual en subtítulos de streaming HLS).
6. **Escribe la transcripción** en un archivo `.txt` con el formato `[Hablante] Texto`.

```bash
python3 vtt_to_transcript.py <archivo.es.vtt> --guest "Nombre del Invitado"
```

---

## Sistema de colores en los subtítulos de RTVE

El hallazgo clave del que depende todo el proceso es que **RTVE codifica la identidad del hablante mediante el color de las etiquetas CSS en el VTT**. Es una convención estándar de la subtitulación televisiva para facilitar la lectura en pantalla.

El programa usa el siguiente esquema de colores:

| Etiqueta VTT | Hablante |
|---|---|
| `<c.yellow>texto</c>` | David Broncano (presentador) |
| `<c.green>texto</c>` | Colaborador / copresentador |
| `<c.magenta>texto</c>` | Colaborador / copresentador |
| *(sin etiqueta de color)* | Invitado principal (a partir del inicio de la entrevista) |

Ejemplo de bloque VTT original:

```
00:36:49.788 --> 00:36:51.291 line:77%
No sabía si sacar el tema o no.

00:36:51.292 --> 00:36:52.316 line:77%
<c.yellow>Puedes sacarlo.</c>
```

La línea sin color es el invitado; la amarilla es Broncano.

---

## Detección automática del inicio de la entrevista

Cada episodio tiene una parte inicial en la que Broncano habla con su equipo, con el público o con colaboradores antes de presentar al invitado. Durante esa fase previa, las líneas **sin color no pertenecen al invitado** sino a otras personas en plató.

Para no atribuir esas líneas al invitado, el script detecta automáticamente el momento en que comienza la entrevista:

> Se busca el primer bloque de texto amarillo (Broncano) que contenga el nombre del invitado como palabra completa (con límites de palabra `\b` para evitar coincidencias parciales, como «ada» dentro de «nada»).

La marca de tiempo de ese bloque se usa como **umbral**: todas las líneas sin color anteriores a ese instante se descartan, y las posteriores se atribuyen al invitado.

```
Interview start detected at 00:24:08  ← Ada Colau
Interview start detected at 00:06:53  ← Santiago Abascal
Interview start detected at 00:04:44  ← Pedro Sánchez
Interview start detected at 00:04:56  ← Rufián / Montero
```

---

## Decisiones tomadas y casos especiales

### Entrevista con Pedro Sánchez — aparición de Candela Peña

Al final del episodio (a partir del turno 577), la actriz Candela Peña se une en plató a Broncano y Pedro Sánchez en un segmento informal. Como también habla sin etiqueta de color, sus líneas serían atribuidas incorrectamente a Sánchez.

**Decisión:** se trunca la transcripción en el turno 576, justo antes de que Broncano la presente. El segmento con Candela Peña no es políticamente relevante para el análisis y se descarta.

### Entrevista con Gabriel Rufián e Irene Montero — dos invitados sin color

Ambos políticos comparten episodio y, al igual que cualquier invitado único, sus líneas aparecen sin etiqueta de color en el VTT. RTVE no les asigna colores diferenciados.

**Decisión:** dado que es imposible distinguir automáticamente quién habla en cada línea sin color, todas las intervenciones del invitado se etiquetan como `[Rufián / Montero]`, indicando que la línea pertenece a uno de los dos sin poder precisar cuál.

Además, al final del episodio aparecen los raperos Fernando Costa y Dollar Selmouni (autores de la cabecera del programa). La transcripción se trunca antes de su presentación (turno 473) por el mismo motivo que con Candela Peña.

---

## Limitaciones conocidas

- **Direcciones de escena residuales:** algunas etiquetas entre paréntesis como `(PÚBLICO)` o `(ININTELIGIBLE)` aparecen mezcladas con texto real en el mismo bloque VTT, por lo que el filtro de acotaciones no las elimina completamente.
- **Turnos mezclados:** en momentos de intervención múltiple simultánea, varias voces aparecen en el mismo bloque sin color, y el script las agrupa bajo el mismo hablante activo.
- **Heurística de inicio de entrevista:** la detección se basa en la primera mención del nombre del invitado en texto amarillo. Si el nombre aparece antes en otro contexto (referencia a una entrevista anterior, etc.), el umbral podría adelantarse.
- **Colaboradores sin nombre:** las líneas verdes y magenta se etiquetan genéricamente como `[Colaborador]` sin identificar a qué miembro del equipo pertenecen.

---

## Uso del script con otros episodios

El script es reutilizable con cualquier programa de RTVE con el mismo esquema de colores:

```bash
# 1. Descargar subtítulos
yt-dlp --write-subs --skip-download --sub-langs "es" -o "<nombre>" "<URL>"

# 2. Generar transcripción
python3 vtt_to_transcript.py <nombre>.es.vtt --guest "Nombre Completo"

# Con dos invitados (etiqueta combinada)
python3 vtt_to_transcript.py <nombre>.es.vtt --guest "Invitado 1 / Invitado 2"
```

**Requisitos:** Python 3.8+ y `yt-dlp` (`brew install yt-dlp` en macOS).

---

## Fuente

Los vídeos y subtítulos son propiedad de [RTVE](https://www.rtve.es) y se encuentran disponibles públicamente en su plataforma de vídeo a la carta. Este repositorio contiene únicamente las transcripciones derivadas para fines de análisis e investigación.
