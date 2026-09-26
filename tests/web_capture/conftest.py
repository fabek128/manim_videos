"""Fixtures compartidas de los tests de `web_capture`.

- `local_server`: sirve `tests/web_capture/fixtures/` por HTTP real en
  `127.0.0.1` (puerto libre), para no depender de internet.
- `browser_manager`: un único Chromium reutilizado por toda la sesión de
  tests (mismo principio de performance que el módulo real). Si Chromium no
  está instalado, los tests que lo requieren se saltan con mensaje
  explícito en vez de fallar.
"""

from __future__ import annotations

import http.server
import socket
import threading
from pathlib import Path
from typing import Iterator

import pytest

from noticia_carrusel.web_capture.browser import BrowserManager
from noticia_carrusel.web_capture.errors import BrowserNotInstalledError

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(FIXTURES_DIR), **kwargs)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - firma de la stdlib
        pass  # silencia el access log en la salida de pytest


@pytest.fixture(scope="session")
def local_server() -> Iterator[str]:
    """`http://127.0.0.1:<puerto>` sirviendo `fixtures/`. Vive toda la sesión."""
    port = _free_port()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), _QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def browser_manager() -> Iterator[BrowserManager]:
    """Un solo `BrowserManager` para toda la sesión de tests."""
    try:
        with BrowserManager() as manager:
            yield manager
    except BrowserNotInstalledError as exc:
        pytest.skip(f"Chromium no instalado ({exc}); corré: playwright install chromium")


@pytest.fixture(autouse=True)
def _mock_vision_clean_by_default(monkeypatch, request):
    """Evita llamadas reales al LLM de visión en tests que no lo prueban.

    Por defecto toda captura se asume limpia; los tests de visión
    (`test_vision.py`) sobreescriben este mock con su propio
    `monkeypatch.setattr` para probar casos dirty/clean.
    """
    # No aplicar a tests que explícitamente prueban visión con LLM mockeado
    if "test_vision" in request.node.nodeid:
        return
    try:
        from noticia_carrusel.web_capture import vision as vision_module
        from noticia_carrusel.web_capture.models import VisionCheckResult

        def _fake_clean(image, prompt_version="v1"):  # noqa: ARG001
            return VisionCheckResult(clean=True, issues=[], confidence=0.95, raw_response='{"clean": true}')

        monkeypatch.setattr(vision_module, "check_screenshot", _fake_clean)
    except Exception:  # noqa: BLE001 - si el módulo no existe en algún contexto, no bloquear
        pass
