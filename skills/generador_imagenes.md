# Skill: Generador de imágenes y videos (Agente E32)

> **Propósito**: skill autocontenido para cualquier agente externo que
> quiera usar los scripts de generación de imágenes/videos del proyecto
> `redes2` sin necesidad de leer el código fuente.
>
> **Carga**: leer junto con `skills/contenido.md` (pipeline de contenido) y
> `skills/global.md` (convenciones del repo) cuando la tarea involucre
> generar piezas visuales. Para video solo, `build.py` + `skills/global.md`.

---

## 1. Setup (obligatorio antes de todo)

```bash
# Desde la raíz del repo (/Users/fabian/code/personal/redes2)
source .venv/bin/activate

# Verificar que todo funciona:
python scripts/generate_images.py --list-tenants
```

Requisitos instalados por el venv:
- Python 3.12
- Pillow, OpenCV, Pydantic, requests, PyYAML (rendering)
- manim Community v0.21.0 + ffmpeg (video; ver `skills/global.md`)
- openrouter (generación de imágenes por IA, opcional)

---

## 2. Estructura del proyecto

```
redes2/
├── scripts/
│   ├── generate_images.py   # Placas y carruseles (Python)
│   ├── generate_videos.py   # Videos via build.py (delega a manim)
│   ├── new_content.py       # Andamiaje de un tema
│   ├── generate_caption.py  # Caption desde brief
│   ├── content_status.py    # Estado de proyectos del tenant
│   ├── fetch_logo.py        # Descargar/logo con origen documentado
│   ├── publish_final.py     # Publicar a carpeta compartida
│   └── promptgate_client.py # Cliente de PromptGate
├── src/noticia_carrusel/    # Motor de render (Python)
│   ├── models.py            # Esquemas Pydantic (AppConfig, SlideConfig…)
│   ├── config.py            # Carga de YAML
│   ├── canvas.py            # CanvasSpec / SafeArea
│   ├── templates.py         # NewsCardRenderer
│   ├── text_engine.py       # Renderizado de texto
│   ├── generator.py         # Pipeline de composición
│   ├── providers.py         # Proveedor de imágenes IA (OpenRouter)
│   ├── tenant.py            # Carga de tenant
│   └── brief.py             # Validación de brief
├── tenants/<tenant_id>/     # Config por marca
│   ├── tenant.yaml          # Manifiesto del tenant
│   ├── configs/images/*.yaml   # Configs de cada pieza
│   ├── content/<slug>/        # Proyecto de contenido
│   ├── assets/logos/…         # Logos del tenant
│   └── output/                # Render salida
├── assets/logos/<marca>/    # Logos compartidos
└── templates/prompts/       # Plantillas de diseño (markdown)
```

**Multi-tenant**: cada tenant vive aislado en `tenants/<id>/`. Nunca mezclar assets ni outputs entre tenants.

---

## 3. Resolver el tenant (primer paso siempre)

Precedencia (de mayor a menor):
1. `--tenant <id>` (flag CLI)
2. `TENANT` env var
3. `DEFAULT_TENANT` en `.env`
4. Único directorio en `tenants/` (si solo hay uno)

```bash
# Listar tenants disponibles:
python scripts/generate_images.py --list-tenants

# Ver manifiesto del tenant elegido:
read tenants/<id>/tenant.yaml
```

Anunciar en una línea antes de generar:
```
Tenant: <id> · <nombre> · <handle>
```

---

## 4. Comandos principales

### 4.1 `generate_images.py` — Placas y carruseles

```bash
python scripts/generate_images.py post --config <archivo>.yaml [opciones]
python scripts/generate_images.py carousel --config <archivo>.yaml [opciones]
```

#### Subcomandos

| Subcomando | Qué genera | Uso |
|---|---|---|
| `post` | Placa individual (1 slide) | Noticias, piezas unitarias |
| `carousel` | Carrusel (N slides) | Colecciones, rankings |

#### Flags

