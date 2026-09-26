# Agent Instructions — Agente E32

Generador multi-tenant de contenido para redes: imágenes, carruseles,
captions y videos con Manim Community v0.21.0.

## 🤖 Modo agente (REGLA DE ARRANQUE — prioridad máxima)

Protocolo completo: `docs/agent-mode.md`. Resumen operativo obligatorio:

### 1. Resolver el tenant antes de la primera acción

Precedencia: `--tenant` > `TENANT` > `DEFAULT_TENANT` en `.env` > único
directorio en `tenants/` > preguntar.

Leer `tenants/<id>/tenant.yaml` y anunciarlo en una línea:

```
Tenant: agente32 · Agente E32 · @fabian128k
```

No pedir confirmación si se resolvió por precedencia. Nunca mezclar
assets ni outputs entre tenants.

### 2. Clasificar la intención

| Pedido | Ruta |
|---|---|
| "hacé una placa de X" | Placa individual |
| "armá un carrusel de X" | Carrusel |
| "story de X" | Story 9:16 |
| "video de X" | Reel / video |
| "escribí algo sobre X" | **Tema o noticia completo** |
| "escribime el copy de X" | Solo caption |
| "generá una imagen de X" | Solo imagen |
| "publicá esto" | Publicación |

**Precedencia con la regla ⚡**: si la escena o pieza **ya existe** y el
usuario pide renderizarla, manda "Render express" (más abajo): cero
preguntas. El modo conversacional aplica solo a contenido nuevo.

### 3. Pipeline de "desarrollar un tema o noticia"

Ante *"escribí algo sobre X"*, en este orden y sin saltear pasos:

1. **Investigar primero, redactar después.** Buscar en internet, mínimo
   3 fuentes, priorizando primarias sobre medios. Registrar fecha de
   cada una.
2. **Devolver el brief al usuario** antes de escribir copy: qué está
   confirmado, qué no, contradicciones entre fuentes y qué no se
   encontró. Esperar validación.
3. **Prototipo de texto** con el template de `templates/posts/` que
   corresponda al tipo de contenido.
4. **Preguntar formato y piezas**, todo junto, con default recomendado.
5. **Resolver assets**: logos por prioridad tenant → compartido; si
   falta, descargar del press kit oficial y documentar el origen.
   **Para prototipos de noticias, usar siempre logos verdaderos** de las
   marcas/entidades mencionadas (OpenAI, Hugging Face, etc.): nunca
   placeholders, monogramas tipográficos ni logos generados por IA. Si el
   logo no existe en `assets/logos/`, descargarlo del press kit oficial
   **antes** de generar el prototipo visual.
6. **Prototipo visual**: antes de generar, chequear si ya hay imágenes
   base en `intermediate/` y preguntar al usuario si regenerar o
   verlas primero (ver §8). Reportar paths absolutos y, si usó IA, el
   costo (ver §7).
   **Chequeo de visión**: toda imagen capturada vía `web_capture` (screenshot)
   pasa por el rol de visión que analiza si hay publicidad, banners, popups u
   otros artefactos. Si no pasa la validación, se regenera automáticamente;
   el loop permite **hasta 3 reintentos** y a la 4ta evaluación —si sigue sin
   pasar— se detiene y se informa al usuario que la imagen no pasó el review
   tras 3 intentos.
7. **Iterar** con el usuario las veces que haga falta.
8. **Final** en calidad alta. Reportar el costo de esta corrida y el
   acumulado del proyecto (ver §7).
9. **Publicar solo con aprobación explícita.**
### 3b. Niveles de trabajo del generador de noticias

El script `scripts/generate_news.py` tiene tres niveles explícitos. No
confundirlos: cada nivel tiene un costo, una profundidad de investigación
y una salida distinta.

