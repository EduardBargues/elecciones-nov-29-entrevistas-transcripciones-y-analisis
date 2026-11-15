---
name: build-political-profile
description: Interview the user to build a political candidate assessment profile. Saves a weighted rubric of the user's criteria and positions to a JSON file under /political-profiles/{name}/.
---

Build a political assessment profile by conducting a structured interview. The resulting JSON file is used by `/assess-candidates` to score candidates against the user's values and priorities.

## Setup

**Determine the profile name**: use the name passed as a CLI argument (e.g. `/build-political-profile Eduard Bargues`). If none provided, ask: "¿Cuál es tu nombre completo?"

Slugify the name for paths: lowercase, strip accents, replace spaces with hyphens (e.g. `Eduard Bargués` → `eduard-bargues`).

- Profile folder: `/political-profiles/{slug}/`
- Profile file: `/political-profiles/{slug}/pp-{slug}.json`

**Check for an existing profile** at that path.

- If it **exists**, ask:
  > "Ya existe un perfil para **{name}**. ¿Quieres reconstruirlo desde cero o editar criterios concretos? (reconstruir / editar)"
  - **Reconstruir**: run the full interview below.
  - **Editar**: show the existing criteria list (label, current weight, firmness) and ask which ones to change. Re-interview only those. Skip to the save step when done.
- If it **doesn't exist**, run the full interview.

---

## Full interview

### Step 1 — Topic selection

Present the 16 predefined topics and ask the user to reply with the numbers they care about (or "todos"):

```
Estos son los temas predefinidos. Responde con los números que te importan (o "todos"):

 1. Vivienda                     — Alquiler, fondos buitre, regulación del mercado inmobiliario y vivienda pública
 2. Inmigración                  — Gestión de flujos migratorios, integración, fronteras y Ceuta
 3. Empleo y salarios            — Salario mínimo, reforma laboral, temporalidad y reducción de jornada
 4. Economía y coste de vida     — Inflación, pensiones, ingreso mínimo vital, impuestos y desigualdad fiscal
 5. Sanidad pública              — Financiación, listas de espera y defensa frente a privatizaciones
 6. Educación pública            — Financiación, modelo educativo y acceso universal
 7. Cambio climático y energía   — Transición energética, renovables, energía nuclear y gestión de desastres (DANA)
 8. Corrupción e instituciones   — Corrupción política, separación de poderes e independencia judicial
 9. Cuestión territorial         — Cataluña, amnistía, referéndum y modelo de Estado (centralismo vs. descentralización)
10. Democracia y libertades      — Extrema derecha, polarización, ley mordaza y memoria histórica
11. Política internacional       — Gaza, Ucrania, Trump, OTAN, Marruecos y relaciones exteriores
12. Medios de comunicación       — Independencia de medios públicos, pluralismo y lucha contra la desinformación
13. Género y derechos LGTBI      — Violencia de género, ley trans, feminismo e igualdad
14. Tecnología y redes sociales  — IA, regulación de plataformas, menores en redes y poder de las tecnológicas
15. Juventud y oportunidades     — Acceso de los jóvenes a empleo, vivienda y movilidad social
16. Infraestructuras             — Inversión en transporte, ferrocarril y seguridad de infraestructuras
```

### Step 2 — Drill into each selected topic

For each selected topic, send a single message with these three questions and wait for the answer before moving to the next topic:

```
**{Topic label}** — {description}

1. **Importancia (1–10)**: ¿Cuánto peso tiene este tema para ti a la hora de valorar a un candidato?
   (1 = poco relevante, 10 = decisivo)

2. **Posición**: ¿Qué postura ideal buscas en un candidato sobre este tema? Descríbela con tus palabras.

3. **Firmeza (1–5)**: ¿Cuánto te importa que el candidato comparta exactamente tu postura?
   (1 = es un deseo, 5 = es línea roja)
```

### Step 3 — Custom topics

After all predefined topics, ask:

> "¿Hay algún tema que no hayamos cubierto y que sea importante para ti? Si es así, descríbelo brevemente. Si no, escribe 'no'."

For each custom topic the user provides, ask the same three questions (importancia, posición, firmeza). Then ask "¿Algún tema más?" and repeat until they say no.

---

## Save the profile

Create the directory `/political-profiles/{slug}/` if it doesn't exist. Write the file `/political-profiles/{slug}/pp-{slug}.json` with this schema:

```json
{
  "name": "Eduard Bargués",
  "slug": "eduard-bargues",
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD",
  "criteria": [
    {
      "id": "vivienda",
      "label": "Vivienda",
      "description": "Acceso a vivienda asequible en compra y alquiler",
      "weight": 8,
      "position": "El Estado debe construir vivienda pública y regular el precio del alquiler.",
      "firmness": 4
    }
  ]
}
```

Field notes:
- `id`: slugified label (lowercase, hyphens, no accents).
- `created_at`: today's date if creating; keep original if editing.
- `updated_at`: always today's date.

After saving, confirm:

> "Perfil guardado en `/political-profiles/{slug}/pp-{slug}.json` con {N} criterios. Usa `/assess-candidates {slug}` para evaluar candidatos."
