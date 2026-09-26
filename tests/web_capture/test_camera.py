import pytest
from pydantic import ValidationError

from noticia_carrusel.web_capture.camera import (
    MIN_CROP_PX,
    build_zoom_to_timeline,
    interpolate,
    zoom_to_selector,
)
from noticia_carrusel.web_capture.errors import RegionTooSmallError
from noticia_carrusel.web_capture.models import CameraKeyframe, CameraTimeline


def test_camera_timeline_requires_ordered_unique_times():
    with pytest.raises(ValidationError):
        CameraTimeline(
            keyframes=[
                CameraKeyframe(time=2.0, x=0.5, y=0.5, zoom=1.0),
                CameraKeyframe(time=1.0, x=0.5, y=0.5, zoom=1.0),
            ]
        )
    with pytest.raises(ValidationError):
        CameraTimeline(
            keyframes=[
                CameraKeyframe(time=1.0, x=0.5, y=0.5, zoom=1.0),
                CameraKeyframe(time=1.0, x=0.6, y=0.5, zoom=1.0),
            ]
        )


def test_interpolate_clamps_before_first_and_after_last():
    timeline = CameraTimeline(
        keyframes=[
            CameraKeyframe(time=1.0, x=0.2, y=0.2, zoom=1.0),
            CameraKeyframe(time=3.0, x=0.8, y=0.8, zoom=2.0),
        ]
    )
    before = interpolate(timeline, 0.0)
    after = interpolate(timeline, 10.0)
    assert (before.x, before.y, before.zoom) == (0.2, 0.2, 1.0)
    assert (after.x, after.y, after.zoom) == (0.8, 0.8, 2.0)


def test_interpolate_linear_midpoint_is_average():
    timeline = CameraTimeline(
        keyframes=[
            CameraKeyframe(time=0.0, x=0.0, y=0.0, zoom=1.0, easing="linear"),
            CameraKeyframe(time=2.0, x=1.0, y=1.0, zoom=3.0, easing="linear"),
        ]
    )
    mid = interpolate(timeline, 1.0)
    assert mid.x == pytest.approx(0.5)
    assert mid.y == pytest.approx(0.5)
    assert mid.zoom == pytest.approx(2.0)


def test_interpolate_ease_in_lags_behind_linear_at_midpoint():
    linear_timeline = CameraTimeline(
        keyframes=[
            CameraKeyframe(time=0.0, x=0.0, y=0.5, zoom=1.0, easing="linear"),
            CameraKeyframe(time=1.0, x=1.0, y=0.5, zoom=1.0, easing="linear"),
        ]
    )
    ease_in_timeline = CameraTimeline(
        keyframes=[
            CameraKeyframe(time=0.0, x=0.0, y=0.5, zoom=1.0, easing="linear"),
            CameraKeyframe(time=1.0, x=1.0, y=0.5, zoom=1.0, easing="ease_in"),
        ]
    )
    linear_mid = interpolate(linear_timeline, 0.5).x
    ease_in_mid = interpolate(ease_in_timeline, 0.5).x
    assert ease_in_mid < linear_mid


def test_interpolate_single_keyframe_is_constant():
    timeline = CameraTimeline(keyframes=[CameraKeyframe(time=0.0, x=0.3, y=0.7, zoom=1.5)])
    a = interpolate(timeline, 0.0)
    b = interpolate(timeline, 99.0)
    assert (a.x, a.y, a.zoom) == (b.x, b.y, b.zoom) == (0.3, 0.7, 1.5)


def test_zoom_to_selector_quarter_width_element():
    # Elemento cuadrado que ocupa 1/4 del ancho de una imagen 1000x1000:
    # zoom esperado = 4 / (1 + 2*0.15) (ver docs/web-capture-plan.md Fase B2).
    bounds = {"x": 100, "y": 100, "width": 250, "height": 250}
    keyframe = zoom_to_selector(bounds, image_size=(1000, 1000), padding=0.15, time=2.5)
    assert keyframe.zoom == pytest.approx(4 / 1.3, rel=1e-3)
    assert keyframe.x == pytest.approx((100 + 125) / 1000)
    assert keyframe.y == pytest.approx((100 + 125) / 1000)
    assert keyframe.time == 2.5


def test_zoom_to_selector_zero_size_raises():
    with pytest.raises(RegionTooSmallError):
        zoom_to_selector({"x": 0, "y": 0, "width": 0, "height": 50}, image_size=(1000, 1000))


def test_zoom_to_selector_never_zooms_below_one():
    # Elemento más grande que la imagen entera: no tiene sentido "alejar".
    bounds = {"x": 0, "y": 0, "width": 5000, "height": 5000}
    keyframe = zoom_to_selector(bounds, image_size=(1000, 1000), padding=0.0)
    assert keyframe.zoom == 1.0


def test_zoom_to_selector_too_small_region_raises():
    # Imagen minúscula: el zoom necesario para encuadrar recortaría por
    # debajo de MIN_CROP_PX.
    bounds = {"x": 0, "y": 0, "width": 2, "height": 2}
    with pytest.raises(RegionTooSmallError):
        zoom_to_selector(bounds, image_size=(2000, 2000), padding=0.15)
    # Sanity: el umbral existe y es positivo.
    assert MIN_CROP_PX > 0


def test_build_zoom_to_timeline_starts_wide_ends_on_element():
    bounds = {"x": 700, "y": 350, "width": 300, "height": 200}
    timeline = build_zoom_to_timeline(bounds, image_size=(2000, 1000), duration=3.0, padding=0.1)
    assert [k.time for k in timeline.keyframes] == [0.0, 3.0]
    start, end = timeline.keyframes
    assert (start.x, start.y, start.zoom) == (0.5, 0.5, 1.0)
    assert end.zoom > 1.0
