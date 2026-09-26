import pytest

from noticia_carrusel.web_capture.api import get_element_bounds

pytestmark = pytest.mark.playwright


def test_get_element_bounds_matches_known_css_position(local_server, browser_manager):
    bounds = get_element_bounds(
        url=f"{local_server}/with_element.html",
        selector="#grafico",
        manager=browser_manager,
    )
    # Ver fixtures/with_element.html: left:200px top:150px width:400px height:300px.
    assert bounds["x"] == pytest.approx(200, abs=1)
    assert bounds["y"] == pytest.approx(150, abs=1)
    assert bounds["width"] == pytest.approx(400, abs=1)
    assert bounds["height"] == pytest.approx(300, abs=1)


def test_get_element_bounds_response_shape(local_server, browser_manager):
    bounds = get_element_bounds(
        url=f"{local_server}/with_element.html",
        selector="#grafico",
        manager=browser_manager,
    )
    assert set(bounds) == {"x", "y", "width", "height"}
    assert all(isinstance(v, (int, float)) for v in bounds.values())
