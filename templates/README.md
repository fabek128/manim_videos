# Templates - Agente E32

Esta carpeta contiene los recursos de diseño reutilizables utilizados por Agente E32 para la generación de contenido en internet.

## Estructura

```
templates/
├── prompts/                 # Guías de DISEÑO VISUAL
│   ├── theme_default.md
│   ├── theme_news_cover.md
│   ├── theme_news_text.md
│   ├── theme_news_bullets.md
│   └── theme_carousel_system.md
└── posts/                   # Guías de TEXTO y estructura editorial
    ├── post_noticia.md
    ├── post_analisis.md
    ├── post_lista_top.md
    ├── post_tutorial.md
    ├── post_lanzamiento.md
    ├── carousel_noticia.md
    └── story_teaser.md
```

## Descripción

- **prompts/**: cómo se ve la pieza. Estilos, composición, portadas,
  slides interiores, consistencia de carrusel.
- **posts/**: qué dice la pieza. Estructura del caption, campos
  requeridos, límites de longitud, mapeo a los campos del YAML y reglas
  de veracidad.

Ambas capas son independientes: un mismo template de post puede
renderizarse con distintos themes visuales.

## Uso

1. El agente detecta la intención y elige el template de `posts/`.
2. Completa los campos requeridos con datos verificados.
3. Elige el theme visual de `prompts/`.
4. Escribe el YAML en `tenants/<id>/configs/images/`.
5. Genera con `scripts/generate_images.py`.

El flujo completo está documentado en `docs/agent-mode.md`.
