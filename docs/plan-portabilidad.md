# Plan de portabilidad entre máquinas

## Objetivo

Permitir que `redes2` se clone y se use en otra máquina macOS o Linux sin depender de:

- rutas absolutas de Fabian;
- servicios accesibles únicamente por la red local o ZeroTier;
- instalaciones específicas de Homebrew o aplicaciones de macOS;
- un entorno virtual o caché creado en la máquina original;
- archivos `.env` no documentados;
- una sesión gráfica para renderizar videos.

El resultado esperado es un checkout reproducible, con el tenant `agente32` funcionando para imágenes, videos, captura web y publicación local mediante configuración externa.

## Alcance

Incluye:

- generación de imágenes y carruseles;
- render de videos con Manim;
- captura web con Playwright;
- generación opcional de texto e imágenes mediante proveedores OpenAI-compatible;
- publicación local de archivos aprobados;
- instalación limpia en macOS y Linux;
- ejecución en una máquina con escritorio o headless.

No incluye:

- crear una base de datos;
- introducir Docker como requisito;
- migrar el proyecto a otro framework;
- automatizar publicaciones en Instagram;
- copiar credenciales desde la máquina actual;
- cambiar la identidad o los assets del tenant `agente32`.

## Estado actual y bloqueos

| Bloqueo | Severidad | Ubicación | Estado objetivo |
|---|---:|---|---|
| Ruta `/Users/fabian/Documents/shared` hardcodeada | Alta | `scripts/publish_final.py:49-60`, `tenants/agente32/.env.example` | Publicación controlada por `FINAL_OUTPUT_DIR`, sin fallback personal obligatorio |
| PromptGate con IP privada como default | Alta | `scripts/promptgate_client.py:22`, `src/noticia_carrusel/vision/vision.py`, `.env.example` | Endpoint obligatorio y configurable; ningún IP personal en código o ejemplos |
| Credenciales dependientes de `.env` local | Alta | `.env`, `tenants/agente32/.env` | Ejemplos completos sin secretos; checklist de configuración manual |
| Manim, FFmpeg y FFprobe externos | Alta | `build.py:81-106`, `build.py:442`, `build.py:553-570` | Dependencias declaradas y diagnóstico automático de herramientas |
| `requirements.txt` no declara Manim | Alta | `requirements.txt`, `pyproject.toml` | Una única fuente de dependencias, lockfile y procedimiento de instalación único |
| Preview gráfico activado por defecto | Media | `build.py:617-619` | Preview desactivado por defecto; activación explícita con `--preview` |
| Chromium de Playwright no instalado por `pip` | Media | `src/noticia_carrusel/web_capture/browser.py:64-75` | Instalación documentada y diagnóstico de Chromium |
| Fallback absoluto de Inkscape para macOS | Media | `scripts/fetch_logo.py:45-48` | Buscar primero en `PATH`; fallback por plataforma o mensaje accionable |
| CairoSVG opcional y silencioso | Media | `src/noticia_carrusel/render/templates.py:8-17,84-92` | Dependencia declarada o error explícito cuando un SVG sea necesario |
| Rutas absolutas en manifests generados | Baja | `tenants/agente32/assets/backgrounds/manifest.json`, `vision_review.json` | Metadatos relativos o regenerables en cualquier checkout |

## Decisiones técnicas

1. **El repositorio sigue siendo filesystem-first.** No se agrega base de datos ni servicio obligatorio.
2. **El tenant continúa resolviéndose con `--tenant > TENANT > DEFAULT_TENANT`.** La lógica existente de `TenantContext` se conserva.
3. **Toda configuración de máquina va a variables de entorno.** No se agregan rutas personales al código.
4. **Los proveedores externos son opcionales por flujo.** El render local debe funcionar sin OpenRouter ni PromptGate cuando se desactivan las funciones de IA.
5. **macOS y Linux son los targets iniciales.** Windows queda fuera del primer corte si requiere instrucciones o cambios específicos adicionales.
6. **La ejecución headless es un requisito.** Un servidor remoto debe poder renderizar usando `--no-preview` y sin reproductor gráfico.
7. **Los errores de entorno deben ser explícitos.** No se deben ocultar errores de fuentes, SVG, proveedores o herramientas externas.

