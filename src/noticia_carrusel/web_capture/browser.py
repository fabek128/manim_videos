"""Cliente Playwright: abre una URL, espera su carga y captura un screenshot.

Reutiliza una sola instancia de Chromium entre varias capturas vía
`BrowserManager` (context manager) — no relanza el browser por cada URL ni
por cada frame; el zoom/pan se calcula después, sobre la imagen ya
capturada (ver `camera.py`/`frames.py`).
"""

from __future__ import annotations

import io
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from PIL import Image

from .errors import (
    BrowserNotInstalledError,
    CaptureTimeoutError,
    InvalidUrlError,
    ScreenshotError,
    SelectorHiddenError,
    SelectorNotFoundError,
    WebCaptureError,
)
from .models import CaptureConfig

# Fragmentos de mensajes de error de Chromium que indican una URL inválida o
# inalcanzable (DNS, conexión rechazada, etc.) en vez de una simple demora.
_INVALID_URL_MARKERS = (
    "ERR_NAME_NOT_RESOLVED",
    "ERR_INVALID_URL",
    "ERR_CONNECTION_REFUSED",
    "ERR_ADDRESS_UNREACHABLE",
    "ERR_EMPTY_RESPONSE",
    "ERR_CONNECTION_RESET",
)


@dataclass
class CaptureResult:
    """Resultado de `capture_url`: imagen decodificada + bounds si hubo selector."""

    image: Image.Image
    bounds: dict[str, float] | None = None


class BrowserManager:
    """Mantiene viva una instancia de Chromium entre varias capturas.

    Uso:
        with BrowserManager() as manager:
            capture_url(cfg_1, manager=manager)
            capture_url(cfg_2, manager=manager)
    """

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright = None
        self._browser = None

    def __enter__(self) -> "BrowserManager":
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch(headless=self._headless)
        except PlaywrightError as exc:
            self._playwright.stop()
            self._playwright = None
            raise BrowserNotInstalledError(
                "No se pudo lanzar Chromium de Playwright. Instalalo con: "
                "playwright install chromium"
            ) from exc
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    @property
    def browser(self):
        if self._browser is None:
            raise WebCaptureError(
                "BrowserManager no está abierto; usalo como context manager "
                "(with BrowserManager() as manager: ...)"
            )
        return self._browser


@contextmanager
def _manager_or_temp(manager: BrowserManager | None) -> Iterator[BrowserManager]:
    if manager is not None:
        yield manager
    else:
        with BrowserManager() as temp:
            yield temp


def _goto(page, cfg: CaptureConfig) -> None:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    try:
        page.goto(cfg.url, timeout=cfg.timeout_ms, wait_until="load")
    except PlaywrightTimeoutError as exc:
        raise CaptureTimeoutError(
            f"Timeout ({cfg.timeout_ms}ms) cargando {cfg.url!r}"
        ) from exc
    except PlaywrightError as exc:
        message = str(exc)
        if any(marker in message for marker in _INVALID_URL_MARKERS):
            raise InvalidUrlError(
                f"URL inválida o inalcanzable: {cfg.url!r} ({message})"
            ) from exc
        raise WebCaptureError(f"Playwright no pudo navegar a {cfg.url!r}: {message}") from exc

    try:
        if cfg.wait_for_network_idle:
            page.wait_for_load_state("networkidle", timeout=cfg.timeout_ms)
        if cfg.wait_for_selector:
            page.wait_for_selector(cfg.wait_for_selector, timeout=cfg.timeout_ms, state="visible")
        if cfg.delay_ms:
            page.wait_for_timeout(cfg.delay_ms)
    except PlaywrightTimeoutError as exc:
        raise CaptureTimeoutError(
            f"Timeout ({cfg.timeout_ms}ms) esperando wait_for_selector/network_idle en {cfg.url!r}"
        ) from exc


def _locate_visible_element(page, selector: str, url: str, timeout_ms: int):
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    try:
        page.wait_for_selector(selector, timeout=timeout_ms, state="attached")
    except PlaywrightTimeoutError as exc:
        raise SelectorNotFoundError(
            f"El selector {selector!r} no matchea ningún elemento en {url!r} "
            f"(timeout {timeout_ms}ms)"
        ) from exc
    element = page.query_selector(selector)
    if element is None:
        raise SelectorNotFoundError(f"El selector {selector!r} no matchea ningún elemento en {url!r}")
    if not element.is_visible():
        raise SelectorHiddenError(
            f"El selector {selector!r} existe en el DOM de {url!r} pero no es visible "
            "(display:none, visibility:hidden o tamaño cero)"
        )
    return element


