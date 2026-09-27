# Agente E32 — Generador de contenido digital

Aplicación personal para crear, revisar y preparar contenido listo para
compartir en internet. El proyecto pertenece a **Agente E32** y también sirve
para promocionar la cuenta de Instagram **[@fabian128k](https://instagram.com/fabian128k)**.

## Propósito

La aplicación centraliza la producción de contenido para internet:

- **Imágenes** para publicaciones, portadas, piezas informativas y recursos
  visuales.
- **Noticias y textos** para posts, captions, resúmenes y contenido editorial.
- **Videos** y animaciones para Reels, Stories, posts y otros formatos sociales.
- **Revisión asistida por IA** para detectar errores, mejorar textos y preparar
  contenido coherente con cada publicación.

Todo el contenido debe mantener la identidad visual y editorial de **Agente E32**.
Cuando corresponda, se prepara para difundir y promocionar
**[@fabian128k](https://instagram.com/fabian128k)**.

El proyecto prioriza piezas reutilizables y data-driven: los datos viven en
JSON cuando corresponde, los videos se generan con escenas parametrizables y
los textos asociados pueden generarse con IA mediante PromptGate.

La arquitectura propuesta para soportar múltiples marcas mediante carpetas está
documentada en [`docs/multi-tenant-folder-design.md`](docs/multi-tenant-folder-design.md).

## Modo agente

El repositorio está preparado para operarse conversacionalmente: el
agente detecta el tenant activo, clasifica lo que pide el usuario
(placa, carrusel, story, video, o desarrollar un tema completo),
investiga, propone prototipos e itera hasta la versión final.

- Protocolo de operación: [`docs/agent-mode.md`](docs/agent-mode.md)
- Plan de construcción pendiente: [`docs/plan-agente-conversacional.md`](docs/plan-agente-conversacional.md)
- Templates de texto: [`templates/posts/`](templates/posts/README.md)
- Templates de diseño: [`templates/prompts/`](templates/README.md)

Ante un pedido como *"escribí algo sobre la compra de X por Y"*, el
agente investiga primero, devuelve un brief con el estado de cada hecho
y recién después redacta. No publica nada sin aprobación explícita.

## Generador de placas y carruseles

Los scripts están separados por responsabilidad. `scripts/generate_images.py`
genera imágenes editoriales; `scripts/generate_videos.py` delega el render de
videos a `build.py`. La IA de OpenRouter produce únicamente la imagen base; el
layout, los textos, los highlights, el degradado y el branding se componen
determinísticamente con Python.

Tecnologías:

- Pillow para canvas, composición y exportación PNG.
- FreeType mediante `PIL.ImageFont` para cargar TTF/OTF.
- OpenCV para crop inteligente, detección opcional de rostros y mejoras visuales.
- Pydantic para validar configuraciones YAML/JSON.
- OpenRouter para imágenes cuando `image_generation.enabled` es `true`.

Instalación:

```bash
uv pip install --python .venv/bin/python -r requirements.txt
```

Generar un post:

```bash
python scripts/generate_images.py post --config post_vertical.yaml
```

Generar un carrusel:

```bash
python scripts/generate_images.py carousel --config carousel_vertical.yaml
```

Para seleccionar un tenant explícito:

```bash
python scripts/generate_images.py --tenant agente32 post --config post_vertical.yaml
```

Los resultados se guardan en el `output_dir` definido por cada configuración
dentro del tenant. Los ejemplos incluidos cubren post cuadrado, post vertical,
Story y carruseles cuadrado/vertical de tres slides. Para usar IA, activar
`image_generation.enabled` y definir un modelo OpenRouter real; los ejemplos
desactivan IA para ser reproducibles y no consumir créditos.

### Fondos reutilizables

El tenant `agente32` tiene fondos verticales reutilizables en
`tenants/agente32/assets/backgrounds/`. Se generaron diez fondos sin texto ni
logos sobre tecnología, IA, robótica y ciencia. Cada fondo pasa por Vision QA
antes de quedar disponible; el manifest y el costo real están en
`assets/backgrounds/manifest.json`, y el detalle de las revisiones en
`assets/backgrounds/vision_review.json`.

Cuando una config no declara `background_image_path`, `image_generation` ni
`web_capture`, `generator.py` selecciona automáticamente uno de esos fondos
de manera determinística por tenant/proyecto/slide. Para conservar el fondo
procedural anterior, declarar `background_mode: "solid"`.

Para regenerar o ampliar la colección:

```bash
python scripts/generate_backgrounds.py --tenant agente32
python scripts/generate_backgrounds.py --tenant agente32 --only 1 4 8 --force
```

Los carruseles también soportan slides `type: "code"`. El código se define en
el campo `code`, envuelto en `<code>...</code>`, y se renderiza con
`assets/fonts/FiraCode-Regular.ttf`, numeración de líneas y panel monoespaciado.

## Multi-tenancy

Los archivos de cada marca viven dentro de `tenants/<tenant_id>/`. El
primer tenant configurado es `agente32`. El código compartido, themes y
assets globales permanecen en la raíz del repositorio.

```text
tenants/agente32/
  configs/images/          # YAML de placas y carruseles
  configs/videos/top/      # JSONs genéricos del top (title/items/audio)
  assets/                  # Logos, fondos, sonidos propios (pisan a global)
  videos/                  # Solo escenas únicas (intro, logos)
  overrides/videos/top/    # Opcional: TopScene que hereda de BaseTopScene
  media/videos/top/<slug>/ # Output tenant-aislado
  tenant.yaml              # Manifest con brand.footer_logos, default_theme, handle

assets/                    # Recursos compartidos (solo lectura)
  backgrounds/             # Pool global para posts y videos
  logos/                   # Logos proveedores reutilizables
generators/videos/top/     # Generador global reutilizable (descriptor + entrypoint)
src/noticia_carrusel/video_generators/top/ # Lógica común
```

La resolución de recursos sigue prioridad tenant → compartido:
un logo `logos/openai/openai_paths.svg` se resuelve primero en el
tenant y, si no existe, en `assets/logos/`.

## Estructura


```text
scripts/
  generate_images.py     # CLI de imágenes y carruseles (tenant-aware)
  generate_videos.py     # CLI de videos; delega en build.py
  publish_final.py       # Publicación con namespace aislado por tenant
  promptgate_client.py   # Cliente OpenAI-compatible para texto
src/noticia_carrusel/    # Configuración, proveedor, visión y render
  web_capture/           # Captura de URLs (Playwright) + cámara zoom/pan
tenants/                 # Carpetas por marca/tenant
templates/               # Prompts de diseño y guías reutilizables
assets/fonts/            # Fuentes TTF/OTF del sistema editorial
```

### Captura web + cámara (zoom/pan)

Screenshots de URLs (Playwright) como fondo de un post, o como clip de
video con zoom/pan animado (OpenCV + ffmpeg, sin Manim). Ver
[`docs/web-capture.md`](docs/web-capture.md).

### Generador de noticias por niveles

Para trabajar desde una URL o investigar un tema completo:

```bash
python scripts/generate_news.py --level 1 \
  --url "https://ejemplo.com/noticia" --format short
python scripts/generate_news.py --level 2 \
  --topic "nuevo modelo de IA de OpenAI"
python scripts/generate_news.py --level 3 \
  --topic "nuevo modelo de IA de OpenAI" --select 1 --format carousel5
```

Nivel 1 analiza una única URL y genera una pieza mínima; nivel 2 busca hasta
3 fuentes y devuelve opciones; nivel 3 contrasta hasta 6 fuentes y genera un
informe profundo. Ver [`docs/news-generator.md`](docs/news-generator.md).
Toda pieza visual pasa por el rol de visión antes de entregarse, con un
máximo de 3 regeneraciones y detención en la cuarta evaluación fallida.

## Instalación desde cero

Requisitos del sistema:

- Python `>=3.12`;
- `uv` ([astral-sh/uv](https://github.com/astral-sh/uv));
- manim, ffmpeg y ffprobe (paquetes de sistema; ver abajo);
- Chromium de Playwright (solo para captura web).

```bash
# 1. Clonar y entrar
git clone <url-del-repo> redes2 && cd redes2

# 2. Entorno virtual + dependencias
uv sync --group dev
source .venv/bin/activate

# 3. Herramientas externas (según sistema operativo)
#    macOS:
#      brew install ffmpeg
#    Debian/Ubuntu:
#      sudo apt install ffmpeg
#    Componente de Manim: se instala con las dependencias Python (manim).

# 4. Playwright (solo si vas a usar captura web)
python -m playwright install chromium

# 5. Configuración
cp .env.example .env
cp tenants/agente32/.env.example tenants/agente32/.env
#    Editar .env según la máquina: PROMPTGATE_BASE_URL, OPENROUTER_API_KEY,
#    FINAL_OUTPUT_DIR, etc.

# 6. Diagnóstico
python scripts/doctor.py --tenant agente32
```

## Modo headless

En un servidor sin sesión gráfica, el preview de Manim está **desactivado
por defecto**. Renderizar un video:

```bash
python build.py --tenant agente32 --video <video> --no-preview --no-post
```

La generación de textos del post requiere `PROMPTGATE_BASE_URL`
configurado; sin endpoint, usar `--no-post` o el flujo fallará con un
mensaje claro.

## Uso rápido

```bash
# Activar entorno virtual
source .venv/bin/activate

# Listar escenas disponibles
python build.py --list

# Renderizar todos los videos del tenant activo (calidad baja, rápido)
python build.py

# Renderizar video específico
python build.py --video intro

# Renderizar en calidad alta con preview
python build.py --video IntroScene --quality high --preview

# Renderizar y abrir con el reproductor del sistema
python build.py --video intro --open

# Combinar todas las escenas en un solo video
python build.py --combine

# Renderizar y ver el resultado en el navegador (levanta el servidor local)
python build.py --video intro --serve
```

## Servir videos en el navegador

`scripts/serve_videos.py` es un servidor HTTP local (solo stdlib, sin
dependencias) que muestra los videos generados con un player en el
navegador. Escucha en `0.0.0.0`, así que la URL es accesible desde
cualquier dispositivo de la red local (celular, tablet, otra máquina).

```bash
# Levantar el servidor (índice en http://<ip-lan>:8300/)
python scripts/serve_videos.py
python scripts/serve_videos.py --port 9001   # puerto custom
python scripts/serve_videos.py --open        # abrir el navegador

# O directamente al renderizar: levanta el servidor en background y
# muestra la URL de cada video recién generado.
python build.py --video intro --serve
```

- El índice (`/`) lista todos los videos `.mp4`/`.webm` del repo, el más
  reciente primero, con player y link de descarga.
- Cada video tiene su página `/watch?path=<ruta>` y una URL directa de
  archivo `/v/<ruta>` con soporte `Range` (permite adelantar/retroceder).
- Por seguridad el servidor **solo** expone videos y las páginas del
  índice: `.env`, configs y el resto del repo devuelven 404.
- `SERVE_PORT` en el entorno cambia el puerto default (8300).
- `build.py --serve` deja el servidor corriendo en background; el log vive
  en `logs/serve_videos.log`.

## PromptGate local

El cliente `scripts/promptgate_client.py` usa PromptGate como endpoint
OpenAI-compatible, sin autenticación ni API key. La configuración vive en
`.env`:

```env
PROMPTGATE_BASE_URL=https://endpoint.example/v1
PROMPTGATE_AUTH=none
PROMPTGATE_TIMEOUT=120
PROMPTGATE_MODEL=coder-rata
```

Modelos OpenRouter para generación de imágenes:

```env
OPENROUTER_IMAGE_DRAFT_MODELS=meta/muse-image,black-forest-labs/flux.2-klein-4b
OPENROUTER_IMAGE_QUALITY_HIGH_MODEL=google/gemini-3.1-flash-image
OPENROUTER_IMAGE_QUALITY_MEDIUM_MODEL=google/gemini-2.5-flash-image
OPENROUTER_IMAGE_QUALITY_LOW_MODEL=bytedance-seed/seedream-4.5
```

Los modelos de calidad están ordenados por nivel: `HIGH` es el mejor,
`MEDIUM` el intermedio y `LOW` el tercero. Los modelos de `DRAFT` se reservan
para borradores y ejemplos.

Descubrir modelos:

```bash
python scripts/promptgate_client.py --list-models
```

Usar el modelo configurado (o sobrescribirlo explícitamente):


```bash
python scripts/promptgate_client.py \

python scripts/promptgate_client.py \
```

Al renderizar una escena, `build.py` genera por defecto el texto del post
asociado en `media/posts/`, usando `PROMPTGATE_MODEL` (actualmente
`coder-rata`). Para desactivar esta generación:

```bash
python build.py --video lostops --no-post
```

El script lee `.env`, no sobrescribe variables ya exportadas, no envía
`Authorization` y falla si se configura un modo de autenticación distinto de
`none`.

## Publicación de contenido aprobado

`build.py` continúa guardando los renders en `media/`. No copia archivos
automáticamente a la carpeta compartida.

La publicación es una acción explícita, posterior a la validación del usuario,
y el namespace se aísla por tenant:

```bash
# Publicar los MP4 del tenant agente32 agrupados por fecha:
python scripts/publish_final.py --video lostops

# Publicar imágenes aprobadas:
python scripts/publish_final.py \
```

La variable `FINAL_OUTPUT_DIR` de `.env` define la raíz opcional; si no se
indica, el namespace del tenant (`tenant.yaml` → `publish.namespace`)
aisla la salida bajo `<FINAL_OUTPUT_DIR>/<namespace>/`:

```text
$FINAL_OUTPUT_DIR/agente32/
  videos/<YYYY-MM-DD>_<slug>/
  images/<YYYY-MM-DD>_<slug>/
```
`--force` es necesario para reemplazar archivos ya publicados.

## Script `build.py`

El script `build.py` actúa como compilador/builder para los videos. Descubre automáticamente las escenas en `videos/` del tenant activo y las renderiza. El tenant se selecciona con `--tenant` o se toma de `TENANT` / `DEFAULT_TENANT` en `.env`.

### Opciones

| Opción | Descripción |
|--------|-------------|
| `--list`, `-l` | Listar todas las escenas disponibles |
| `--video`, `-v` | Renderizar video específico (nombre parcial) |
| `--tenant` | Tenant activo; default desde TENANT/DEFAULT_TENANT |
| `--quality`, `-q` | Calidad: `low` (480p), `medium` (720p), `high` (1080p), `4k` |
| `--preview`, `-p` | Preview de manim durante el render (default: activado) |
| `--no-preview` | Desactivar preview de manim |
| `--open`, `-o` | Abrir video con reproductor del sistema después de renderizar |
| `--combine`, `-c` | Combinar todas las escenas en un solo video |

> **Diferencia `--preview` vs `--open`**: `--preview` abre la ventana nativa de manim durante el render (útil para debug, activado por defecto). `--open` abre el video terminado con el reproductor del sistema (VLC, QuickTime, etc.).

### Ejemplos

```bash
# Listar escenas
python build.py --list

# Renderizar 'intro' (preview activado por defecto)
python build.py -v intro

# Renderizar sin preview (más rápido)
python build.py -v intro --no-preview

# Renderizar y abrir automáticamente
python build.py -v intro -o

# Renderizar todo en alta calidad
python build.py -q high

# Combinar todas las escenas en un video
python build.py --combine -q high

# Combinar y abrir resultado
python build.py --combine -o
```

### Uso directo de Manim

También puedes usar Manim directamente:

```bash
# Renderizar un video (calidad baja, rápido)
manim -pql videos/2026-08-22_intro/scene.py IntroScene

# Renderizar en calidad alta
manim -pqh videos/2026-08-22_intro/scene.py IntroScene

# Renderizar en 4K
manim -pqk videos/2026-08-22_intro/scene.py IntroScene
```

## Convenciones


## Agregar un nuevo video

1. Crear carpeta: `mkdir videos/2026-08-23_mi_tema/`
2. Crear `scene.py` con la escena
3. Ejecutar: `python build.py --video mi_tema`
## Uso rápido

```bash
# Activar entorno virtual
source .venv/bin/activate

# Listar escenas disponibles
python build.py --list

# Renderizar todos los videos (calidad baja, rápido)
python build.py

# Renderizar video específico
python build.py --video intro

# Renderizar en calidad alta con preview
python build.py --video IntroScene --quality high --preview

# Renderizar y abrir con el reproductor del sistema
python build.py --video intro --open

# Combinar todas las escenas en un solo video
python build.py --combine
```

## PromptGate local

El cliente `scripts/promptgate_client.py` usa PromptGate como endpoint
OpenAI-compatible, sin autenticación ni API key. La configuración vive en
`.env`:

```env
PROMPTGATE_BASE_URL=https://endpoint.example/v1
PROMPTGATE_AUTH=none
PROMPTGATE_TIMEOUT=120
PROMPTGATE_MODEL=coder-rata
```
Modelos OpenRouter para generación de imágenes:

```env
OPENROUTER_IMAGE_DRAFT_MODELS=meta/muse-image,black-forest-labs/flux.2-klein-4b
OPENROUTER_IMAGE_QUALITY_HIGH_MODEL=google/gemini-3.1-flash-image
OPENROUTER_IMAGE_QUALITY_MEDIUM_MODEL=google/gemini-2.5-flash-image
OPENROUTER_IMAGE_QUALITY_LOW_MODEL=bytedance-seed/seedream-4.5
```

Los modelos de calidad están ordenados por nivel: `HIGH` es el mejor,
`MEDIUM` el intermedio y `LOW` el tercero. Los modelos de `DRAFT` se reservan
para borradores y ejemplos.

Descubrir modelos:

```bash
python scripts/promptgate_client.py --list-models
```

Usar el modelo configurado (o sobrescribirlo explícitamente):


```bash
python scripts/promptgate_client.py \
  --prompt "Tu prompt aquí"

python scripts/promptgate_client.py \
  --model <id-devuelto-por-list-models> \
  --prompt "Tu prompt aquí"
```

Al renderizar una escena, `build.py` genera por defecto el texto del post
asociado en `media/posts/`, usando `PROMPTGATE_MODEL` (actualmente
`coder-rata`). Para desactivar esta generación:

```bash
python build.py --video lostops --no-post
```

El script lee `.env`, no sobrescribe variables ya exportadas, no envía
`Authorization` y falla si se configura un modo de autenticación distinto de
`none`.

## Publicación de contenido aprobado

`build.py` continúa guardando los renders en `media/`. No copia archivos
automáticamente a la carpeta compartida.

La publicación es una acción explícita, posterior a la validación del usuario:

```bash
# Publicar los MP4 de media/videos/lostops/ agrupados por fecha:
python scripts/publish_final.py --video lostops

# Publicar imágenes aprobadas:
python scripts/publish_final.py \
  --type images \
  --source media/images/post.png \
  --date 2026-08-23 \
  --slug modelos-semana
```

La variable `FINAL_OUTPUT_DIR` de `.env` define la raíz (obligatoria para
publicar). El script crea los directorios solo al publicar:

```text
$FINAL_OUTPUT_DIR/
  videos/<YYYY-MM-DD>_<slug>/
  images/<YYYY-MM-DD>_<slug>/
```

`--force` es necesario para reemplazar archivos ya publicados.

## Script `build.py`

El script `build.py` actúa como compilador/builder para los videos. Descubre automáticamente las escenas en `videos/` y las renderiza.

### Opciones

| Opción | Descripción |
|--------|-------------|
| `--list`, `-l` | Listar todas las escenas disponibles |
| `--video`, `-v` | Renderizar video específico (nombre parcial) |
| `--quality`, `-q` | Calidad: `low` (480p), `medium` (720p), `high` (1080p), `4k` |
| `--preview`, `-p` | Preview de manim durante el render (default: activado) |
| `--no-preview` | Desactivar preview de manim |
| `--open`, `-o` | Abrir video con reproductor del sistema después de renderizar |
| `--combine`, `-c` | Combinar todas las escenas en un solo video |

> **Diferencia `--preview` vs `--open`**: `--preview` abre la ventana nativa de manim durante el render (útil para debug, activado por defecto). `--open` abre el video terminado con el reproductor del sistema (VLC, QuickTime, etc.).

### Ejemplos

```bash
# Listar escenas
python build.py --list

# Renderizar 'intro' (preview activado por defecto)
python build.py -v intro

# Renderizar sin preview (más rápido)
python build.py -v intro --no-preview

# Renderizar y abrir automáticamente
python build.py -v intro -o

# Renderizar todo en alta calidad
python build.py -q high

# Combinar todas las escenas en un video
python build.py --combine -q high

# Combinar y abrir resultado
python build.py --combine -o
```

### Uso directo de Manim

También puedes usar Manim directamente:

```bash
# Renderizar un video (calidad baja, rápido)
manim -pql videos/2026-08-22_intro/scene.py IntroScene

# Renderizar en calidad alta
manim -pqh videos/2026-08-22_intro/scene.py IntroScene

# Renderizar en 4K
manim -pqk videos/2026-08-22_intro/scene.py IntroScene
```

## Convenciones

- Cada video vive en su carpeta con fecha y tema: `videos/YYYY-MM-DD_tema/`
- Nombre de archivo: `scene.py` (o descriptivo si hay múltiples)
- Las escenas se nombran en PascalCase y heredan de `Scene`
- Output renderizado va a `media/` (gitignored)
- El script `build.py` descubre escenas automáticamente

## Agregar un nuevo video

1. Crear carpeta: `mkdir videos/2026-08-23_mi_tema/`
2. Crear `scene.py` con la escena
3. Ejecutar: `python build.py --video mi_tema`
