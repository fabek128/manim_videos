# Generador de noticias por niveles

`scripts/generate_news.py` orquesta investigación, análisis editorial,
recursos visuales y piezas de noticias sin publicar automáticamente.

```text
nivel 1: URL única -> extracción -> PromptGate -> screenshot -> Vision QA -> pieza mínima
nivel 2: tema -> búsqueda -> 3 fuentes -> PromptGate -> informe + opciones -> elección -> piezas
nivel 3: tema -> búsqueda ampliada -> hasta 6 fuentes -> contraste profundo -> informe + opciones -> elección -> piezas
```

## Requisitos

```bash
uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
```

El análisis editorial usa `PROMPTGATE_MODEL` (en este proyecto: `coder-rata`).
La validación visual usa `PROMPTGATE_VISION_MODEL` si está configurado o
`OPENROUTER_VISION_MODEL` con `OPENROUTER_API_KEY`.

## Niveles

### Nivel 1 — Fuente única

Para cuando ya tenés el artículo y querés una noticia mínima.

```bash
python scripts/generate_news.py \
  --level 1 \
  --url "https://ejemplo.com/noticia" \
  --format short
```

Hace lo siguiente:

1. valida que la URL sea HTTP(S);
2. descarga un máximo de 4 MiB y extrae título, metadata y texto visible;
3. manda el contenido delimitado a PromptGate como datos no confiables;
4. genera un análisis estructurado con hecho, titular, descripción,
   desarrollo, actores, estado y datos sin confirmar;
5. captura la URL una vez con Playwright y HiDPI;
6. valida el screenshot con Vision QA;
7. genera una pieza breve, `brief.md`, `informe.md`, `caption.md` y `post.txt`.

No busca otras fuentes. El resultado no debe marcarse como confirmado si el
artículo no alcanza el estándar editorial de fuentes primarias.

### Nivel 2 — Búsqueda relacionada

Para una consulta de tema. Busca hasta 3 resultados, intenta leerlos y
entrega un informe antes de crear una pieza.

```bash
# Primera etapa: informe + opciones; no genera PNG todavía
python scripts/generate_news.py \
  --level 2 \
  --topic "nuevo modelo de IA de OpenAI"

# Segunda etapa: se elige una opción y se genera un carrusel esencial
python scripts/generate_news.py \
  --level 2 \
  --topic "nuevo modelo de IA de OpenAI" \
  --select 1 \
  --format carousel3
```

El informe separa `Confirmado`, `Sin confirmar`, `Contradicciones`, `No
encontrado` y propone entre 2 y 5 ángulos. El primer comando es el gate
editorial: el usuario debe revisar las opciones antes de producir la pieza.
Si PromptGate devuelve una salida truncada o no parseable, el script no
inventa una interpretación: conserva las fuentes, deja el fallo en el log y
genera opciones de contingencia derivadas literalmente de títulos/textos de
las fuentes, marcando `Refinamiento editorial de IA` como pendiente.

### Nivel 3 — Investigación profunda

Para temas importantes o ambiguos. Busca hasta 8 resultados, contrasta hasta
6 fuentes legibles y solicita a PromptGate una comparación más profunda.

```bash
python scripts/generate_news.py \
  --level 3 \
  --topic "nuevo modelo de IA de OpenAI"

python scripts/generate_news.py \
  --level 3 \
  --topic "nuevo modelo de IA de OpenAI" \
  --select 2 \
  --format carousel5
```

Además del estado de los hechos, el informe debe registrar contradicciones,
datos faltantes y la fuente de cada ángulo. La IA no puede convertir una
afirmación de una sola fuente en hecho confirmado.

## Interacción

En una terminal interactiva, si los niveles 2/3 no reciben `--select`, el
script genera primero el informe y luego pregunta en lote el id del ángulo,
el formato y el fondo (`screenshot` o `solid`). En ejecución no interactiva,
imprime la ruta del informe y termina sin generar piezas. Esto evita elegir
por el usuario y evita entregar una noticia sin validación editorial.

Flags principales:

| Flag | Uso |
|---|---|
| `--level 1\|2\|3` | Nivel de carga obligatorio |
| `--url URL` | Fuente única para nivel 1 |
| `--topic TEXTO` | Tema para nivel 2/3 |
| `--select N` | Ángulo elegido del informe |
| `--format short` | 1 slide `cover`, título + descripción breve |
| `--format long` | 1 slide `text`, título + desarrollo |
| `--format carousel3` | cover + qué pasó + por qué importa |
| `--format carousel5` | cover + qué pasó + puntos + impacto + qué sigue |
| `--format story` | Story 9:16 breve |
| `--format story_complete` | Story 9:16 con desarrollo |
| `--visual screenshot\|solid` | Fondo real capturado o sólido |
| `--logo-ref PATH` | Logo real relativo a `assets/`; repetir para varios |
| `--non-interactive` | No preguntar en terminal |

