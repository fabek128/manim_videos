import pytest

from noticia_carrusel.web_capture.api import capture_url, get_element_bounds
from noticia_carrusel.web_capture.errors import SelectorHiddenError, SelectorNotFoundError

pytestmark = pytest.mark.playwright


def test_get_element_bounds_missing_selector_raises(local_server, browser_manager):
    with pytest.raises(SelectorNotFoundError, match="#no-existe"):
        get_element_bounds(
            url=f"{local_server}/with_element.html",
            selector="#no-existe",
            timeout_ms=1500,
            manager=browser_manager,
        )


def test_get_element_bounds_hidden_selector_raises(local_server, browser_manager):
    with pytest.raises(SelectorHiddenError, match="#oculto"):
        get_element_bounds(
            url=f"{local_server}/hidden_element.html",
            selector="#oculto",
            manager=browser_manager,
        )


def test_capture_url_missing_selector_raises(local_server, browser_manager):
    with pytest.raises(SelectorNotFoundError):
        capture_url(
            url=f"{local_server}/with_element.html",
            selector="#no-existe",
            timeout_ms=1500,
            manager=browser_manager,
        )


def test_capture_url_hidden_selector_raises(local_server, browser_manager):
    with pytest.raises(SelectorHiddenError):
        capture_url(
            url=f"{local_server}/hidden_element.html",
            selector="#oculto",
            manager=browser_manager,
        )
