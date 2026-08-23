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
```

## Uso

```bash
# Activar entorno virtual
source .venv/bin/activate

# Renderizar un video (calidad baja, rápido)
manim -pql videos/2026-08-22_intro/scene.py IntroScene

# Renderizar en calidad alta
manim -pqh videos/2026-08-22_intro/scene.py IntroScene

# Renderizar en 4K
manim -pqk videos/2026-08-22_intro/scene.py IntroScene
```

## Convenciones

- Cada video vive en su carpeta con fecha y tema
- Nombre de archivo: `scene.py` (o descriptivo si hay múltiples)
- Las escenas se nombran en PascalCase
- Output renderizado va a `media/` (gitignored)