| Nivel | Entrada | Investigación | Salida |
|---|---|---|---|
| `1` — Fuente única | `--url <URL>` | Lee y analiza solo esa página | `brief.md`, informe corto, screenshot validado, una pieza mínima y `post.txt` |
| `2` — Búsqueda | `--topic "<tema>"` | Busca noticias relacionadas, lee hasta 3 fuentes y separa confirmados/no confirmados | informe con opciones de ángulo; después de elegir, piezas + `post.txt` |
| `3` — Investigación profunda | `--topic "<tema>"` | Busca hasta 8 resultados, contrasta hasta 6 fuentes, arma cronología, contradicciones y datos faltantes | informe profundo con opciones; después de elegir, piezas, assets y `post.txt` |

Uso:

```bash
# Nivel 1: URL directa, análisis mínimo y pieza breve
python scripts/generate_news.py --level 1 \
  --url "https://ejemplo.com/noticia" --format short

# Nivel 2: devuelve informe y opciones; --select genera la opción elegida
python scripts/generate_news.py --level 2 \
  --topic "nuevo modelo de IA de OpenAI"
python scripts/generate_news.py --level 2 \
  --topic "nuevo modelo de IA de OpenAI" --select 1 --format carousel3

# Nivel 3: investigación ampliada, contradicciones y cronología
python scripts/generate_news.py --level 3 \
  --topic "nuevo modelo de IA de OpenAI" --select 2 --format carousel5
```

Si faltan `--select`, `--format` o `--visual` y el proceso tiene terminal
interactiva, el script pregunta en lote qué ángulo, formato y tipo de fondo
usar (`screenshot` o `solid`). Sin terminal interactiva, imprime las opciones
y termina sin generar piezas: el agente debe devolver el informe al usuario y
esperar su elección.

### 3c. Gate visual obligatorio antes de entregar

El rol de visión debe ejecutarse en **cada etapa visual previa a la
entrega**:

1. screenshot crudo capturado por `web_capture`;
2. cada PNG final de post/story/carrusel después de componer texto,
   logos y fondo;
3. frames representativos de un video web, si el nivel genera video.

Debe validar publicidad, popups, cookies, paywalls, 404/captcha,
artefactos de carga, texto cortado, contraste, zonas seguras, logos
verdaderos y texto que tape ojos, boca, caras, pantallas, gráficos,
código, logos u objetos focales. Texto sobre torso o fondo oscuro sin
ocultar el objeto focal no es un error.

Si el resultado no pasa:

- regenerar o corregir la composición;
- permitir como máximo **3 reintentos**;
- la 4.ª evaluación es el último review: si falla, detenerse, conservar
  el diagnóstico y reportar al usuario que no pasó después de 3 intentos;
- nunca entregar ni publicar silenciosamente una imagen fallida;
- la visión sobre texto/reportes no reemplaza la revisión editorial de
  hechos: son gates separados.

El estado del gate debe quedar en `vision_review.json` junto al proyecto,
con `attempts`, `clean`, `issues`, `confidence` y `status`
(`passed`/`stopped_after_3_retries`). No publicar sin aprobación explícita.


### 4. Reglas de interacción

- Preguntar en lote, máximo 4 preguntas por turno, numeradas.
- Siempre proponer un default: el usuario debe poder responder "dale".
- Nunca preguntar lo que se resuelve leyendo archivos (tenant, marca,
  handle, formatos, assets disponibles).
- Reportar paths absolutos de cada artefacto generado.
- No generar piezas que el usuario no pidió.

### 5. Veracidad

- Nunca inventar métricas, fechas, precios, nombres ni capacidades.
- Marcar `[SIN CONFIRMAR]` lo que no tenga fuente y avisarlo.
- Separar dato, inferencia y opinión de forma explícita.
- Dato faltante: `N/D`. Jamás un valor estimado.
- Benchmarks del fabricante se citan como "según <empresa>".

### 6. Templates

| Capa | Carpeta | Define |
|---|---|---|
| Texto | `templates/posts/` | Estructura del caption, campos, límites |
| Diseño | `templates/prompts/` | Composición visual, portadas, slides |

Elegir el de texto según el tipo: `post_noticia`, `post_analisis`,
`post_lista_top`, `post_tutorial`, `post_lanzamiento`,
`carousel_noticia`, `story_teaser`.

### 7. Costos de generación de imágenes por IA

