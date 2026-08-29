from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw


PRESETS: dict[str, tuple[int, int]] = {
    "post_square": (1080, 1080),
    "post_vertical": (1080, 1350),
    "story": (1080, 1920),
    "carousel_square": (1080, 1080),
    "carousel_vertical": (1080, 1350),
}


@dataclass(frozen=True)
class SafeArea:
    left: int
    top: int
    right: int
    bottom: int

    def box(self, image: Image.Image) -> tuple[int, int, int, int]:
        return (self.left, self.top, image.width - self.right, image.height - self.bottom)

    def expand(self, left: int = 0, top: int = 0, right: int = 0, bottom: int = 0) -> "SafeArea":
        """Suma margen extra en píxeles a cada lado (ver `MarginConfig`)."""
        return SafeArea(self.left + left, self.top + top, self.right + right, self.bottom + bottom)


@dataclass(frozen=True)
class CanvasSpec:
    width: int
    height: int
    safe: SafeArea

    @classmethod
    def from_format(
        cls,
        format_name: str,
        *,
        safe_left: float | None = None,
        safe_top: float | None = None,
        safe_right: float | None = None,
        safe_bottom: float | None = None,
    ) -> "CanvasSpec":
        """Resuelve dimensiones y margen seguro de un formato.

        `safe_*` son overrides opcionales como fracción del ancho
        (`safe_left`/`safe_right`) o alto (`safe_top`/`safe_bottom`)
        del lienzo. `None` conserva el default del formato.
        """
        try:
            width, height = PRESETS[format_name]
        except KeyError as exc:
            raise ValueError(f"Formato no soportado: {format_name}") from exc
        default_side = width * 0.06
        is_square = format_name in ("post_square", "carousel_square")
        if is_square:
            # Validado visualmente: badges + divisor + footer necesitan
            # esta reserva fija en formatos 1:1 (ver theme_carousel_system.md).
            default_top = height * 0.18
            default_bottom = height * 0.20
        else:
            default_top = height * 0.06
            default_bottom_ratio = 0.13 if format_name == "story" else 0.08
            default_bottom = height * default_bottom_ratio

        left = round(width * safe_left) if safe_left is not None else round(default_side)
        right = round(width * safe_right) if safe_right is not None else round(default_side)
        top = round(height * safe_top) if safe_top is not None else round(default_top)
        bottom = round(height * safe_bottom) if safe_bottom is not None else round(default_bottom)
        return cls(width, height, SafeArea(left, top, right, bottom))

    def new_image(self, color: str = "#101010") -> Image.Image:
        return Image.new("RGB", (self.width, self.height), color)


def draw_divider(draw: ImageDraw.ImageDraw, y: int, spec: CanvasSpec, color: str, width: int = 2) -> None:
    draw.line((spec.safe.left, y, spec.width - spec.safe.right, y), fill=color, width=width)