| Flag | Default | Descripción |
|---|---|---|
| `--config` | *(requerido)* | Path relativo dentro de `configs/images/` del tenant |
| `--tenant` | Desde env | Tenant activo |
| `--quality <draft\|low\|medium\|high>` | `draft` | Calidad de la imagen IA. `draft` = modelo barato, `high` = mejor modelo |
| `--reuse-intermediate` | off | Reusar imágenes base ya generadas en `intermediate/` (sin costo IA) |
| `--check-intermediate` | off | Listar imágenes base existentes y salir (sin generar) |

#### Ejemplos

```bash
# Prototipo en borrador (usa modelo barato, sin reusar)
python scripts/generate_images.py post --config noticia_malaponte_vertical.yaml --quality draft

# Prototipo reusando imágenes base ya generadas (sin costo)
python scripts/generate_images.py post --config noticia_malaponte_vertical.yaml --reuse-intermediate

# Ver qué imágenes base hay sin generar nada
python scripts/generate_images.py post --config noticia_malaponte_vertical.yaml --check-intermediate

# Carrusel final en calidad alta, reusando base
python scripts/generate_images.py carousel --config nvidia-hugging-face-carousel.yaml --quality high --reuse-intermediate
```

#### Salida típica

```
/Users/fabian/code/personal/redes2/tenants/<id>/content/<slug>/renders/slide_01.png
/Users/fabian/code/personal/redes2/tenants/<id>/content/<slug>/renders/slide_02.png
…
Reusó 4 imagen(es) base existente(s) (sin costo, sin llamar a la IA)
| 2026-08-28 18:27:27 | meta/muse-image | slide_04 (text) | 0.0100 |
**Total acumulado: $0.0800 USD**
```

### 4.2 `generate_videos.py` — Videos via Manim

```bash
python scripts/generate_videos.py --video <nombre> [opciones_build]
```

Delega directamente en `build.py`. Ver `skills/global.md` → sección "⚡ Render express" para la regla de render sin preguntas:

```bash
# Reel default (1080x1920@30)
source .venv/bin/activate && python build.py --video <nombre> --no-preview

# Post vertical 3:4
python build.py --video <nombre> -f post --no-preview

# Alta calidad 1080p60
python build.py --video <nombre> --no-format -q high --no-preview
```

### 4.3 Otros scripts

| Script | Uso |
|---|---|
| `scripts/new_content.py --slug <tema-kebab> --tema "<descripción>"` | Crea `brief.md`, `caption.md`, `assets/` |
| `scripts/generate_caption.py --slug <fecha>_<tema-kebab> --template post_noticia` | Genera caption desde brief |
| `scripts/content_status.py` | Estado de todos los proyectos del tenant |
| `scripts/fetch_logo.py --slug <marca> --url <url> --license "<lic>"` | Descarga y registra logo |
| `scripts/publish_final.py --type images --source <path> --date <YYYY-MM-DD> --slug <tema>` | Publica a carpeta compartida |

---

## 5. Schema completo del YAML de config

Cada pieza visual se define en `tenants/<id>/configs/images/<nombre>.yaml`.

