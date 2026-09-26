"""Genera los frames BGR (listos para `encode.py`) recortando/escalando un
screenshot único según una `CameraTimeline` interpolada. Puro OpenCV: no
vuelve a abrir el browser por frame (ver "Performance" en
`docs/web-capture-plan.md`)."""

from __future__ import annotations

from typing import Iterator

import cv2
import numpy as np
from PIL import Image

from ..vision.image_ops import pil_to_bgr
from .camera import MIN_CROP_PX, CameraState, interpolate
from .errors import RegionTooSmallError
from .models import CameraTimeline


def _base_crop_size(source_size: tuple[int, int], output_size: tuple[int, int]) -> tuple[float, float]:
    """Tamaño del crop a `zoom=1.0`: el rectángulo más grande con el aspect
    de `output_size` que entra dentro de `source_size` ("cover")."""
    src_w, src_h = source_size
    out_w, out_h = output_size
    aspect = out_w / out_h
    base_w = min(src_w, src_h * aspect)
    base_h = base_w / aspect
    return base_w, base_h


def _crop_rect(
    state: CameraState,
    source_size: tuple[int, int],
    output_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Rectángulo de crop `(left, top, width, height)` en píxeles de la
    imagen fuente para el estado de cámara `state`. Siempre dentro de los
    límites de `source_size` (a `zoom >= 1.0` el crop base solo se achica)."""
    src_w, src_h = source_size
    base_w, base_h = _base_crop_size(source_size, output_size)
    crop_w = base_w / state.zoom
    crop_h = base_h / state.zoom
    if crop_w < MIN_CROP_PX or crop_h < MIN_CROP_PX:
        raise RegionTooSmallError(
            f"El zoom {state.zoom:.2f}x recortaría {crop_w:.0f}x{crop_h:.0f}px "
            f"de la captura, menor al mínimo de nitidez ({MIN_CROP_PX}px)"
        )
    center_x = state.x * src_w
    center_y = state.y * src_h
    left = min(max(center_x - crop_w / 2, 0.0), src_w - crop_w)
    top = min(max(center_y - crop_h / 2, 0.0), src_h - crop_h)
    return int(round(left)), int(round(top)), int(round(crop_w)), int(round(crop_h))


def iter_frames(
    image: Image.Image,
    timeline: CameraTimeline,
    duration: float,
    fps: int,
    output_size: tuple[int, int],
) -> Iterator[np.ndarray]:
    """Un frame BGR por cada `1/fps` segundos de `duration`, recortando
    `image` según la cámara interpolada (`camera.interpolate`) en cada
    instante y reescalando al tamaño de salida con Lanczos (buena calidad en
    zooms altos)."""
    source = pil_to_bgr(image)
    src_h, src_w = source.shape[:2]
    total_frames = max(1, round(duration * fps))
    for i in range(total_frames):
        t = i / fps
        state = interpolate(timeline, t)
        left, top, crop_w, crop_h = _crop_rect(state, (src_w, src_h), output_size)
        cropped = source[top : top + crop_h, left : left + crop_w]
        yield cv2.resize(cropped, output_size, interpolation=cv2.INTER_LANCZOS4)