Cada llamada a un modelo de imagen (`image_generation.enabled: true`)
devuelve `usage.cost` en la respuesta de OpenRouter. Se registra
automáticamente, sin intervención del agente, en `resumen.md`: junto
al proyecto de contenido si la config tiene `content_slug`
(`content/<slug>/resumen.md`), o junto al output si no
(`output/<output_dir>/resumen.md`). El costo nunca se inventa: si el
proveedor no lo informa, no se registra nada.

Implementado en `src/noticia_carrusel/cost_summary.py` +
`generator.py::generate()`. `scripts/generate_images.py` imprime al
terminar el costo de esa corrida y el acumulado del proyecto.

**Obligación del agente**: después de generar cualquier pieza con
imagen por IA (placa, carrusel, story — prototipo o final), reportar
al usuario el costo real tomándolo de la salida del comando, nunca
estimado:

> Este prototipo (4 slides) costó \$0.04 USD. Acumulado del proyecto:
> \$0.08 USD.

Si la generación usó fondo sólido o una imagen provista (sin IA), no
hay costo que reportar — decirlo si el usuario pregunta.

### 8. Reuso de imágenes intermedias antes de generar

**Siempre chequear antes de generar un borrador o prototipo** si ya
hay imágenes base en `intermediate/` para esa config:

```bash
python scripts/generate_images.py post --config <archivo>.yaml --check-intermediate
```

Si el comando devuelve imágenes existentes, **preguntar al usuario**,
nunca decidir solo:

> Ya hay 4 imágenes base generadas para este prototipo en
> `intermediate/`. ¿Querés volver a generarlas, o verlas antes de
> decidir?

Si el usuario quiere verlas primero, mostrarlas (`read` sobre cada
path) antes de preguntar de nuevo. El usuario decide:

- **"Sí, regenerar"** → correr normal, sin flags extra. Llama a la IA
  de nuevo, genera costo nuevo (§7).
- **"No, usá esas" / "no, quiero que vuelvas a generar el post con
  esas"** → correr con `--reuse-intermediate`: reusa las imágenes
  existentes como fondo y vuelve a componer el texto/theme sobre
  ellas, sin llamar a la IA ni sumar costo.

```bash
python scripts/generate_images.py post --config <archivo>.yaml --reuse-intermediate
```

Implementado en `generator.py::intermediate_images()` (chequeo, sin
costo ni llamadas) y `_base_image(..., reuse_intermediate=True)`
(reuso real, salta la API si el archivo ya existe).

## Setup

```bash
# Crear el venv desde cero (requiere `uv` y Python 3.12):
uv sync --group dev
source .venv/bin/activate

# Herramientas externas del sistema (según SO):
#   macOS:  brew install ffmpeg
#   Debian: sudo apt install ffmpeg

# Playwright (solo captura web):
python -m playwright install chromium

# Configuración inicial (sin secretos reales, editarlos después):
cp .env.example .env
cp tenants/agente32/.env.example tenants/agente32/.env

# Verificación:
python scripts/doctor.py --tenant agente32
```

## Estructura del proyecto

```text
generators/videos/top/       # Generador global reutilizable (top/lostops) — código común
  generator.yaml             # descriptor: id, aliases, entrypoint, config_subdir
  scene.py                   # entrypoint Manim mínimo (delega a BaseTopScene)
src/noticia_carrusel/video_generators/top/  # Lógica común: modelos, loader, composer, style
assets/                      # Recursos compartidos (solo lectura)
  backgrounds/               # Fondos reutilizables para posts y videos (pool combinado)
  fonts/
  logos/<nombre>/            # Un logo por carpeta: fuente SVG + versión paths + README
  sounds/<categoría>/        # Música y SFX para los videos (ej. intros/)
tenants/<id>/                # Todo lo propio de la marca/tenant
  tenant.yaml
  assets/                    # Exclusivos o que pisan a global (misma key lógica)
    backgrounds/
    logos/
    sounds/
  configs/videos/top/        # JSONs genéricos del top (title, subtitle, items, audio)
  videos/                    # Solo escenas únicas del tenant (intro, logos). Los generadores comunes NO van aquí
  overrides/videos/top/      # Opcional: TopScene que hereda de BaseTopScene y reemplaza style/renderer
  media/videos/top/<slug>/   # Output renderizado tenant-aislado
utils/                       # Utilidades compartidas (themes, helpers)
docs/
build.py
skills/
templates/
```
> Regla: los generadores reutilizables viven fuera de `tenants/`. El tenant aporta configs, assets, outputs y opcionalmente un override pequeño; nunca una copia del generador global. Ver `docs/shared-top-generator-refactor-plan.md` y `docs/multi-tenant-folder-design.md`.
## Convenciones