```yaml
# === Metadatos ===
project_name: "noticia_malaponte_vertical"   # Identificador interno
output_dir: "noticia_malaponte_vertical"     # Carpeta de salida
format: "post_vertical"                      # Formato de lienzo (ver §6)
template: "news_card"                        # Template de render

# === Marca ===
brand:
  name: "AGENTE E32"                         # Nombre de la marca
  logo_path: "logos/agente32/agente32.svg"   # Logo relativo a assets/ del tenant

# === Fuentes (relativas a assets/fonts/) ===
fonts:
  title: "fonts/Montserrat-ExtraBold.ttf"    # Título (obligatorio)
  body: "fonts/Inter-SemiBold.ttf"           # Cuerpo/subtítulo
  code: "fonts/FiraCode-Regular.ttf"         # Code blocks (si hay slides code)

# === Colores (hex) ===
colors:
  text_primary: "#FFFFFF"                    # Texto principal
  text_secondary: "#D9D9D9"                  # Texto secundario
  highlight_bg: "#0057D9"                    # Fondo de badges/highlights
  footer_text: "#FFFFFF"                     # Color del footer
  divider: "#6F86A8"                         # Color de la línea divisoria

# === Generación de imagen de fondo por IA (opcional) ===
image_generation:
  enabled: false                             # true para generar fondo con IA
  model: "google/gemini-3.1-flash-image"     # Modelo IA (se puede usar alias)
  prompt: "Fotografía periodística vertical…" # Prompt positivo
  negative_prompt: "blurry, distorted…"      # Prompt negativo

# === Safe area (fracción del lienzo; opcional, conserva defaults del formato) ===
safe_area:
  top: 0.18          # 0.0–0.45
  bottom: 0.20       # 0.0–0.45
  # left / right también aceptados (default: 0.06 del ancho)

# === Margen extra en píxeles (sumado al safe_area; default 20px cada lado) ===
margin:
  left: 20
  top: 20
  right: 20
  bottom: 20

# === Slides ===
slides:
  - type: "cover"              # cover | text | bullets | code
    title: "APROBARON EL PLIEGO…"
    highlights:                # (cover) badges destacados
      - "MALAPONTE"
      - "SERÁ CAMARISTA"
    subtitle: "Rosario · Información judicial"  # (cover) descripción
    body: "El pliego fue aprobado…"             # (text/bullets/code) cuerpo
    bullets:                                # (bullets) lista de puntos
      - "Nombramiento en la Cámara Federal"
      - "Impacto institucional en Rosario"
    code: |                               # (code) bloque de código
      <code>
      def publicar_noticia(titulo, imagen):
          return renderizar(titulo, imagen)
      </code>
    footer_text: "AGENTE E32"              # Texto del footer por slide
```

### Campos obligatorios
- `project_name`, `output_dir`, `format`, `template`
- `brand.name`, `brand.logo_path`
- `fonts.title` (y `fonts.body`, `fonts.code` si hay slides de código)
- `colors` completo
- `slides` con al menos un slide; cada slide necesita `type` y `title`
- `content` con `title` para el slide cover (o `title` + `body` para text/bullets/code)

---

## 6. Formatos de lienzo disponibles

| `format` | Pixeles | Proporción | Uso |
|---|---|---|---|
| `post_square` | 1080×1080 | 1:1 | Post cuadrado |
| `carousel_square` | 1080×1080 | 1:1 | Carrusel cuadrado |
| `post_vertical` | 1080×1350 | 4:5 | Post vertical clásico |
| `carousel_vertical` | 1080×1350 | 4:5 | Carrusel vertical |
| `story` | 1080×1920 | 9:16 | Story / Reel |

Los defaults de `safe_area` por formato (fracción del lienzo):

| Formato | Izq./Der. | Arriba | Abajo |
|---|---|---|---|
| `post_square` / `carousel_square` | 6% | **18%** | **20%** |
| `post_vertical` / `carousel_vertical` | 6% | 6% | 8% |
| `story` | 6% | 6% | 13% |

> **Nota**: `post_square`/`carousel_square` tienen top/bottom más altos
> (18%/20%) porque el bloque fijo (badges + divisor + footer) necesita esa
> reserva en formato 1:1. **No se aplica a los demás formatos** — la misma
> fracción aplicada a vertical/story recortaría el título.

El `margin` agrega **20px por defecto** en los 4 lados, sumado al `safe_area` (universal para todos los formatos).

---

## 7. Tipos de slide

| `type` | Campos requeridos | Descripción |
|---|---|---|
| `cover` | `title`, `highlights` (opcional), `subtitle` (opcional) | Portada del carrusel con imagen principal, título, badges, divisor |
| `text` | `title`, `body` | Slide de desarrollo / explicación |
| `bullets` | `title`, `bullets` (lista) | Lista de puntos clave |
| `code` | `title`, `code` | Bloque de código con panel oscuro, Fira Code, números de línea |

