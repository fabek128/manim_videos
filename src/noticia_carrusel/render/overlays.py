from __future__ import annotations

from PIL import Image, ImageDraw


def vertical_gradient(
    size: tuple[int, int],
    start: str = "#00000000",
    end: str = "#000000E6",
    start_at: float = 0.35,
    end_at: float = 1.0,
) -> Image.Image:
    width, height = size
    overlay = Image.new("RGBA", size)
    pixels = overlay.load()
    def rgba(value: str) -> tuple[int, int, int, int]:
        value = value.lstrip("#")
        if len(value) == 6:
            value += "FF"
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4, 6))
    sr, sg, sb, sa = rgba(start)
    er, eg, eb, ea = rgba(end)
    span = max(0.001, end_at - start_at)
    for y in range(height):
        progress = max(0.0, min(1.0, (y / max(1, height - 1) - start_at) / span))
        for x in range(width):
            pixels[x, y] = (
                round(sr + (er - sr) * progress),
                round(sg + (eg - sg) * progress),
                round(sb + (eb - sb) * progress),
                round(sa + (ea - sa) * progress),
            )
    return overlay


def add_gradient(
    image: Image.Image,
    start: str,
    end: str,
    start_at: float = 0.35,
    end_at: float = 1.0,
) -> Image.Image:
    return Image.alpha_composite(image.convert("RGBA"), vertical_gradient(image.size, start, end, start_at, end_at))


def add_soft_shadow(image: Image.Image, box: tuple[int, int, int, int], radius: int = 18, opacity: int = 100) -> Image.Image:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(box, radius=radius, fill=(0, 0, 0, opacity))
    return Image.alpha_composite(image.convert("RGBA"), layer)
