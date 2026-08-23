# Agent Instructions — Manim Videos

Proyecto de animaciones matemáticas con Manim Community v0.21.0.

## Setup

```bash
# Entorno virtual con Python 3.12
source .venv/bin/activate

# Dependencias ya instaladas: manim, ffmpeg (sistema)
```

## Estructura del proyecto

```
videos/
  YYYY-MM-DD_tema/      # Cada video en su carpeta con fecha
    scene.py             # Escenas (clases que heredan de Scene)
media/                   # Output renderizado (gitignored)
utils/                   # Utilidades compartidas
build.py                 # Script de compilación
```

## Convenciones

- **Carpetas**: `videos/YYYY-MM-DD_tema/` (fecha + tema descriptivo)
- **Archivos**: `scene.py` o nombre descriptivo si hay múltiples
- **Clases**: PascalCase, heredan de `Scene` o subclases (e.g., `MovingCameraScene`)
- **Imports**: `from manim import *` (convención estándar de Manim)
- **Output**: todo va a `media/`, está gitignored

## Script build.py

Compilador/builder para renderizar videos. Descubre escenas automáticamente.

### Comandos principales

```bash
python build.py --list                    # Listar escenas disponibles
python build.py                          # Renderizar todas (calidad baja)
python build.py --video intro            # Renderizar por nombre parcial
python build.py --video IntroScene -q h  # Calidad alta
python build.py --video intro -p         # Con preview automático
python build.py --combine                # Combinar todas en un video
python build.py --combine -q high        # Combinar en alta calidad
```

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
```

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
- Los archivos en `media/` son output generado, no editar
- Para agregar utilidades compartidas, usar `utils/`
- Las escenas se descubren por herencia de `Scene`, no por nombre de archivo
