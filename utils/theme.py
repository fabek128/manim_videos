"""Temas visuales compartidos para los videos.

Manim no trae sistema de temas para escenas (solo para colores de la CLI).
Este modulo implementa uno minimo: paleta declarativa + patch de fuente por
defecto + Scene base que la aplica.
"""

import functools
from dataclasses import dataclass

from manim import MarkupText, Scene, Text

# ---------------------------------------------------------------------------
# Fuente por defecto del proyecto para Text/MarkupText.
# Los assets SVG de logos NO la usan: van convertidos a curvas.
# Especificacion completa: docs/fonts.md
# ---------------------------------------------------------------------------
DEFAULT_FONT = "Fira Code"


def _patch_default_font(cls, font_name: str) -> None:
    """Fuerza `font=font_name` cuando el caller no especifica una."""
    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def init(self, *args, **kwargs):
        # `font` es el 7mo parámetro posicional de Text (tras text,
        # fill_opacity, stroke_width, color, font_size, line_spacing).
        passed_positionally = len(args) >= 7
        if not passed_positionally and not kwargs.get("font"):
            kwargs["font"] = font_name
        orig_init(self, *args, **kwargs)

    cls.__init__ = init


_patch_default_font(Text, DEFAULT_FONT)
_patch_default_font(MarkupText, DEFAULT_FONT)


# ---------------------------------------------------------------------------
# Paletas
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Theme:
    """Paleta de un video: fondo y colores de marca."""

    background: str = "#000000"
    primary: str = "#FFFFFF"  # color principal (texto/figuras)
    accent: str = "#CCFF00"  # color de acento
    dark: str = "#00112B"  # azul marino agente32
    light: str = "#F9F9F9"  # blanco hueso agente32


# Temas disponibles
DEFAULT = Theme()
AGENTE32 = Theme(
    background="#000000",
    primary="#CCFF00",
    accent="#F9F9F9",
)


class ThemedScene(Scene):
    """Escena con tema aplicado automaticamente.

    Uso:
        class MiEscena(ThemedScene):
            theme = AGENTE32  # opcional; DEFAULT si se omite

            def construct(self):
                texto = Text("Hola", color=self.theme.primary)
                ...
    """

    theme: Theme = DEFAULT

    def setup(self):
        self.camera.background_color = self.theme.background