- **Fuentes**: la especificación completa vive en `docs/fonts.md`. Resumen:
  `Fira Code` para código (default automático en todo `Text`/`MarkupText` vía
  `utils.theme`), **Space Grotesk** para títulos principales, **Inter** para
  textos/subtítulos/UI, **Manrope** como alternativa títulos + cuerpo. Los
  logos SVG van como curvas y no se ven afectados; nunca tocar las fuentes de
  los logos.
- **Archivos**: `scene.py` o nombre descriptivo si hay múltiples
- **Clases**: PascalCase, heredan de `Scene` o subclases (e.g., `MovingCameraScene`)
- **Imports**: `from manim import *` (convención estándar de Manim)
- **Assets**: logos en `assets/logos/<nombre>/` con README que documente cómo
  regenerar la versión paths (ver `assets/logos/agente32/README.md`).
  Los backgrounds reutilizables viven en `assets/backgrounds/` (global) y
  `tenants/<id>/assets/backgrounds/` (tenant). El catálogo se fusiona con
  prioridad tenant por key lógica (`TenantContext.iter_assets` + `available_backgrounds`);
  un fondo explícito (`background_image_path`) siempre gana al pool. Usar
  `background_mode: "solid"` solo cuando se solicite explícitamente conservar
  el fondo procedural.
- **Manim** no soporta `<text>` en SVG: convertir a curvas con Inkscape
  (`--export-text-to-path`) y forzar `stroke:none` (strokes residuales gigantes)
- **Análisis de JSON de tops**: cuando el usuario pida analizar uno o más JSON,
  leer siempre los archivos reales antes de opinar. Revisar estructura, tipos,
  campos obligatorios, valores faltantes o inválidos, orden del ranking,
  referencias a logos/assets y URLs SVG. El esquema actual es genérico:
  `title`/`subtitle`/`audio`/`background_image_path`/`final_hold_seconds`/`items[]`
  (`name`/`visual_asset`/`secondary_text`/`metric`/`comment`/`specs[]`/`highlighted`);
  el esquema viejo (`titulo`/`modelos`/`provider`/`metrica`) vive solo en
  `tenants/<id>/videos/lostops/json` migrado a `configs/videos/top`. Revisar
  también todos los textos visibles y proponer redacción más clara sin inventar
  métricas, nombres, precios ni otros hechos.
- **Temas**: usar `ThemedScene` de `utils/theme.py`; paletas definidas ahí mismo.
  El generador global resuelve el theme por `brand.default_theme` del manifest
  y el footer por `brand.footer_logos` (usa `TenantContext.resolve_asset`);
  no hardcodear `agente32`/`fabian128k` en código común.
- **Audio**: música en `assets/sounds/<categoría>/` o `tenants/<id>/assets/sounds/`.
  El generador top resuelve el asset vía `TenantContext.resolve_asset` y el
  builder inyecta `VIDEO_CONFIG`/`RENDER_SEED`; nunca usar
  `Path(__file__).parents[2] / "assets"` dentro de generadores comunes.
- **Skills y protocolo (carga obligatoria)**: al iniciar CUALQUIER tarea de
  este repo, leer siempre `skills/global.md` antes de escribir código. Si la
  tarea es de contenido para redes (placa, carrusel, story, caption, o
  "escribí algo sobre X"), leer además `skills/contenido.md`,
  `skills/generador_imagenes.md`, `docs/agent-mode.md` y el
  template correspondiente de `templates/posts/`.
  Si la tarea corresponde a un tipo de video con skill específica
  (`skills/los_mas_usados.md`, etc.), leerla también. No esperar a que el
  usuario lo pida: las skills se levantan solas. Las skills son
  instrucciones autocontenidas: parámetros a pedir, estructura, assets y
  checklist.