def _try_dismiss_overlays(page) -> None:
    """Intenta cerrar cookie banners/popups comunes antes de un screenshot limpio."""
    candidates = [
        "text=Accept all",
        "text=Accept",
        "text=Got it",
        "text=Close",
        "text=Aceptar",
        "text=Entendido",
        "text=Accept cookies",
        "[aria-label*='Close' i]",
        "[aria-label*='Dismiss' i]",
        "[aria-label*='Aceptar' i]",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=500):
                loc.click(timeout=1000)
                page.wait_for_timeout(400)
                break
        except Exception:  # noqa: BLE001 - best-effort, no debe romper la captura
            continue
    # Ocultar selectores típicos de ads como fallback no destructivo
    try:
        page.add_style_tag(content='[id*="ad" i], [class*="ad-banner" i] { display: none !important; }')
        page.wait_for_timeout(200)
    except Exception:  # noqa: BLE001
        pass


def capture_url(
    cfg: CaptureConfig,
    manager: BrowserManager | None = None,
    bounds_selector: str | None = None,
    mitigate_overlays: bool = False,
) -> CaptureResult:
    """Abre `cfg.url`, espera su carga y devuelve el screenshot.

    Si `cfg.selector` está seteado, captura solo ese elemento y devuelve
    también su bounding box (píxeles de página, sin escalar por `cfg.scale`).

    `bounds_selector` (independiente de `cfg.selector`, se ignora si
    `cfg.selector` está seteado) resuelve además el bounding box de otro
    elemento **en la misma navegación** — usado por
    `api.render_web_clip` para no abrir la URL dos veces cuando necesita
    tanto el screenshot completo como el bbox del elemento a encuadrar
    (`zoom_to`).

    Reutiliza `manager` si se pasa (ver `BrowserManager`); si no, abre y
    cierra un browser temporal.
    """
    with _manager_or_temp(manager) as mgr:
        context = mgr.browser.new_context(
            viewport={"width": cfg.viewport[0], "height": cfg.viewport[1]},
            device_scale_factor=cfg.scale,
        )
        try:
            page = context.new_page()
            _goto(page, cfg)
            if mitigate_overlays:
                _try_dismiss_overlays(page)
            bounds: dict[str, float] | None = None
            if cfg.selector:
                element = _locate_visible_element(page, cfg.selector, cfg.url, cfg.timeout_ms)
                box = element.bounding_box()
                if box is None:
                    raise ScreenshotError(
                        f"No se pudo calcular el bounding box de {cfg.selector!r} en {cfg.url!r}"
                    )
                bounds = box
                try:
                    png_bytes = element.screenshot(timeout=cfg.timeout_ms)
                except Exception as exc:  # noqa: BLE001 - Playwright levanta varias clases
                    raise ScreenshotError(
                        f"Playwright no pudo capturar el elemento {cfg.selector!r} en {cfg.url!r}: {exc}"
                    ) from exc
            else:
                if bounds_selector:
                    element = _locate_visible_element(page, bounds_selector, cfg.url, cfg.timeout_ms)
                    box = element.bounding_box()
                    if box is None:
                        raise ScreenshotError(
                            f"No se pudo calcular el bounding box de {bounds_selector!r} en {cfg.url!r}"
                        )
                    bounds = box
                try:
                    png_bytes = page.screenshot(full_page=cfg.full_page, timeout=cfg.timeout_ms)
                except Exception as exc:  # noqa: BLE001
                    raise ScreenshotError(f"Playwright no pudo capturar {cfg.url!r}: {exc}") from exc
            image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            return CaptureResult(image=image, bounds=bounds)
        finally:
            context.close()


def get_element_bounds(
    url: str,
    selector: str,
    manager: BrowserManager | None = None,
    timeout_ms: int = 30_000,
) -> dict[str, float]:
    """Bounding box (`x`, `y`, `width`, `height`, píxeles de página) de `selector` en `url`."""
    cfg = CaptureConfig(url=url, timeout_ms=timeout_ms)
    with _manager_or_temp(manager) as mgr:
        context = mgr.browser.new_context(
            viewport={"width": cfg.viewport[0], "height": cfg.viewport[1]},
            device_scale_factor=cfg.scale,
        )
        try:
            page = context.new_page()
            _goto(page, cfg)
            element = _locate_visible_element(page, selector, url, timeout_ms)
            box = element.bounding_box()
            if box is None:
                raise ScreenshotError(f"No se pudo calcular el bounding box de {selector!r} en {url!r}")
            return {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]}
        finally:
            context.close()