## Fase 0 — Baseline y contrato de ejecución

### Tareas

- [ ] Confirmar los flujos mínimos que deben funcionar en otra máquina:
  - [ ] `generate_images.py` con una configuración sin IA.
  - [ ] `build.py --list`.
  - [ ] un render de video sin preview.
  - [ ] una captura web con Chromium instalado.
  - [ ] publicación de una imagen a un directorio configurable.
- [ ] Confirmar que `agente32` es el tenant de smoke test.
- [ ] Definir el comando oficial de instalación y eliminar instrucciones contradictorias entre `README.md`, `AGENTS.md`, `requirements.txt` y `pyproject.toml`.
- [ ] Definir versiones mínimas y estrategia de actualización.

### Criterio de aceptación

Existe una lista corta de comandos oficiales para instalar, diagnosticar y ejecutar el proyecto. Ningún flujo depende de ejecutar comandos desde `/Users/fabian/code/personal/redes2`.

## Fase 1 — Eliminar rutas y endpoints personales

### 1.1 Publicación configurable

Archivo: `scripts/publish_final.py`.

- [ ] Eliminar el fallback `/Users/fabian/Documents/shared` de `_final_root()`.
- [ ] Exigir `FINAL_OUTPUT_DIR` para publicar, o definir un fallback portable basado en una ruta configurable del usuario.
- [ ] Mantener la validación de ruta absoluta.
- [ ] Mantener el namespace del tenant: `<FINAL_OUTPUT_DIR>/<namespace>/videos` e `images`.
- [ ] Actualizar `tenants/agente32/.env.example` con un placeholder portable, no con una ruta personal.
- [ ] Actualizar `README.md` y `AGENTS.md` con ejemplos usando `/ruta/de/salida`.

### 1.2 PromptGate configurable

Archivos:

- `scripts/promptgate_client.py`;
- `src/noticia_carrusel/vision/vision.py`;
- `.env.example`;
- `README.md`.

- [ ] Eliminar `10.125.115.196` como valor por defecto.
- [ ] Mantener `PROMPTGATE_BASE_URL` como configuración explícita.
- [ ] Cuando falte el endpoint, mostrar qué variable falta y qué funcionalidades quedan deshabilitadas.
- [ ] Mantener la posibilidad de usar un endpoint OpenAI-compatible alternativo.
- [ ] No enviar credenciales cuando `PROMPTGATE_AUTH=none`.
- [ ] Validar `/models` antes de ejecutar generación de texto.
- [ ] Documentar un modo local sin PromptGate: render sin post automático usando `--no-post`.

### Criterio de aceptación

Una máquina nueva no intenta conectarse a una IP privada ni escribe en una ruta perteneciente a otro usuario. Los comandos sin proveedor configurado fallan con un mensaje claro o continúan en modo sin IA cuando el flujo lo permite.

## Fase 2 — Unificar y reproducir dependencias

### 2.1 Fuente única de dependencias

- [ ] Elegir `pyproject.toml` como fuente principal.
- [ ] Declarar explícitamente las dependencias usadas directamente por el código:
  - [ ] `manim>=0.21.0`;
  - [ ] `Pillow`;
  - [ ] `opencv-python-headless`;
  - [ ] `pydantic`;
  - [ ] `requests`;
  - [ ] `PyYAML`;
  - [ ] `playwright`;
  - [ ] `cairosvg`;
  - [ ] `numpy`, si el código lo importa directamente fuera de una dependencia transitiva.
- [ ] Decidir si `requirements.txt` se elimina o se genera desde el proyecto.
- [ ] Mantener `pytest` en un grupo de desarrollo, no en runtime.
- [ ] Generar y versionar `uv.lock`.
- [ ] Probar la instalación desde cero usando únicamente el procedimiento documentado.

