import numpy as np
import pytest
from PIL import Image

from noticia_carrusel.web_capture.camera import CameraState
from noticia_carrusel.web_capture.errors import RegionTooSmallError
from noticia_carrusel.web_capture.frames import _base_crop_size, _crop_rect, iter_frames
from noticia_carrusel.web_capture.models import CameraKeyframe, CameraTimeline


def _synthetic_image(width: int = 800, height: int = 600) -> Image.Image:
    """Imagen con gradiente en R (por fila) y G (por columna): crops
    distintos producen contenido distinto, útil para comparar frames."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    row_gradient = np.linspace(0, 255, height, dtype=np.uint8)
    col_gradient = np.linspace(0, 255, width, dtype=np.uint8)
    arr[:, :, 0] = row_gradient[:, None]
    arr[:, :, 1] = col_gradient[None, :]
    return Image.fromarray(arr)


def test_base_crop_size_fits_inside_source_and_matches_aspect():
    base_w, base_h = _base_crop_size((800, 600), (1080, 1920))  # aspect 9:16
    assert base_w <= 800
    assert base_h <= 600
    assert base_w / base_h == pytest.approx(1080 / 1920, rel=1e-6)


def test_crop_rect_shrinks_and_stays_in_bounds_as_zoom_grows():
    source_size = (800, 600)
    output_size = (400, 300)
    widths = []
    for zoom in (1.0, 1.5, 2.0, 4.0):
        state = CameraState(x=0.5, y=0.5, zoom=zoom)
        left, top, w, h = _crop_rect(state, source_size, output_size)
        assert 0 <= left <= source_size[0] - w
        assert 0 <= top <= source_size[1] - h
        widths.append(w)
    assert widths == sorted(widths, reverse=True)  # estrictamente monótono decreciente
    assert len(set(widths)) == len(widths)


def test_crop_rect_clamped_to_source_near_edges():
    # Centro en la esquina: el crop no puede salirse del frame.
    state = CameraState(x=0.02, y=0.02, zoom=1.0)
    left, top, w, h = _crop_rect(state, (800, 600), (400, 300))
    assert left >= 0
    assert top >= 0
    assert left + w <= 800
    assert top + h <= 600


def test_crop_rect_too_small_region_raises():
    state = CameraState(x=0.5, y=0.5, zoom=1000.0)
    with pytest.raises(RegionTooSmallError):
        _crop_rect(state, (800, 600), (400, 300))


def test_iter_frames_constant_camera_yields_identical_frames():
    image = _synthetic_image()
    timeline = CameraTimeline(keyframes=[CameraKeyframe(time=0.0, x=0.5, y=0.5, zoom=1.5)])
    frames = list(iter_frames(image, timeline, duration=0.3, fps=10, output_size=(200, 150)))
    assert len(frames) == 3
    for frame in frames[1:]:
        assert np.array_equal(frame, frames[0])


def test_iter_frames_count_and_shape():
    image = _synthetic_image()
    timeline = CameraTimeline(
        keyframes=[
            CameraKeyframe(time=0.0, x=0.5, y=0.5, zoom=1.0),
            CameraKeyframe(time=1.0, x=0.5, y=0.5, zoom=2.0),
        ]
    )
    output_size = (320, 240)
    frames = list(iter_frames(image, timeline, duration=1.0, fps=5, output_size=output_size))
    assert len(frames) == 5
    for frame in frames:
        assert frame.shape == (output_size[1], output_size[0], 3)


def test_iter_frames_zoom_changes_frame_content():
    image = _synthetic_image()
    timeline = CameraTimeline(
        keyframes=[
            CameraKeyframe(time=0.0, x=0.5, y=0.5, zoom=1.0, easing="linear"),
            CameraKeyframe(time=1.0, x=0.5, y=0.5, zoom=3.0, easing="linear"),
        ]
    )
    frames = list(iter_frames(image, timeline, duration=1.0, fps=4, output_size=(200, 150)))
    assert not np.array_equal(frames[0], frames[-1])


def test_iter_frames_propagates_region_too_small():
    image = _synthetic_image(width=100, height=100)
    timeline = CameraTimeline(keyframes=[CameraKeyframe(time=0.0, x=0.5, y=0.5, zoom=1000.0)])
    with pytest.raises(RegionTooSmallError):
        list(iter_frames(image, timeline, duration=0.1, fps=10, output_size=(50, 50)))