## Formatos de salida (Instagram)

Referencia completa y zonas seguras: `docs/instagram-formats.md`.

| Formato | Medida (px) | Proporción |
|---|---|---|
| Post vertical (priorizado) | 1080 x 1440 | 3:4 |
| Post vertical clásico | 1080 x 1350 | 4:5 |
| Post cuadrado | 1080 x 1080 | 1:1 |
| Post horizontal | 1080 x 608 | 1.91:1 |
| Historia (Story) | 1080 x 1920 | 9:16 |
| Reel | 1080 x 1920 | 9:16 |
| Portada del Reel (feed) | 1080 x 1440 | 3:4 |
| Foto de perfil | 320 x 320 | 1:1 |

Renderizar con resolución custom:

```bash
# Reel / Story
manim -qh -r 1080,1920,30 videos/<carpeta>/scene.py MiEscena
# Post vertical priorizado
manim -qh -r 1080,1440,30 videos/<carpeta>/scene.py MiEscena
```

- `frame_width` es constante (~14.22u); con la resolución cambia `frame_height`.
  Composición centrada funciona en todos los formatos; evitar contenido cerca
  de bordes superior/inferior para Reels/Stories (UI de Instagram superpuesta).

## ⚡ Render express (REGLA PARA AGENTES — prioridad máxima)

Cuando el usuario pide "genera/arma/renderiza el video X" y la escena ya existe:

> **Alcance**: esta regla aplica a piezas que **ya existen**. Para contenido
> nuevo ("escribí algo sobre X", "hacé una placa de Y") manda el pipeline
> conversacional del "Modo agente" al inicio de este documento.

1. **CERO preguntas, CERO análisis previo.** No preguntar formato, calidad,
   duración ni nada. No leer la escena completa. Ejecutar directo:

   ```bash
   source .venv/bin/activate && python build.py --video <nombre-lo-que-sea> --no-preview
   ```

2. **Default automático**: Reel 1080x1920@30 (`-f reel` es el default implícito).
   Solo usar otra cosa si el usuario lo pidió explícitamente en ESTE mensaje
   (`-f post` para 3:4; `--no-format -q high` para 1080p60 estándar).
3. `<nombre-lo-que-sea>`: pasar lo que dijo el usuario tal cual ("lomas",
   "los mas usados", "intro"...). `build.py` matchea fuzzy (subsecuencia
   case-insensitive sin acentos contra carpeta y clase; desempata por fecha
   de carpeta más reciente). Si no matchea, recién ahí correr `--list`.
4. **Reportar solo**: path del mp4 final + verificación ffprobe (resolución/fps)
   + un comando alternativo si quiere otro formato. Nada más.
5. Preguntar SOLO si falta algo que bloquea el render real: la escena no existe
   o el script falla con error de código. Si el usuario pidió datos/métricas que
   la escena aún no tiene, renderizar igual y avisarlo en el reporte.

Esta regla aplica también a skills (`skills/global.md`, `skills/los_mas_usados.md`):
si este documento y una skill discrepan, manda ESTE documento.

## Generación de textos con IA

- Cualquier texto nuevo que haya que generar para el proyecto debe producirse
  usando el modelo `coder-rata` a través de PromptGate.
- Esto incluye textos dentro de videos, títulos, subtítulos, descripciones,
  comentarios, captions, resúmenes, noticias y textos generados por scripts.
## Publicación final tras aprobación explícita

- `build.py` y los generadores deben guardar primero los resultados en `media/`.
- Nunca copiar automáticamente videos o imágenes a la carpeta compartida.
- Solo después de que el usuario dé una aprobación explícita (`OK`,
  `aprobado`, `publicar` o equivalente), copiar el archivo validado a
  `$FINAL_OUTPUT_DIR/<namespace>`, usando `scripts/publish_final.py`.
