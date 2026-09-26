"""Fachada pública de `web_capture`.

Punto de entrada único para capturar URLs, resolver bounding boxes y
renderizar clips con movimiento de cámara. La usan el pipeline de posts, el
de video y el CLI de prueba — ninguno de ellos debería importar `browser.py`,
`frames.py` ni `encode.py` directamente.
"""

from __future__ import annotations

import logging
import tempfile
from contextlib import nullcontext
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from . import browser as _browser
from .camera import build_zoom_to_timeline
from .cache import (
    cache_key,
    load_cached,
    load_cached_bounds,
    load_cached_vision,
    store_cached,
)
from .encode import encode_frames_to_mp4
from .errors import ScreenshotRejectedError, WebCaptureError
from .frames import iter_frames
from .models import CaptureConfig, VisionCheckResult, WebSceneConfig

if TYPE_CHECKING:
    from ..tenant import TenantContext

logger = logging.getLogger(__name__)

_FALLBACK_CACHE_DIR = Path(tempfile.gettempdir()) / "agente32_web_capture"
"""Destino de las capturas cuando no se pasa `tenant` (ej. CLI standalone).
No es una caché real (no hay invalidación por config): solo asegura que
`capture_url` siempre devuelva un `Path` a un archivo persistido."""


def _save_without_tenant(cfg: CaptureConfig, image: Image.Image) -> Path:
    _FALLBACK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _FALLBACK_CACHE_DIR / f"{cache_key(cfg)}.png"
    image.save(path, format="PNG", optimize=True)
    return path


def _check_vision(image: Image.Image, cfg: CaptureConfig) -> VisionCheckResult | None:
    if not cfg.vision_check:
        return None
    try:
        from .vision import check_screenshot

        return check_screenshot(image)
    except Exception as exc:  # noqa: BLE001 - fail-open
        logger.warning("Vision QA falló para %s: %s — fail-open", cfg.url, exc)
        return VisionCheckResult(clean=True, issues=[], confidence=0.0, raw_response=None)


def _capture_cached(
    cfg: CaptureConfig,
    tenant: "TenantContext | None",
    force_capture: bool,
    manager: "_browser.BrowserManager | None",
    bounds_selector: str | None = None,
) -> tuple[Path, dict[str, float] | None]:
    """Resuelve `cfg` (+ `bounds_selector` opcional) usando la caché del
    tenant cuando aplica. Si hay hit de imagen pero faltan los bounds
    pedidos, recaptura (una sola vez) y actualiza la caché con ambos.
    Si `vision_check` está activo, valida con el rol de visión antes de
    devolver (ver Fase A6)."""
    # --- Cache hit path ---
    if tenant is not None and not force_capture:
        cached_image = load_cached(tenant, cfg)
        if cached_image is not None:
            bounds = load_cached_bounds(tenant, cfg) if bounds_selector else None
            needs_bounds = bounds_selector is not None and bounds is None
            if not needs_bounds:
                # Vision check sobre imagen cacheada si hace falta
                if cfg.vision_check:
                    vision_dict = load_cached_vision(tenant, cfg)
                    if vision_dict is None:
                        # No hay resultado previo: correr ahora sin navegar
                        try:
                            img = Image.open(cached_image).convert("RGB")
                            vision_result = _check_vision(img, cfg)
                            if vision_result and not vision_result.clean and cfg.strict_vision:
                                raise ScreenshotRejectedError(
                                    f"Screenshot en caché rechazado por visión: {vision_result.issues} (conf={vision_result.confidence}) para {cfg.url}"
                                )
                            # Actualizar sidecar con el resultado (sin re-guardar PNG si no hace falta, pero store_cached re-guarda igual)
                            if vision_result:
                                # Re-guardar para persistir vision en sidecar
                                # (sobrescribe mismo PNG, actualiza JSON)
                                img_cached = Image.open(cached_image).convert("RGB")
                                store_cached(tenant, cfg, img_cached, bounds=bounds, vision=vision_result)
                                if vision_result and not vision_result.clean:
                                    logger.warning("Vision QA cache dirty pero strict_vision=False, usando cache: %s", vision_result.issues)
                        except ScreenshotRejectedError:
                            raise
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("Vision QA sobre cache falló: %s", exc)
                    else:
                        # Ya hay visión cacheada
                        if not vision_dict.get("clean", True) and cfg.strict_vision:
                            raise ScreenshotRejectedError(
                                f"Screenshot en caché rechazado por visión: {vision_dict.get('issues')} para {cfg.url}"
                            )
                        if not vision_dict.get("clean", True):
                            logger.warning("Vision QA cache dirty (strict_vision=False): %s", vision_dict.get("issues"))
                return cached_image, bounds

    # --- Fresh capture ---
    result = _browser.capture_url(cfg, manager=manager, bounds_selector=bounds_selector, mitigate_overlays=False)
    vision_result: VisionCheckResult | None = None
    if cfg.vision_check:
        vision_result = _check_vision(result.image, cfg)
        if vision_result and not vision_result.clean:
            if cfg.strict_vision:
                raise ScreenshotRejectedError(
                    f"Screenshot rechazado por visión: {vision_result.issues} (conf={vision_result.confidence}) para {cfg.url}"
                )
            # Modo blando: hasta 3 reintentos con mitigación
            for attempt in range(1, 4):
                logger.warning("Vision QA dirty (%s) intento %d/3, reintentando con mitigación Playwright", vision_result.issues, attempt)
                try:
                    mitigated = _browser.capture_url(cfg, manager=manager, bounds_selector=bounds_selector, mitigate_overlays=True)
                    mitigated_vision = _check_vision(mitigated.image, cfg)
                    result = mitigated
                    vision_result = mitigated_vision
                    if mitigated_vision and mitigated_vision.clean:
                        logger.info("Vision QA limpio tras reintento %d/3", attempt)
                        break
                    if mitigated_vision and not mitigated_vision.clean:
                        logger.warning("Vision QA sigue dirty tras mitigación intento %d/3: %s", attempt, mitigated_vision.issues)
                        if attempt == 3:
                            logger.error("Vision QA no pasó validación tras 3 reintentos (4 evaluaciones), se detiene y se informa: %s para %s", mitigated_vision.issues, cfg.url)
                except Exception as exc2:  # noqa: BLE001
                    logger.warning("Mitigación de visión falló intento %d/3: %s — usando imagen original", attempt, exc2)
                    break
    if tenant is not None:
        path = store_cached(tenant, cfg, result.image, bounds=result.bounds, vision=vision_result)
    else:
        path = _save_without_tenant(cfg, result.image)
        # Para fallback sin tenant, no persistimos vision en sidecar (no hay cache estructurada)
        if vision_result and not vision_result.clean:
            logger.warning("Vision QA dirty en modo sin tenant: %s", vision_result.issues)
    return path, result.bounds


