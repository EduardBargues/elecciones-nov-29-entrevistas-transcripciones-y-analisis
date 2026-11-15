# Elecciones 29-N · Transcripciones de entrevistas en La Revuelta

> 🇬🇧 An English version of this document is available: [README.english.md](README.english.md)

Transcripciones con identificación de hablante de cuatro entrevistas políticas emitidas en **La Revuelta** (RTVE) antes de las elecciones generales del 29 de noviembre de 2026.

---

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `vtt_to_transcript.py` | Script Python que convierte subtítulos VTT de RTVE en transcripciones etiquetadas por hablante |
| `ada-colau.es.vtt` | Subtítulos originales descargados de RTVE — entrevista con Ada Colau |
| `santiago-abascal.es.vtt` | Subtítulos originales — entrevista con Santiago Abascal |
| `pedro-sanchez.es.vtt` | Subtítulos originales — entrevista con Pedro Sánchez |
| `rufian-montero.es.vtt` | Subtítulos originales — entrevista con Gabriel Rufián e Irene Montero |
| `ada-colau-transcript.txt` | Transcripción limpia con hablantes identificados |
| `santiago-abascal-transcript.txt` | Transcripción limpia con hablantes identificados |
| `pedro-sanchez-transcript.txt` | Transcripción limpia con hablantes identificados |
| `rufian-montero-transcript.txt` | Transcripción limpia con hablantes identificados |

---

## Metodología

### Paso 1 — Descarga de subtítulos con `yt-dlp`

Los vídeos de La Revuelta están alojados en la plataforma de RTVE (`rtve.es/play`). RTVE publica subtítulos oficiales en formato [WebVTT](https://www.w3.org/TR/webvtt1/) para cumplir con los requisitos de accesibilidad de la televisión pública.

Los cuatro episodios utilizados son:

| Invitado | URL |
|---|---|
| Ada Colau | https://www.rtve.es/play/videos/la-revuelta/programa-10-11-26-ada-colau/17308865/ |
| Santiago Abascal | https://www.rtve.es/play/videos/la-revuelta/programa-09-11-26-santiago-abascal/17306884/ |
| Pedro Sánchez | https://www.rtve.es/play/videos/la-revuelta/programa-22-10-2026-pedro-sanchez/17279095/ |
| Gabriel Rufián e Irene Montero | https://www.rtve.es/play/videos/la-revuelta/programa-27-10-2026-gabriel-rufian-irene-montero-fernandocosta-dollar-selmouni/17286287/ |

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

La Revuelta usa el siguiente esquema de colores:

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

Cada episodio de La Revuelta tiene una parte inicial en la que Broncano habla con su equipo, con el público o con colaboradores antes de presentar al invitado. Durante esa fase previa, las líneas **sin color no pertenecen al invitado** sino a otras personas en plató.

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

El script es reutilizable con cualquier episodio de La Revuelta (o de cualquier programa de RTVE con el mismo esquema de colores):

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
