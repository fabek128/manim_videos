"""Errores del módulo de captura web. Ninguno se silencia ni se envuelve en
`Exception` genérica: cada caso listado en `docs/web-capture-plan.md` tiene
una subclase propia con mensaje accionable."""

from __future__ import annotations


class WebCaptureError(RuntimeError):
    """Base de todos los errores de `web_capture`."""


class InvalidUrlError(WebCaptureError):
    """URL con esquema no soportado o malformada."""


class CaptureTimeoutError(WebCaptureError):
    """La navegación, la espera de un selector o el network-idle excedió el timeout."""


class SelectorNotFoundError(WebCaptureError):
    """El selector no matchea ningún elemento dentro del timeout."""


class SelectorHiddenError(WebCaptureError):
    """El selector existe en el DOM pero no está visible (display:none, etc.)."""


class BrowserNotInstalledError(WebCaptureError):
    """Playwright no encuentra el binario de Chromium instalado."""


class ScreenshotError(WebCaptureError):
    """Playwright no pudo generar el screenshot (página/elemento)."""


class RegionTooSmallError(WebCaptureError):
    """El crop resultante es demasiado pequeño para el zoom pedido."""


class EncodeError(WebCaptureError):
    """FFmpeg falló al codificar los frames a MP4."""


class ScreenshotRejectedError(WebCaptureError):
    """El chequeo de visión rechazó el screenshot por publicidad/artefactos."""
