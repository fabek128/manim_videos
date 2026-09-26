from __future__ import annotations

from types import SimpleNamespace

import pytest
from manim import ImageMobject, Square, config
from PIL import Image
from pydantic import ValidationError

from noticia_carrusel.video_generators.top.composer import TopComposer
from noticia_carrusel.video_generators.top.models import TopItem, TopMetric
from noticia_carrusel.video_generators.top.style import TopStyle


class _TenantAssets:
    def __init__(self, root):
        self.root = root

    def resolve_asset(self, relative: str):
        path = self.root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        return path


def test_logo_accepts_official_raster_asset(tmp_path) -> None:
    logo_path = tmp_path / "logos" / "vendor" / "vendor.png"
    logo_path.parent.mkdir(parents=True)
    Image.new("RGBA", (32, 32), (255, 255, 255, 255)).save(logo_path)
    composer = object.__new__(TopComposer)
    composer.tenant = _TenantAssets(tmp_path)
    item = SimpleNamespace(visual_asset="vendor", name="Vendor")

    logo = composer._logo(item)

    assert isinstance(logo, ImageMobject)


def test_final_ranking_defaults_to_readable_summary() -> None:
    style = TopStyle()

    assert style.ranking_show_comments is False
    assert style.ranking_show_specs is False


class _CaptureScene:
    def __init__(self) -> None:
        self.camera = SimpleNamespace(frame_height=config.frame_height)
        self.calls: list[tuple[int, object, object, dict]] = []

    def ingreso_tarjeta_puesto(
        self,
        puesto,
        objeto,
        destino,
        **kwargs,
    ):
        self.calls.append((puesto, objeto, destino, kwargs))
        return destino


def _layout_composer(items: tuple[TopItem, ...]) -> TopComposer:
    composer = object.__new__(TopComposer)
    composer.spec = SimpleNamespace(items=items)
    composer.style = TopStyle()
    composer._slots_colocados = []
    composer._titulo_ref = None
    composer._alto_zonas_u = 0.0
    composer._footer_alto = 0.0
    composer._lim_sup = config.frame_height / 2
    composer._lim_inf = -config.frame_height / 2
    composer.u_px = config.frame_height / config.pixel_height
    composer._logo = lambda _item: Square(side_length=0.4)
    composer._accent = lambda: "#FFFFFF"
    composer._dark = lambda: "#000000"
    composer._chequear_zonas = lambda *_args: None
    return composer

def test_all_cards_keep_equal_height_and_only_rank_one_is_highlighted() -> None:
    detailed = TopItem(
        name="Elemento con nombre extenso",
        metric=TopMetric(label="Tokens", value="100M"),
        comment=("Primera línea extensa", "Segunda línea extensa"),
        specs=(
            {"label": "Provider", "value": "Proveedor"},
            {"label": "Estado", "value": "Activo"},
        ),
    )
    compact = TopItem(
        name="Breve",
        metric=TopMetric(label="Tokens", value="50M"),
    )
    composer = _layout_composer((detailed, compact))
    scene = _CaptureScene()

    composer.animar_tarjeta_puesto(scene, 2, compact)
    composer.animar_tarjeta_puesto(scene, 1, detailed)

    central_heights = [call[1][0].height for call in scene.calls]
    ranking_heights = [call[2][0].height for call in scene.calls]
    pulses = {call[0]: call[3]["pulso"] for call in scene.calls}

    assert central_heights == pytest.approx([3.8, 3.8])
    assert ranking_heights == pytest.approx([1.2, 1.2])
    assert pulses == {2: 0.0, 1: composer.style.card_highlight_pulse_factor}


def test_highlighted_is_not_a_content_field() -> None:
    with pytest.raises(ValidationError):
        TopItem.model_validate({"name": "Elemento", "highlighted": True})
