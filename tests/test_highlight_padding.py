from __future__ import annotations

from pathlib import Path

from PIL import Image

from noticia_carrusel.render.text_engine import TextEngine


def test_highlight_background_has_uniform_padding_around_visible_glyphs():
    """El fondo de highlight debe dejar el mismo padding visible en los cuatro lados."""
    root = Path(__file__).parents[1]
    engine = TextEngine(
        title_font=root / "assets/fonts/Montserrat-ExtraBold.ttf",
        body_font=root / "assets/fonts/Inter-SemiBold.ttf",
        code_font=root / "assets/fonts/FiraCode-Regular.ttf",
    )
    image = Image.new("RGB", (700, 160), "#15243A")
    engine.draw_highlights(
        image,
        (40, 40),
        "IMAGEN DE PRUEBA",
        ["PRUEBA"],
        max_width=620,
        font_size=60,
        text_color="#FFFFFF",
        highlight_color="#0057D9",
        padding=10,
        max_lines=1,
    )
    pixels = image.load()

    import numpy as np

    arr = np.array(image)
    bg_mask = (arr == (0, 87, 217)).all(axis=2)
    ink_mask = (arr == (255, 255, 255)).all(axis=2)
    bg_y, bg_x = np.where(bg_mask)
    assert len(bg_x) and len(bg_y)
    # Restringir la tinta al área del highlight para ignorar el resto del título.
    y0, y1, x0, x1 = bg_y.min(), bg_y.max(), bg_x.min(), bg_x.max()
    ink_in_bg = ink_mask[y0:y1 + 1, x0:x1 + 1]
    ink_y, ink_x = np.where(ink_in_bg)
    assert len(ink_x) and len(ink_y)
    pads = (
        int(ink_y.min() - 0),  # T: desde top del highlight
        int((y1 - y0) - 1 - ink_y.max()),  # B: desde bottom del highlight
        int(ink_x.min() - 0),  # L: desde left del highlight
        int((x1 - x0) - 1 - ink_x.max()),  # R: desde right del highlight
    )
    assert pads[0] == pads[1] == pads[2] == pads[3], f"padding no uniforme: {pads}"
    assert pads[0] >= 8
