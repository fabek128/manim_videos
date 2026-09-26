from __future__ import annotations

from noticia_carrusel.video_generators.top.composer import (
    ZONA_SEGURA_MAX_FRACCION,
    _zona_segura_px,
)


def test_zona_segura_px_no_afecta_formatos_verticales() -> None:
    # 9:16 (1080x1920) y 3:4 (1080x1440) conservan los 220px declarados.
    assert _zona_segura_px(220, 1920) == 220.0
    assert _zona_segura_px(220, 1440) == 220.0


def test_zona_segura_px_clampa_renders_bajos() -> None:
    assert _zona_segura_px(220, 1080) == ZONA_SEGURA_MAX_FRACCION * 1080
    assert _zona_segura_px(220, 480) == ZONA_SEGURA_MAX_FRACCION * 480
def test_zona_segura_px_respeta_valores_bajo_el_tope() -> None:
    # 60px de 480 = 12.5% < tope → sin clamp.
    assert _zona_segura_px(60, 480) == 60.0


