# Captura web + motor de cámara (`web_capture`)

Módulo para capturar URLs con Playwright y animar zoom/pan sobre esas
capturas con OpenCV, codificando el resultado con `ffmpeg`. Desacoplado de
Manim (ver justificación en `docs/web-capture-plan.md` §2.2). Diseño y plan
completo: [`docs/web-capture-plan.md`](web-capture-plan.md).

```text
URL -> Playwright -> screenshot HiDPI -> Vision QA (LLM) -> Camera Engine -> OpenCV
    -> frames -> FFmpeg -> recurso de post / clip de video
```

Cada screenshot pasa por un **chequeo automático de visión** antes de
usarse: un modelo de visión analiza la imagen y marca `clean=false` si
detecta publicidad, banners, popups, cookie banners, paywalls, 404 o
artefactos (ver [Validación visual](#validación-visual-con-rol-de-visión) abajo).

## Instalación

```bash
uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt
python -m playwright install chromium
```

`requirements-dev.txt` agrega `pytest` (no se instala en producción).

Para el chequeo de visión (opcional pero recomendado):

```bash
# PromptGate si expone visión, si no OpenRouter
PROMPTGATE_VISION_MODEL=vision  # o el alias que exponga tu PromptGate
# o
OPENROUTER_VISION_MODEL=google/gemini-2.5-flash
```

Sin estas variables, el chequeo hace fail-open (loguea y deja pasar la
imagen) — nunca bloquea por falta de configuración.

## API (`src/noticia_carrusel/web_capture/api.py`)

```python
from noticia_carrusel.web_capture.api import capture_url, get_element_bounds, render_web_clip

# 1) Screenshot simple (viewport)
path = capture_url(url="https://example.com", width=1920, height=1080, scale=2)

# 2) Página completa
path = capture_url(url="https://example.com", full_page=True)

# 3) Elemento específico
path = capture_url(url="https://example.com", selector="#grafico")

# 4) Bounding box de un elemento (para calcular zoom manualmente)
bounds = get_element_bounds(url="https://example.com", selector="#grafico")
# {"x": 850.0, "y": 300.0, "width": 600.0, "height": 400.0}
```

## Motor de cámara

```python
from noticia_carrusel.web_capture.models import CaptureConfig, WebSceneConfig, CameraTimeline, CameraKeyframe
from noticia_carrusel.web_capture.api import render_web_clip

# 5) Zoom automático a un selector (vista completa -> elemento encuadrado)
scene = WebSceneConfig(
    capture=CaptureConfig(url="https://example.com", viewport=(1080, 1920), scale=2),
    duration=3.0,
    zoom_to="#grafico",
    padding=0.15,
)
render_web_clip(scene, output_path=Path("clip.mp4"))

# 6) Pan + zoom manual (keyframes explícitos)
scene = WebSceneConfig(
    capture=CaptureConfig(url="https://example.com", viewport=(1080, 1920)),
    duration=4.0,
    camera=CameraTimeline(keyframes=[
        CameraKeyframe(time=0.0, x=0.5, y=0.5, zoom=1.0, easing="linear"),
        CameraKeyframe(time=4.0, x=0.3, y=0.35, zoom=1.8, easing="ease_in_out"),
    ]),
)
render_web_clip(scene, output_path=Path("clip.mp4"))
```

Easing disponible: `linear`, `ease_in`, `ease_out`, `ease_in_out`
(`web_capture/easing.py`, curvas propias, no reutiliza `manim.rate_functions`
a propósito — ver plan §2.2).

## 7. Integración dentro de un post o un video

### Posts / carruseles (Pillow, `src/noticia_carrusel/`)

Un slide puede usar un screenshot como fondo con `web_capture` (mutuamente
excluyente con `background_image_path`/`image_generation`):

```yaml
# tenants/<id>/configs/images/*.yaml
slides:
  - type: "cover"
    title: "..."
    web_capture:
      url: "https://docs.python.org/3.12/"
      viewport: [1080, 1350]
      scale: 2
```

Ejemplo completo y reproducible: `tenants/agente32/configs/images/post_web_capture.yaml`
(`python scripts/generate_images.py post --config post_web_capture.yaml`).
Se cachea en `tenants/<id>/cache/web_capture/` (no en `output_dir/intermediate/`,
que es el caché por-config de imágenes generadas por IA); `--reuse-intermediate`
reusa el screenshot sin volver a navegar. Sin cámara: un post es un frame único.

### Video (`build.py`, engine `web`)

Una carpeta de video puede tener `web.yaml` en vez de `scene.py` — sin
Manim. `build.py` la descubre y renderiza igual que una escena Manim:

```yaml
# videos/<slug>/web.yaml
capture:
  url: "https://example.com"
duration: 5
zoom_to: "#grafico"
```

```bash
python build.py --tenant agente32 --video <slug> --no-preview
```

El viewport/fps de captura siguen al formato/calidad pedidos por el
comando (`-f reel`, `-q high`, etc.) — igual que una escena Manim recibe
`-r`/`--fps` — lo que declara `web.yaml` es solo el default para invocar el
módulo directamente, fuera de `build.py`. La salida usa el mismo layout
(`media/videos/<slug>/<hh>p<fps>/`) que las escenas Manim, así que
`--combine`, `--open` y `output_path_for()` funcionan sin cambios.

Ejemplo completo: `tenants/agente32/videos/2026-08-31_demo-zoom-web/` (ver su
propio `README.md`).

## Caché

`capture_url(..., tenant=tenant)` cachea por `(url, viewport, scale,
selector, full_page, wait_for, delay)` en `tenant.cache_dir /
"web_capture"` (sha256 de esos campos, 16 hex + sidecar `.json` con
metadata). `force_capture=True` ignora un hit existente. Sin `tenant`
(ej. CLI standalone), cae a un directorio temporal del sistema — no es una
caché real, solo asegura que la función devuelva un `Path` persistido.

## Validación visual con rol de visión

Todo screenshot pasa por un chequeo automático antes de usarse como fondo.
El chequeo se puede desactivar por config (`vision_check: false`).

```yaml
web_capture:
  url: "https://example.com"
  vision_check: true   # default: true
  strict_vision: false # default: false → reintento blando; true → rechaza
```

- **Qué detecta**: publicidad/banners (`"SALE"`, `"Subscribe"`, `"GET 3
  MONTHS"`), popups/overlays, cookie banners (`"Accept all"`), paywalls,
  errores 404/500, captchas, páginas en blanco o a medio renderizar, y
  **texto que tapa caras u objetos importantes** (rostros/ojos/boca,
  pantallas, gráficos, logos o producto principal irreconocible por el
  degradado/texto — ej: título sobre los ojos de Altman/Brockman).
  expone visión, si no `OPENROUTER_VISION_MODEL`, default
  `google/gemini-2.5-flash`). El prompt pide **solo JSON**:
  `{"clean": bool, "issues": [...], "confidence": 0.0-1.0}` validado por
  Pydantic (`VisionCheckResult`).
- **Qué pasa si está sucio (`clean==false`)**:
  - `strict_vision: true` → lanza `ScreenshotRejectedError` con los
    `issues` (útil para pipelines donde un ad no es aceptable).
  - `strict_vision: false` (default) → reintenta **hasta 3 veces** con
    mitigación Playwright (clic en `text=Accept|Got it|Close|Aceptar` si
    existe, ocultar `[id*="ad" i]`), vuelve a chequear cada vez; si a la
    **4ta evaluación** sigue sucio, se detiene el loop, se loguea `error`
    con los `issues` y se devuelve la última imagen igual (fail-open) con
    el resultado adjunto para informar al usuario que no pasó validación
    tras 3 reintentos.
  - El resultado se guarda en el sidecar JSON (`"vision": {...}`) para
    no pagar el LLM dos veces sobre la misma captura.
- **Fallback**: si el proveedor de visión falla o no está configurado,
  se loguea y se deja pasar la imagen (no se inventa un `clean=true`).

Ejemplo real: el screenshot de TIME usado en la placa de OpenAI
(`tenants/agente32/content/.../renders/slide_01.png`) contenía el banner
superior "GET 3 MONTHS PRINT & DIGITAL. SAVE 50%" — con este chequeo,
`issues` habría incluido `"publicidad: banner de suscripción"` y el modo
blando habría intentado ocultarlo antes de usar la imagen.

## Errores (`web_capture/errors.py`)

| Excepción | Causa |
|---|---|
| `InvalidUrlError` | esquema no soportado (`file://`, etc.) o URL inalcanzable (DNS/conexión) |
| `CaptureTimeoutError` | timeout cargando la página, `wait_for_selector` o `network_idle` |
| `SelectorNotFoundError` | el selector no matchea ningún elemento |
| `SelectorHiddenError` | el selector existe pero no es visible |
| `BrowserNotInstalledError` | falta `playwright install chromium` |
| `ScreenshotError` | Playwright no pudo generar el screenshot |
| `ScreenshotRejectedError` | el chequeo de visión rechazó la imagen por publicidad/artefactos (ver Validación visual arriba) |
| `RegionTooSmallError` | el zoom pedido recortaría menos de `MIN_CROP_PX` (64px) de la captura |
| `EncodeError` | `ffmpeg` no está instalado, frame de tamaño incorrecto, o falló el encode |
Por seguridad, `capture_url` solo acepta `http://`/`https://` (no
`file://`/`javascript:`/`data:`); todo timeout es obligatorio, nunca espera
indefinida.

## CLI de prueba

Pendiente (Fase F del plan): `scripts/web_capture.py`. Mientras tanto, usar
la API directamente (ver ejemplos arriba) o `python -c "..."`.

## Tests

`tests/web_capture/` — 55 tests, ninguno depende de internet
(`conftest.py::local_server` sirve `tests/web_capture/fixtures/*.html` por
HTTP local). Los que requieren Chromium están marcados
`@pytest.mark.playwright` y se saltan con mensaje explícito si no está
instalado.

```bash
python -m pytest
```

## Nota: quirk conocido de `build.py` con Manim (no relacionado a este módulo)

Al verificar `--combine` mezclando una escena Manim real con una escena
`web`, se detectó que **el motor Manim de `build.py` no pasa `--media_dir`
al subproceso `manim`**: el video termina en `<repo_root>/media/videos/scene/...`
(nombre de módulo, siempre "scene" porque todo `scene.py` se llama igual)
en vez de `tenant.media_dir/videos/<carpeta>/...`, que es lo que asume
`output_path_for()`. Es el mismo comportamiento que ya advierte
`lostops/README.md` ("Manim nombra la carpeta de salida por la altura...").
Preexistente, no introducido por este módulo, no tocado acá: el engine
`web` sí escribe exactamente donde `output_path_for()` espera (verificado).
Queda fuera de esta fase — requiere decidir si se agrega `--media_dir` al
comando Manim o se ajusta `output_path_for()` para reflejar el
comportamiento real, y no fue pedido.