def capture_url(
    url: str,
    width: int = 1920,
    height: int = 1080,
    scale: int = 2,
    selector: str | None = None,
    full_page: bool = False,
    wait_for_selector: str | None = None,
    wait_for_network_idle: bool = False,
    delay_ms: int = 0,
    timeout_ms: int = 30_000,
    vision_check: bool = True,
    strict_vision: bool = False,
    tenant: "TenantContext | None" = None,
    force_capture: bool = False,
    manager: "_browser.BrowserManager | None" = None,
) -> Path:
    """Captura `url` (o `selector` dentro de ella) y devuelve el PNG
    resultante. Si `tenant` está seteado, cachea por configuración (ver
    `web_capture/cache.py`) — `force_capture=True` ignora un hit existente
    y lo regenera. Si `vision_check` está activo, valida con el rol de
    visión antes de devolver."""
    cfg = CaptureConfig(
        url=url,
        viewport=(width, height),
        scale=scale,
        full_page=full_page,
        selector=selector,
        wait_for_selector=wait_for_selector,
        wait_for_network_idle=wait_for_network_idle,
        delay_ms=delay_ms,
        timeout_ms=timeout_ms,
        vision_check=vision_check,
        strict_vision=strict_vision,
    )
    path, _bounds = _capture_cached(cfg, tenant, force_capture, manager)
    return path


def get_element_bounds(
    url: str,
    selector: str,
    timeout_ms: int = 30_000,
    manager: "_browser.BrowserManager | None" = None,
) -> dict[str, float]:
    """`{"x", "y", "width", "height"}` (píxeles de página) de `selector` en `url`."""
    return _browser.get_element_bounds(url, selector, manager=manager, timeout_ms=timeout_ms)


def render_web_clip(
    scene: WebSceneConfig,
    output_path: Path,
    tenant: "TenantContext | None" = None,
    force_capture: bool = False,
    manager: "_browser.BrowserManager | None" = None,
) -> Path:
    """Orquesta el pipeline completo: 1 captura (+ bounds si hay `zoom_to`,
    en la misma navegación) -> timeline de cámara -> frames -> MP4.

    Si no se pasa `manager`, abre y cierra un `BrowserManager` propio para
    toda la operación (una sola instancia de Chromium, no una por frame).
    """
    cfg = scene.capture
    with (_browser.BrowserManager() if manager is None else nullcontext(manager)) as mgr:
        image_path, bounds = _capture_cached(
            cfg,
            tenant,
            force_capture,
            mgr,
            bounds_selector=scene.zoom_to if not cfg.selector else None,
        )
        image = Image.open(image_path).convert("RGB")

        if scene.zoom_to:
            if bounds is None:
                raise WebCaptureError(
                    f"No se pudieron resolver los bounds de zoom_to={scene.zoom_to!r} en {cfg.url!r}"
                )
            # `bounds` está en píxeles de página; la imagen capturada está
            # escalada por `cfg.scale` (HiDPI) — llevar el bbox a ese espacio.
            scaled_bounds = {
                "x": bounds["x"] * cfg.scale,
                "y": bounds["y"] * cfg.scale,
                "width": bounds["width"] * cfg.scale,
                "height": bounds["height"] * cfg.scale,
            }
            timeline = build_zoom_to_timeline(
                scaled_bounds, image.size, scene.duration, padding=scene.padding
            )
        elif scene.camera is not None:
            timeline = scene.camera
        else:
            raise WebCaptureError(
                "WebSceneConfig necesita `camera` o `zoom_to` para generar un clip"
            )

        output_size = (cfg.viewport[0], cfg.viewport[1])
        frames = iter_frames(image, timeline, scene.duration, scene.fps, output_size)
        return encode_frames_to_mp4(frames, output_path, scene.fps, output_size)
