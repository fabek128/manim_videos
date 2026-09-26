"""Motor de cámara: interpolación entre keyframes + zoom automático a un
elemento DOM a partir de su bounding box. Puro (sin I/O): no importa
Playwright ni OpenCV, así que se testea sin fixtures ni red.
"""

from __future__ import annotations

from dataclasses import dataclass

from .easing import apply_easing
from .errors import RegionTooSmallError
from .models import CameraKeyframe, CameraTimeline

MIN_CROP_PX = 64
"""Ancho/alto mínimo (en px de la imagen fuente) que puede recortar un zoom
sin quedar por debajo del umbral razonable de nitidez tras el resize final."""


@dataclass(frozen=True)
class CameraState:
    """Estado de cámara en un instante: centro normalizado + nivel de zoom."""

    x: float
    y: float
    zoom: float


def interpolate(timeline: CameraTimeline, t: float) -> CameraState:
    """Estado de cámara en el instante `t` (segundos), interpolando entre
    los keyframes de `timeline` con el easing del keyframe destino de cada
    tramo. `t` fuera de rango clampea al primer/último keyframe."""
    keyframes = timeline.keyframes
    first, last = keyframes[0], keyframes[-1]
    if len(keyframes) == 1 or t <= first.time:
        return CameraState(first.x, first.y, first.zoom)
    if t >= last.time:
        return CameraState(last.x, last.y, last.zoom)
    for prev, nxt in zip(keyframes, keyframes[1:]):
        if prev.time <= t <= nxt.time:
            span = nxt.time - prev.time
            local_t = (t - prev.time) / span if span > 0 else 1.0
            eased = apply_easing(nxt.easing, local_t)
            return CameraState(
                x=prev.x + (nxt.x - prev.x) * eased,
                y=prev.y + (nxt.y - prev.y) * eased,
                zoom=prev.zoom + (nxt.zoom - prev.zoom) * eased,
            )
    raise AssertionError(  # pragma: no cover - inalcanzable: t ya está acotado arriba
        f"t={t} fuera de los tramos de la timeline pese a los chequeos de límites"
    )


def zoom_to_selector(
    bounds: dict[str, float],
    image_size: tuple[int, int],
    padding: float = 0.15,
    time: float = 0.0,
    easing: str = "ease_in_out",
) -> CameraKeyframe:
    """Keyframe que centra y encuadra `bounds` (bbox en px de la imagen
    capturada) dejando `padding` (fracción del elemento) de aire alrededor.

    `zoom` nunca baja de 1.0 (no se "aleja" más que la vista completa). Si
    el zoom resultante recortaría una región menor a `MIN_CROP_PX` en algún
    eje, levanta `RegionTooSmallError`: la captura no tiene resolución
    suficiente para ese nivel de detalle.
    """
    width_img, height_img = image_size
    if width_img <= 0 or height_img <= 0:
        raise RegionTooSmallError(f"image_size inválido: {image_size}")
    w, h = bounds["width"], bounds["height"]
    if w <= 0 or h <= 0:
        raise RegionTooSmallError(
            f"El elemento tiene tamaño nulo (width={w}, height={h}); no se puede encuadrar"
        )
    center_x = (bounds["x"] + w / 2) / width_img
    center_y = (bounds["y"] + h / 2) / height_img
    padded_w = w * (1 + 2 * padding)
    padded_h = h * (1 + 2 * padding)
    zoom = max(1.0, min(width_img / padded_w, height_img / padded_h))
    crop_w = width_img / zoom
    crop_h = height_img / zoom
    if crop_w < MIN_CROP_PX or crop_h < MIN_CROP_PX:
        raise RegionTooSmallError(
            f"El zoom calculado ({zoom:.2f}x) recortaría una región de "
            f"{crop_w:.0f}x{crop_h:.0f}px de la captura, menor al mínimo de "
            f"nitidez ({MIN_CROP_PX}px). Capturá con mayor resolución/scale "
            "o reducí el zoom pedido."
        )
    return CameraKeyframe(
        time=time,
        x=min(max(center_x, 0.0), 1.0),
        y=min(max(center_y, 0.0), 1.0),
        zoom=zoom,
        easing=easing,
    )


def build_zoom_to_timeline(
    bounds: dict[str, float],
    image_size: tuple[int, int],
    duration: float,
    padding: float = 0.15,
    easing: str = "ease_in_out",
) -> CameraTimeline:
    """Timeline de 2 keyframes: vista completa (`t=0`) -> elemento encuadrado
    (`t=duration`). Implementa el `zoom_to_selector(selector, duration,
    padding)` del pedido; la resolución `selector -> bounds` vive en
    `api.render_web_clip` (que sí tiene acceso a Playwright)."""
    start = CameraKeyframe(time=0.0, x=0.5, y=0.5, zoom=1.0, easing="linear")
    end = zoom_to_selector(bounds, image_size, padding=padding, time=duration, easing=easing)
    return CameraTimeline(keyframes=[start, end])