### 2.2 Herramientas del sistema

Documentar por sistema operativo:

- `ffmpeg` y `ffprobe` para render, trim y combinación;
- `inkscape` únicamente para convertir logos a paths con `fetch_logo.py --for-manim`;
- Chromium administrado por Playwright;
- una terminal compatible con los comandos del proyecto.

No usar `brew install` como única instrucción. Incluir comandos para macOS y Linux y una nota para Windows si se mantiene soporte parcial.

### 2.3 Diagnóstico de entorno

Crear `scripts/doctor.py` con estas comprobaciones:

- versión de Python `>=3.12`;
- import de `manim`, `Pillow`, `cv2`, `pydantic`, `yaml`, `requests`, `cairosvg` y `playwright`;
- presencia de `manim`, `ffmpeg` y `ffprobe` en `PATH`;
- disponibilidad de Chromium de Playwright;
- existencia del tenant solicitado;
- existencia de `DEFAULT_TENANT` o `TENANT`;
- presencia de `FINAL_OUTPUT_DIR` cuando se valida publicación;
- formato válido de `PROMPTGATE_BASE_URL` cuando se configura PromptGate;
- presencia de fuentes y assets declarados por el tenant.

El diagnóstico debe devolver código distinto de cero solamente cuando el flujo solicitado no puede ejecutarse.

### Criterio de aceptación

Una instalación limpia produce un diagnóstico legible y permite distinguir entre:

- entorno incompleto;
- feature opcional sin configurar;
- error real del proyecto.

## Fase 3 — Soporte headless y herramientas externas

### 3.1 Render de Manim

Archivo: `build.py`.

- [ ] Cambiar el preview por defecto a desactivado.
- [ ] Mantener `--preview` como activación explícita.
- [ ] Mantener `--no-preview` por compatibilidad.
- [ ] Ejecutar Manim con el intérprete del entorno virtual o verificar el binario encontrado antes de iniciar.
- [ ] Incluir en el error la ruta o comando faltante.

### 3.2 FFmpeg y FFprobe

- [ ] Validar `shutil.which("ffmpeg")` y `shutil.which("ffprobe")` antes de renderizar o combinar.
- [ ] Reemplazar mensajes que solo indican `brew install ffmpeg` por instrucciones neutrales al sistema operativo.
- [ ] Mantener los comandos sin shell para evitar diferencias innecesarias entre sistemas.

### 3.3 Apertura de archivos

- [ ] Mantener `open`, `xdg-open` y `start` como funcionalidades opcionales.
- [ ] Si no existe una sesión gráfica, informar que el archivo fue generado y omitir la apertura.
- [ ] El render nunca debe fallar solamente porque `--open` no puede abrir un reproductor.

### Criterio de aceptación

En una máquina headless, este flujo termina con un MP4 válido:

```bash
.venv/bin/python build.py \
  --tenant agente32 \
  --video <video> \
  --no-preview \
  --no-post
```

No requiere `$DISPLAY`, QuickTime, Finder ni una sesión gráfica.

## Fase 4 — Playwright, SVG y assets

### 4.1 Captura web

- [ ] Mantener `playwright` como dependencia Python.
- [ ] Documentar explícitamente:

```bash
.venv/bin/python -m playwright install chromium
```

- [ ] Hacer que el diagnóstico detecte Chromium faltante antes de iniciar el flujo.
- [ ] Mantener el error `BrowserNotInstalledError` con el comando exacto de reparación.
- [ ] No descargar browsers automáticamente durante un render.

### 4.2 SVG y CairoSVG

