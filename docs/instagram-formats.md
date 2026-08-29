# Formatos de Instagram para videos e imágenes

Referencia de tamaños que Instagram soporta actualmente. Fuente de verdad para
renderizar con Manim (`-r` / `config.pixel_width` / `config.pixel_height`).

> Última verificación: 2026-08-24

## Tabla de formatos

| Formato | Medida (px) | Proporción | Uso típico |
|---|---|---|---|
| Post vertical (nuevo, priorizado) | 1080 x 1440 | 3:4 | Posts en feed — formato que Instagram prioriza |
| Post vertical clásico | 1080 x 1350 | 4:5 | Posts en feed — el clásico recomendado |
| Post cuadrado | 1080 x 1080 | 1:1 | Posts en feed |
| Post horizontal | 1080 x 608 | 1.91:1 | Posts en feed (enlace/vista previa) |
| Historia (Story) | 1080 x 1920 | 9:16 | Stories (video/imagen, máx 60s por story) |
| Reel | 1080 x 1920 | 9:16 | Reels (video vertical) |
| Portada del Reel (en el feed) | 1080 x 1440 | 3:4 | Cover del reel tal como se ve en el feed |
| Foto de perfil | 320 x 320 | 1:1 | Avatar |

## Cómo renderizar cada formato con Manim

La resolución se controla con `-r ancho,alto,fps`. Ejemplos:

```bash
# Reel / Story (1080x1920 @ 30fps)
manim -qh -r 1080,1920,30 videos/.../scene.py MiEscena

# Post vertical priorizado (1080x1440 @ 30fps)
manim -qh -r 1080,1440,30 videos/.../scene.py MiEscena

# Post cuadrado (1080x1080 @ 30fps)
manim -qh -r 1080,1080,30 videos/.../scene.py MiEscena
```

O desde Python:

```python
from manim import config

config.pixel_width = 1080
config.pixel_height = 1920  # Reel/Story
config.frame_rate = 30
```

## Notas para composición en Manim

- `frame_width` siempre es ~14.22 unidades; lo que cambia con la resolución es
  `frame_height` (= frame_width * alto/ancho). Composición pensada para 16:9
  puede quedar corta en vertical.
- Para Reels/Stories (9:16): diseñar pensando en zona superior e inferior —
  Instagram superpone UI (usuario, audio, caption) sobre esos bordes.
  Zona segura útil: centro ~1080x1420px.
- Para posts 4:5 y 3:4: mismo cuidado con bordes inferior/superior en el feed.

## Zonas seguras (Reel/Story 1080x1920)

| Zona | Rango aproximado |
|---|---|
| UI superior (nombre, fecha) | 0–220px desde arriba |
| UI inferior (audio, caption, botones) | 1320–1920px |
| Contenido seguro | y ≈ 250–1300px |

## Relación con este repo

- Los logos en `assets/logos/` están vectorizados; escalan sin pérdida a cualquier
  formato de esta tabla.
- `ThemedScene` (`utils/theme.py`) aplica paleta independiente del formato;
  combinar ambos para plantillas por formato si hace falta.