- `FINAL_OUTPUT_DIR` se configura en `.env` (ruta absoluta de la máquina);
  `publish_final.py` falla con un mensaje claro si falta.
- Agrupar siempre por tipo y fecha:
  `$FINAL_OUTPUT_DIR/<namespace>/videos/<YYYY-MM-DD>_<slug>/` o
  `$FINAL_OUTPUT_DIR/<namespace>/images/<YYYY-MM-DD>_<slug>/`.
- No interpretar una revisión, un comentario positivo o el fin del render como
  aprobación para publicar.



## Generador de imágenes y carruseles

Para generar imágenes y carruseles desde YAML/JSON, usar el CLI
dedicado. Los configs viven dentro del tenant activo
(`tenants/<tenant_id>/configs/images/`):

```bash
# Sin especificar tenant (toma TENANT / DEFAULT_TENANT de .env):
python scripts/generate_images.py post --config post_vertical.yaml
python scripts/generate_images.py carousel --config carousel_vertical.yaml

# Con tenant explícito:
python scripts/generate_images.py --tenant agente32 post --config post_vertical.yaml

Para renderizar videos, usar el CLI dedicado de videos:

```bash
python scripts/generate_videos.py --video lostops --no-preview
python scripts/generate_videos.py --tenant agente32 --video lostops --no-preview
```

- Las configuraciones viven dentro de `tenants/<tenant_id>/configs/` o
  en un archivo propio `.yaml`, `.yml` o `.json`.
- `generate-post` produce una imagen individual; `generate-carousel`
  produce `slide_01.png`, `slide_02.png`, etc.
- Los resultados se guardan en el `output_dir` declarado por cada
  configuración dentro del tenant.
- La IA de OpenRouter genera únicamente la imagen base; Pillow
  compone el texto y el diseño final.
- Para usar IA, `image_generation.enabled` debe ser `true` y el
  modelo debe ser un ID válido o un alias configurado en `.env`
  (`draft`, `high`, `medium`, `low`). Los modelos `draft` se usan
  para borradores; `high`, `medium` y `low` usan los modelos de
  calidad configurados en `.env`.
- Los carruseles también soportan `type: "code"`. El contenido debe
  ir en el campo `code` envuelto en `<code>...</code>`; el renderer
  elimina los tags y lo presenta con
  `assets/fonts/FiraCode-Regular.ttf`, numeración de líneas y panel
  monoespaciado. No usar la IA para escribir el código del slide.
- Antes de publicar, revisar visualmente cada imagen y corregir los
  textos; no copiar nada a `$FINAL_OUTPUT_DIR` sin aprobación explícita.


## Multi-tenancy

El proyecto soporta múltiples marcas/tenants mediante carpetas. Cada
tenant vive en `tenants/<tenant_id>/` con su propio manifiesto,
configuraciones, assets, videos, media y output.

```text
tenants/agente32/
  configs/images/      # YAML de placas y carruseles
  assets/              # Logos, fuentes propias del tenant
  videos/              # Escenas Manim del tenant
  media/               # Output renderizado
  output/              # Imágenes generadas
  .env                 # Claves específicas del tenant (gitignored)
  tenant.yaml          # Manifest con id, namespace, brand, social
