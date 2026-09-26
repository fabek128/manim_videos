"""Captura de URLs (Playwright) + motor de cámara (zoom/pan) desacoplado de Manim.

Arquitectura (ver `docs/web-capture-plan.md`):

    URL -> Playwright -> screenshot HiDPI -> Camera Engine -> OpenCV
        -> frames -> FFmpeg -> clip / recurso de post

Uso típico vía la fachada pública en `web_capture.api`:

    from noticia_carrusel.web_capture.api import capture_url, get_element_bounds, render_web_clip
"""

from __future__ import annotations