Todos los slides admiten `footer_text` (sobrescribe el del tenant si lo hay) y el footer con `@fabian128k` + ícono social se dibuja siempre en el borde inferior.

---

## 8. Template de diseño (`templates/prompts/`)

Los templates son archivos markdown que funcionan como guías reutilizables para mantener consistencia visual. Se refieren en el YAML con `template:`.

| Archivo | Define |
|---|---|
| `templates/prompts/theme_carousel_system.md` | Composición visual de carruseles: safe area, margin, degradado, divisor, footer |
| `templates/prompts/theme_default.md` | Defaults generales de composición |
| `templates/prompts/theme_news_cover.md` | Reglas específicas para portada (cover) |
| `templates/prompts/theme_news_text.md` | Reglas para slides de texto |
| `templates/prompts/theme_news_bullets.md` | Reglas para slides de bullets |
| `templates/prompts/theme_carousel_system.md` | Reglas para slides de código |

Los templates **no se ejecutan** — son documentación/autoprompt para que el agente mantenga la coherencia visual. Consultarlos para conocer reglas específicas de cada tipo de slide.

---

## 9. Calidad de imagen IA y costos

Cada llamada a un modelo de imagen (`image_generation.enabled: true`) genera un costo reportado por OpenRouter en la salida del comando y en `resumen.md`.

| `--quality` | Modelo usado | Cuándo usar |
|---|---|---|
| `draft` (default) | `OPENROUTER_IMAGE_DRAFT_MODELS` | Prototipos, iteraciones |
| `low` / `medium` | Modelos intermedios | Revisiones |
| `high` | `OPENROUTER_IMAGE_QUALITY_HIGH_MODEL` | Entrega final |

El costo se registra automáticamente en `resumen.md` (junto al proyecto en `content/<slug>/`, o en `output/<output_dir>/` si no tiene `content_slug`).

**Reportar siempre** el costo real tomado de la salida del comando, nunca estimado:
```
> Este prototipo (4 slides) costó $0.04 USD. Acumulado del proyecto: $0.08 USD.
```
Fondo sólido o imagen provista (sin IA) → no hay costo que reportar.

---

## 10. Reuso de imágenes base (intermediate)

Antes de generar un prototipo, **siempre** chequear si ya hay imágenes base en `intermediate/`:

```bash
python scripts/generate_images.py post --config <archivo>.yaml --check-intermediate
```

Si devuelve imágenes existentes, preguntar al usuario:
- **"Sí, regenerar"** → correr normal (llama a la IA, genera costo nuevo)
- **"No, usá esas"** → correr con `--reuse-intermediate` (sin costo IA)

```bash
python scripts/generate_images.py post --config <archivo>.yaml --reuse-intermediate
```

---

## 11. Verificación visual antes de entregar

Antes de mostrar un PNG al usuario:
1. El texto no se corta ni a mitad de palabra.
2. El contraste es suficiente (texto legible sobre el fondo).
3. El branding está presente (logo, nombre de marca, handle).
4. Las zonas seguras de Instagram se respetan:
   - Top safe: 150px (zona de UI de Instagram)
   - Bottom safe: 150px (zona de UI de Instagram)
5. Formato correcto según el `format` del YAML (1080×1080 / 1080×1350 / 1080×1920).
6. Sin violación de la zona segura: ningún color de highlight/título
   debe pintar en la franja inferior del footer (y=799 a y=1080
   para 1080px de alto).

Verificación rápida de violación de zona segura (pixeles reales):
```bash
python -c "
from PIL import Image
img = Image.open('<path>').convert('RGB')
target = (0, 87, 217)  # highlight_bg
for y in range(799, 1080):
    row = [img.getpixel((x,y)) for x in range(0,1080)]
    m = sum(1 for p in row if abs(p[0]-target[0])<20 and abs(p[1]-target[1])<20 and abs(p[2]-target[2])<20)
    if m > 5: print(f'VIOLACION y={y}: {m}px'); break
else: print('OK')
"
```