- [ ] Declarar `cairosvg` si se mantienen logos SVG como input de Pillow.
- [ ] Si CairoSVG es opcional, cambiar el comportamiento silencioso de `templates.py` por un warning o error cuando el logo sea obligatorio.
- [ ] Mantener las versiones `<slug>_paths.svg` para escenas de Manim.
- [ ] Hacer que `fetch_logo.py` busque Inkscape primero mediante `PATH`.
- [ ] Separar la detección de Inkscape por sistema operativo; nunca asumir `/Applications/Inkscape.app`.

### 4.3 Fuentes

- [ ] Verificar que todas las fuentes requeridas estén incluidas en `assets/fonts/`.
- [ ] No depender de fuentes instaladas en macOS.
- [ ] Documentar que los SVG con texto fuente deben convertirse a paths antes de distribuirlos.
- [ ] Revisar `fabian128k_src.svg`, que contiene una familia de fuente específica de macOS, y usar la versión convertida a paths durante runtime.

### Criterio de aceptación

Los logos, textos y fuentes se renderizan igual en una instalación limpia sin fuentes propietarias instaladas en el sistema.

## Fase 5 — Configuración y secretos

### 5.1 `.env` raíz

- [ ] Mantener `.env` fuera de Git.
- [ ] Completar `.env.example` con todas las variables soportadas y valores vacíos o neutros.
- [ ] No incluir IPs privadas, rutas personales, tokens ni passwords reales.
- [ ] Separar variables obligatorias de opcionales.
- [ ] Indicar qué comandos requieren cada variable.

Variables mínimas documentadas:

```env
DEFAULT_TENANT=agente32
FINAL_OUTPUT_DIR=/ruta/absoluta/de/salida
```

Variables opcionales:

```env
PROMPTGATE_BASE_URL=https://endpoint.example/v1
PROMPTGATE_AUTH=none
PROMPTGATE_MODEL=modelo-disponible
OPENROUTER_API_KEY=
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
```

### 5.2 `.env` del tenant

- [ ] Mantener secretos de redes en `tenants/<tenant>/.env`.
- [ ] Mantener `tenants/<tenant>/.env.example` sin valores reales.
- [ ] Explicar que los secretos deben configurarse de nuevo en cada máquina.
- [ ] No convertir credenciales de redes sociales en requisito para generar o renderizar contenido local.

### 5.3 Rotación

- [ ] Rotar cualquier token que haya sido compartido fuera de un gestor seguro.
- [ ] Revisar que los secretos no aparezcan en logs, manifests, sesiones ni documentación.
- [ ] Agregar una comprobación de secretos accidentales en CI o en `scripts/doctor.py`.

### Criterio de aceptación

El repositorio puede copiarse o clonarse sin transportar secretos. El proyecto explica exactamente qué valores debe crear el operador en la máquina nueva.

## Fase 6 — Limpiar metadatos dependientes de la máquina

### Tareas

- [ ] Reemplazar rutas absolutas en `tenants/agente32/assets/backgrounds/manifest.json` por rutas relativas al directorio del tenant.
- [ ] Reemplazar rutas absolutas en `vision_review.json` por rutas relativas.
- [ ] Verificar otros JSON/YAML versionados con `/Users/fabian`, `/Volumes`, `/home` o `C:\`.
- [ ] Mantener timestamps, costos y resultados de QA, pero hacer que sus paths sean relocatables.
- [ ] Regenerar manifests después del cambio.
- [ ] Confirmar que `backgrounds.py` continúa ignorando los manifests como assets renderizables.

### Criterio de aceptación

Después de clonar el repo en otra ruta, ningún manifest versionado apunta a la máquina original y los assets se resuelven desde el checkout nuevo.

## Fase 7 — Documentación de instalación y operación

### README.md

- [ ] Reemplazar rutas `/Users/fabian/...` por placeholders.
- [ ] Añadir una sección “Instalación desde cero”.
- [ ] Añadir una sección “Modo headless”.
- [ ] Añadir una sección “Proveedores opcionales”.
- [ ] Añadir una sección “Publicación local”.
- [ ] Referenciar `scripts/doctor.py` como primer diagnóstico.

### AGENTS.md

- [ ] Mantener las reglas editoriales y multi-tenant.
- [ ] Eliminar instrucciones que asuman Homebrew o una ruta absoluta personal.
- [ ] Documentar la resolución del tenant y el contrato de configuración portable.

### Documentos específicos

- [ ] Actualizar `docs/web-capture.md` con instalación de Chromium y diagnóstico.
- [ ] Actualizar `docs/fonts.md` con la política de fuentes incluidas y SVG convertido a paths.
- [ ] Añadir este plan al índice o sección de documentación del README.

## Fase 8 — Validación en una máquina limpia

### Preparación

- [ ] Crear un checkout nuevo en una ruta distinta.
- [ ] No copiar `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache` ni caches del tenant.
- [ ] Crear los archivos de entorno desde los ejemplos.
- [ ] Configurar únicamente el tenant `agente32` y los proveedores necesarios.

### Smoke tests

Ejecutar en este orden:

```bash
.venv/bin/python scripts/doctor.py --tenant agente32
.venv/bin/python build.py --tenant agente32 --list
.venv/bin/python scripts/generate_images.py \
  --tenant agente32 \
  post \
  --config draft_smoke.yaml