```

Resolución de recursos: primero se busca en el tenant y luego en
los compartidos (`assets/`, `templates/`, `src/`). El `tenant.yaml`
define el `namespace` usado para aislar la publicación final.

### Selección de tenant

El tenant se resuelve por este orden de precedencia:

1. `--tenant` en la línea de comandos.
2. Variable de entorno `TENANT`.
3. `DEFAULT_TENANT` en `.env`.
4. Fallback al tenant más reciente si existe solo uno.

```bash
python scripts/generate_images.py --tenant agente32 post --config post_vertical.yaml
python build.py --tenant agente32 --video lostops
python scripts/publish_final.py --tenant agente32 --video lostops
```

## Script build.py
Compilador/builder para renderizar videos. Descubre escenas
automáticamente. El tenant se selecciona con `--tenant` o se toma
de `TENANT` / `DEFAULT_TENANT` en `.env`.

### Comandos principales

```bash
python build.py --video lomas --no-preview  # ⚡ EXPRESS: fuzzy + Reel default
python build.py --list                    # Listar escenas disponibles
python build.py                          # Renderizar todas (preview activado)
python build.py --video lomas -f post    # Post vertical 1080x1440@30
python build.py --video lomas --no-format -q high  # 1080p60 estándar
python build.py --video intro -o         # Abrir con reproductor del sistema
python build.py --combine                # Combinar todas en un video
python build.py --combine -q high        # Combinar en alta calidad
python build.py --combine -o             # Combinar y abrir resultado
```

> **Matching**: `--video` acepta nombre parcial/fuzzy, case-insensitive, sin
> acentos ("lomas", "los mas", "semana" → `ModelosSemana`). Desempata por
> carpeta más reciente.

> **Formatos (`-f`)**: `reel` = 9:16 (Reel/Story), `post` = 3:4 (post vertical).
> Al renderizar UN video, si no se pasa `-f` se usa `reel` automáticamente;
> `--no-format` vuelve a las calidades `-q` estándar. La salida con formato va a
> `media/videos/<módulo>/<H>p<fps>/`. Instagram es el destino por defecto del repo.

> **`--preview` vs `--open`**: `--preview` es la ventana nativa de manim durante el render (activado por defecto). `--open` abre el video terminado con el reproductor del sistema. Usar `--no-preview` para desactivar el preview.

### Calidades

| Flag | Resolución | Uso |
|------|-----------|-----|
| `-q low` | 480p15 | Desarrollo, previews rápidos |
| `-q medium` | 720p30 | Revisión intermedia |
| `-q high` | 1080p60 | Producción |
| `-q 4k` | 2160p60 | Producción máxima |

### Uso directo de Manim

```bash
manim -ql videos/2026-08-22_intro/scene.py IntroScene   # baja
manim -qh videos/2026-08-22_intro/scene.py IntroScene   # alta
manim -qk videos/2026-08-22_intro/scene.py IntroScene   # 4K

# Resolución custom (Reel/Story 9:16) — manim v0.21: -r es "W,H", fps va aparte
PYTHONPATH=. manim -qh -r 1080,1920 --fps 30 videos/<carpeta>/scene.py MiEscena
# Post vertical 3:4
PYTHONPATH=. manim -qh -r 1080,1440 --fps 30 videos/<carpeta>/scene.py MiEscena
```
Notas:
- En v0.21 `-r W,H,FPS` es inválido ("Resolution option is invalid"); el FPS se pasa con `--fps`.
- `PYTHONPATH=.` (o ejecutar desde la raíz del repo) para que `utils.theme` importe bien al llamar manim directo; `build.py` no lo necesita.

## Crear un nuevo video

1. Crear carpeta: `mkdir videos/YYYY-MM-DD_tema/`
2. Crear `scene.py` con la clase Scene
3. Verificar: `python build.py --list`
4. Renderizar: `python build.py --video tema`

## Template de escena

```python
from manim import *


class MiEscena(Scene):
    """Descripción de la animación."""

    def construct(self):
        # Objetos
        texto = Text("Hola Mundo", font_size=48)
        circulo = Circle(radius=1, color=BLUE)

        # Animaciones
        self.play(Write(texto))
        self.play(Create(circulo))
        self.wait(2)
```

## Notas para agentes

- Siempre activar `.venv` antes de ejecutar manim o build.py
- El script `build.py` acepta nombres parciales (case-insensitive)
- `--combine` requiere ffmpeg instalado en el sistema
- `--open` abre el video con el reproductor predeterminado (macOS: `open`, Linux: `xdg-open`, Windows: `start`)
- `--preview` es el preview nativo de manim (se abre durante el render)
- Los archivos en `media/` son output generado, no editar
- Para agregar utilidades compartidas, usar `utils/`
- Las escenas se descubren por herencia de `Scene`, no por nombre de archivo
