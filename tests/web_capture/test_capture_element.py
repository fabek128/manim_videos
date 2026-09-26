import pytest
from PIL import Image

from noticia_carrusel.web_capture.api import capture_url

pytestmark = pytest.mark.playwright


def test_capture_element_matches_css_size(local_server, browser_manager):
    path = capture_url(
        url=f"{local_server}/with_element.html",
        selector="#grafico",
        width=1000,
        height=800,
        scale=1,
        manager=browser_manager,
    )
    with Image.open(path) as image:
        # #grafico mide 400x300 CSS px (ver fixtures/with_element.html);
        # tolerancia de redondeo de sub-píxel del browser.
        assert image.size[0] == pytest.approx(400, abs=2)
        assert image.size[1] == pytest.approx(300, abs=2)


def test_capture_element_hidpi_scale(local_server, browser_manager):
    path = capture_url(
        url=f"{local_server}/with_element.html",
        selector="#grafico",
        width=1000,
        height=800,
        scale=2,
        manager=browser_manager,
    )
    with Image.open(path) as image:
        assert image.size[0] == pytest.approx(800, abs=4)
        assert image.size[1] == pytest.approx(600, abs=4)


def test_capture_element_that_appears_late(local_server, browser_manager):
    # #tardio se inyecta por JS a los 300ms; capturarlo por selector debe
    # esperar a que aparezca (mismo mecanismo que get_element_bounds).
    path = capture_url(
        url=f"{local_server}/slow_dynamic.html",
        selector="#tardio",
        width=400,
        height=300,
        scale=1,
        manager=browser_manager,
    )
    with Image.open(path) as image:
        assert image.size[0] == pytest.approx(120, abs=2)
        assert image.size[1] == pytest.approx(80, abs=2)