---

## 12. Flujo de trabajo típico

### Generar una placa nueva
```bash
# 1. Si es un tema nuevo, crear andamiaje
python scripts/new_content.py --slug noticia-malaponte --tema "Florentino Malaponte será camarista federal"

# 2. Completar el brief a mano (investigación verificable)
# 3. Generar el caption (opcional)
python scripts/generate_caption.py --slug 2026-08-28_noticia-malaponte --template post_noticia

# 4. Escribir el YAML de la placa
#    tenants/<id>/configs/images/noticia_malaponte_vertical.yaml

# 5. Chequear imágenes base existentes
python scripts/generate_images.py post --config noticia_malaponte_vertical.yaml --check-intermediate

# 6. Prototipo en borrador
python scripts/generate_images.py post --config noticia_malaponte_vertical.yaml --quality draft

# 7. Iterar con el usuario

# 8. Final en calidad alta
python scripts/generate_images.py post --config noticia_malaponte_vertical.yaml --quality high
```

### Generar un carrusel
```bash
# 1. Escribir el YAML con N slides (cover + text/bullets/code…)
#    tenants/<id>/configs/images/nvidia-hugging-face-carousel.yaml

# 2. Prototipo reusando imágenes base (sin costo)
python scripts/generate_images.py carousel --config nvidia-hugging-face-carousel.yaml --reuse-intermediate

# 3. Final en calidad alta
python scripts/generate_images.py carousel --config nvidia-hugging-face-carousel.yaml --quality high --reuse-intermediate

# 4. Publicar (solo con aprobación explícita)
python scripts/publish_final.py --type images --source <path> --date 2026-08-28 --slug nvidia-hugging-face
```

---

## 13. Patrones comunes y buenas prácticas

- **Nunca** inventar métricas, fechas, precios, nombres ni capacidades.
- **Siempre** usar el logo SVG del tenant (`brand.logo_path`); nunca dibujar logos a mano ni generarlos por IA.
- **Mantener** un solo color de `highlight_bg` por tenant (ej: `#0057D9` para AGENT E32).
- **Usar** `--quality draft` para iterar; solo `--quality high` para la entrega final.
- **Reusar** imágenes base con `--reuse-intermediate` si el usuario no quiere nuevo costo IA.
- **Reportar** paths absolutos de cada artefacto generado.
- **No generar** piezas que el usuario no pidió.
- **Los tenants viven aislados**: `tenants/<id>/` — nunca mezclar assets ni outputs entre tenants.

---

## 14. Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError` | Venv no activado o `src/` no en path | `source .venv/bin/activate` desde raíz del repo |
| `FileNotFoundError` en fonts | Fuente no copiada a `assets/fonts/` | Copiar desde `assets/fonts/` del repo o documentar en `docs/fonts.md` |
| Logo no aparece | `logo_path` incorrecto o SVG sin curvas | Verificar path relativo a `assets/`; convertir SVG a curvas con Inkscape |
| Texto recortado en portada | `safe_area.bottom` demasiado grande | Bajar `safe_area.bottom` (fracción 0.0–0.45) o agregar `margin.bottom` |
| Texto recortado en vertical | `safe_area.top/bottom` aplicado universalmente | No aplicar los defaults square (18%/20%) a vertical — usar los propios del formato (6%/8%) |
| Imagen IA con costo inesperado | `image_generation.enabled: true` con `--quality high` | Usar `--quality draft` para prototipos, o deshabilitar (`enabled: false`) |
| Zona segura violada (píxeles) | Contenido pinta en franja del footer | Aumentar `margin.bottom` o reducir contenido para que quepa antes del límite |
| `FileNotFoundError` en tenant.yaml | Tenant no existe | `python scripts/generate_images.py --list-tenants` para verificar |
