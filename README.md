# Manim Videos

Colección de videos y animaciones matemáticas creadas con [Manim Community](https://www.manim.community/).

## Estructura

```
videos/
  YYYY-MM-DD_tema/
    scene.py          # Escenas del video
    README.md         # Descripción del video (opcional)
media/                # Output renderizado (auto-generado)
utils/                # Utilidades compartidas
build.py              # Script de compilación/renderizado
```

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