## Archivos de salida

Cada selección crea un proyecto en `tenants/<id>/content/<fecha>_<slug>/`:

```text
brief.md             # hechos, estado, fuentes y faltantes
informe.md           # investigación y opciones editoriales
caption.md           # caption para revisión
post.txt             # texto plano listo para copiar/publicar
vision_review.json   # resultado de cada evaluación visual
assets/              # recursos específicos del proyecto
renders/             # slide_01.png, slide_02.png, ...
```

El YAML de la pieza queda en `tenants/<id>/configs/images/` y referencia el
`content_slug` del proyecto. El script nunca copia nada a
`/Users/fabian/Documents/shared`.

## Formatos visuales

| Formato | Slides | Uso |
|---|---:|---|
| `short` | 1 | Gancho, título y descripción breve |
| `long` | 1 | Título y desarrollo más extenso |
| `carousel3` | 3 | Hecho, qué pasó, por qué importa |
| `carousel5` | 5 | Noticia completa con puntos clave y cierre |
| `story` | 1 | Teaser 9:16, una idea + CTA |
| `story_complete` | 1 | Título, descripción y desarrollo en 9:16 |

Los logos de entidades deben ser reales. El script usa mappings para assets
conocidos (`openai`, `huggingface`, `anthropic`, `google`, `nvidia`) y acepta
`--logo-ref` para assets adicionales. Si hace falta un logo no existente,
descargarlo desde el press kit oficial y documentar su origen antes de
producir el prototipo.

## Vision QA: gate obligatorio

El rol de visión se ejecuta en tres puntos:

1. sobre el screenshot crudo de cada URL;
2. sobre cada PNG final ya compuesto (texto, logos, degradado y fondo);
3. sobre frames representativos si en el futuro el nivel genera video.

El prompt debe comprobar:

- publicidad, banners, suscripciones, cookies, popups, paywalls;
- páginas 404/500, captchas, blank/loading states y fuentes rotas;
- texto cortado, contraste insuficiente y contenido fuera de zonas seguras;
- logos falsos, faltantes o ilegibles;
- texto/degradado sobre ojos, boca o rostro completo;
- texto sobre pantallas, gráficos, código, logos o productos focales;
- texto sobre torso, brazos, piernas o fondo sin ocultar el foco: no es error.

### Loop acotado

```text
render -> vision review
  limpio       -> entregar para revisión del usuario
  sucio        -> corregir/regenerar (intento 1)
  sucio        -> corregir/regenerar (intento 2)
  sucio        -> corregir/regenerar (intento 3)
  sucio        -> 4ta evaluación, detener e informar
```

No existe loop infinito. `vision_review.json` registra `attempts`,
`clean`, `issues`, `confidence` y `status` (`passed` o
`stopped_after_3_retries`). La detección de visión no sustituye la revisión
editorial del brief ni la confirmación de fuentes.

## Seguridad y veracidad

- Solo URLs HTTP(S); no se permite `file://`, `javascript:` ni `data:`.
- Timeout y límite de tamaño de fuente obligatorios.
- El HTML de una fuente se trata como datos, nunca como instrucciones.
- La búsqueda usa resultados públicos y no ejecuta JavaScript del buscador.
- No se publica automáticamente.
- Si falta una fecha, cifra, fuente o logo real: `N/D`, `[SIN CONFIRMAR]` o
  detener producción; nunca completar por inferencia.

## Ejemplos de flujo recomendado

### URL ya conocida

```bash
python scripts/generate_news.py --level 1 \
  --url "https://time.com/article/2026/08/26/openai-sam-altman-interview/" \
  --format short \
  --logo-ref logos/openai/openai_black.svg
```

### Tema nuevo

```bash
# 1. Obtener informe y opciones
python scripts/generate_news.py --level 3 \
  --topic "nuevo modelo de IA de OpenAI"

# 2. Luego de revisar el informe, elegir un ángulo y formato
python scripts/generate_news.py --level 3 \
  --topic "nuevo modelo de IA de OpenAI" \
  --select 1 --format carousel5
```

El segundo comando genera una pieza en borrador y ejecuta Vision QA antes de
mostrar sus paths. La publicación requiere aprobación explícita posterior.
