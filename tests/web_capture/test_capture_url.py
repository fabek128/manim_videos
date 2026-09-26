import pytest
from PIL import Image

from noticia_carrusel.web_capture.api import capture_url
from noticia_carrusel.web_capture.errors import CaptureTimeoutError

pytestmark = pytest.mark.playwright


def test_capture_url_viewport_screenshot_matches_requested_size(local_server, browser_manager, tmp_path):
    path = capture_url(
        url=f"{local_server}/simple.html",
        width=640,
        height=480,
        scale=1,
        manager=browser_manager,
    )
    assert path.is_file()
    with Image.open(path) as image:
        assert image.size == (640, 480)


def test_capture_url_hidpi_scale_multiplies_pixel_size(local_server, browser_manager):
    path = capture_url(
        url=f"{local_server}/simple.html",
        width=320,
        height=240,
        scale=2,
        manager=browser_manager,
    )
    with Image.open(path) as image:
        assert image.size == (640, 480)


def test_capture_url_full_page_is_taller_than_viewport(local_server, browser_manager):
    viewport_path = capture_url(
        url=f"{local_server}/tall.html",
        width=400,
        height=300,
        scale=1,
        full_page=False,
        manager=browser_manager,
    )
    full_path = capture_url(
        url=f"{local_server}/tall.html",
        width=400,
        height=300,
        scale=1,
        full_page=True,
        manager=browser_manager,
    )
    with Image.open(viewport_path) as viewport_image, Image.open(full_path) as full_image:
        assert viewport_image.size == (400, 300)
        assert full_image.height > viewport_image.height


def test_capture_url_wait_for_selector_dynamic_content(local_server, browser_manager):
    # No debe lanzar: espera explícitamente a que #tardio aparezca (inyectado
    # por JS a los 300ms) antes de tomar el screenshot.
    path = capture_url(
        url=f"{local_server}/slow_dynamic.html",
        width=300,
        height=200,
        wait_for_selector="#tardio",
        manager=browser_manager,
    )
    assert path.is_file()


def test_capture_url_timeout_on_missing_wait_selector(local_server, browser_manager):
    from noticia_carrusel.web_capture.models import CaptureConfig
    from noticia_carrusel.web_capture import browser as web_capture_browser

    cfg = CaptureConfig(
        url=f"{local_server}/simple.html",
        wait_for_selector="#nunca-existe",
        timeout_ms=1000,
    )
    with pytest.raises(CaptureTimeoutError):
        web_capture_browser.capture_url(cfg, manager=browser_manager)