```

Para video:

```bash
.venv/bin/python build.py \
  --tenant agente32 \
  --video <video> \
  --no-preview \
  --no-post
```

Para web capture:

```bash
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/generate_images.py \
  --tenant agente32 \
  post \
  --config post_web_capture.yaml
```

Para publicación local:

```bash
FINAL_OUTPUT_DIR=/tmp/redes2-published \
  .venv/bin/python scripts/publish_final.py \
  --tenant agente32 \
  --type images \
  --source <archivo-aprobado> \
  --date YYYY-MM-DD \
  --slug smoke-test
```

### Validación de resultados

- [ ] Las imágenes se generan dentro del tenant nuevo.
- [ ] El MP4 se genera sin preview gráfico.
- [ ] La captura web usa Chromium instalado por Playwright.
- [ ] Los logos y fuentes aparecen correctamente.
- [ ] PromptGate falla de forma explícita si no está configurado.
- [ ] OpenRouter solo se usa cuando está habilitado y autenticado.
- [ ] La publicación escribe únicamente dentro de `FINAL_OUTPUT_DIR`.
- [ ] No se crean archivos fuera del checkout salvo la salida configurada.
- [ ] No aparecen rutas de la máquina original en la salida generada.

## Definition of Done

La migración se considera terminada únicamente cuando se cumplen todos estos puntos:

- [ ] No existen rutas `/Users/fabian`, `/Volumes` ni IPs privadas personales en código o ejemplos operativos.
- [ ] `FINAL_OUTPUT_DIR` controla toda publicación local.
- [ ] PromptGate tiene endpoint configurable y no hay default privado hardcodeado.
- [ ] Las dependencias Python están unificadas y lockeadas.
- [ ] `manim`, `ffmpeg`, `ffprobe`, Chromium e Inkscape tienen diagnóstico claro.
- [ ] El render headless funciona con `--no-preview`.
- [ ] Los SVG y fuentes funcionan sin dependencias gráficas propias de macOS.
- [ ] Los manifests versionados no contienen rutas absolutas de la máquina original.
- [ ] La instalación limpia pasa `scripts/doctor.py` y los smoke tests.
- [ ] El README permite a otra persona preparar el entorno sin consultar la máquina original.

## Orden recomendado de implementación

1. Eliminar rutas personales de publicación.
2. Eliminar defaults privados de PromptGate.
3. Unificar dependencias y crear lockfile.
4. Agregar `scripts/doctor.py`.
5. Desactivar preview por defecto y robustecer herramientas externas.
6. Declarar CairoSVG y validar SVG/fuentes.
7. Normalizar manifests generados.
8. Actualizar README, AGENTS y documentación específica.
9. Ejecutar validación desde checkout limpio en macOS.
10. Repetir validación desde checkout limpio en Linux.
