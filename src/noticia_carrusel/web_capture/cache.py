"""Caché de screenshots por `(url, viewport, scale, selector, ...)`.

Evita volver a navegar/renderizar una página que no cambió al regenerar un
post o video (mismo espíritu que `intermediate/` en
`generator.py::intermediate_images`, ver `AGENTS.md` §8), pero con clave
propia por captura en vez de por-config: varias configs que capturan la
misma URL/selector comparten la misma entrada de caché.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from ..tenant import TenantContext
from .models import CaptureConfig

if TYPE_CHECKING:
    from .models import VisionCheckResult

_CACHE_FIELDS = (
    "url",
    "viewport",
    "scale",
    "full_page",
    "selector",
    "wait_for_selector",
    "wait_for_network_idle",
    "delay_ms",
)


def cache_key(cfg: CaptureConfig) -> str:
    """Hash estable de los campos que determinan el contenido capturado.

    `timeout_ms`, `vision_check` y `strict_vision` quedan fuera a propósito:
    no cambian el contenido de la imagen, solo cómo se espera o valida.
    """
    payload = {field: getattr(cfg, field) for field in _CACHE_FIELDS}
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def cached_path(tenant: TenantContext, cfg: CaptureConfig) -> Path:
    key = cache_key(cfg)
    return tenant.cache_path(Path("web_capture") / f"{key}.png")


def _meta_path(image_path: Path) -> Path:
    return image_path.with_suffix(".json")


def load_cached(tenant: TenantContext, cfg: CaptureConfig) -> Path | None:
    """PNG cacheado para `cfg`, o `None` si no hay hit. No navega."""
    path = cached_path(tenant, cfg)
    return path if path.is_file() else None


def load_cached_bounds(tenant: TenantContext, cfg: CaptureConfig) -> dict[str, float] | None:
    """Bounds guardados junto a una captura cacheada, si los hubo.

    Los bounds dependen del layout de la página en el momento de la
    captura: no se cachean por separado de la imagen, viajan en el mismo
    sidecar. Si la imagen está cacheada pero sin bounds (se guardó sin
    `zoom_to`), devuelve `None` — el llamador decide si eso alcanza o hace
    falta recapturar.
    """
    meta_path = _meta_path(cached_path(tenant, cfg))
    if not meta_path.is_file():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    bounds = data.get("bounds")
    return bounds if isinstance(bounds, dict) else None


def load_cached_vision(tenant: TenantContext, cfg: CaptureConfig) -> dict | None:
    """Resultado de visión guardado junto a una captura cacheada, si lo hay.

    Devuelve el dict serializado de `VisionCheckResult` o None. Se usa
    para no pagar el LLM dos veces sobre la misma imagen (ver Fase A6).
    """
    meta_path = _meta_path(cached_path(tenant, cfg))
    if not meta_path.is_file():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    vision = data.get("vision")
    return vision if isinstance(vision, dict) else None


def store_cached(
    tenant: TenantContext,
    cfg: CaptureConfig,
    image: Image.Image,
    bounds: dict[str, float] | None = None,
    vision: "VisionCheckResult | dict | None" = None,
) -> Path:
    """Guarda `image` en la caché de `cfg` junto a un sidecar de metadata.

    `bounds`, si se pasa, viaja en el sidecar para que una próxima captura
    con la misma `cfg` que también pida bounds pueda usarlos sin renavegar
    (ver `load_cached_bounds`). `vision` hace lo mismo para el resultado
    del chequeo de visión (ver `load_cached_vision`).
    """
    path = cached_path(tenant, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    # Normalizar vision a dict si es Pydantic
    vision_dict = None
    if vision is not None:
        if hasattr(vision, "model_dump"):
            vision_dict = vision.model_dump()  # type: ignore[union-attr]
        elif isinstance(vision, dict):
            vision_dict = vision
    meta = {
        "url": cfg.url,
        "selector": cfg.selector,
        "viewport": list(cfg.viewport),
        "scale": cfg.scale,
        "full_page": cfg.full_page,
        "bounds": bounds,
        "vision": vision_dict,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _meta_path(path).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path
