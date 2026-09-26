"""Tests de validación visual con rol de visión."""

from __future__ import annotations
import base64
import io
import json

import pytest
from PIL import Image

from noticia_carrusel.web_capture.errors import ScreenshotRejectedError
from noticia_carrusel.web_capture.models import VisionCheckResult


def _fake_response(content: str):
    from unittest.mock import Mock
    mock = Mock()
    mock.raise_for_status = Mock()
    mock.json.return_value = {"choices": [{"message": {"content": content}}]}
    return mock


def test_vision_check_result_validation():
    r = VisionCheckResult(clean=True, issues=[], confidence=0.95)
    assert r.clean is True
    r2 = VisionCheckResult(clean=False, issues=["publicidad: banner"], confidence=0.8)
    assert "publicidad" in r2.issues[0]


def test_check_screenshot_clean_with_mocked_llm(monkeypatch):
    from noticia_carrusel.web_capture import vision as vision_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", "test/model")
    monkeypatch.delenv("PROMPTGATE_VISION_MODEL", raising=False)

    fake_json = json.dumps({"clean": True, "issues": [], "confidence": 0.99})
    monkeypatch.setattr("noticia_carrusel.web_capture.vision.requests.post", lambda *a, **kw: _fake_response(fake_json))

    img = Image.new("RGB", (100, 100), "white")
    result = vision_module.check_screenshot(img)
    assert result.clean is True
    assert result.confidence == pytest.approx(0.99)


def test_prepare_image_preserves_reel_resolution_with_diagnostic_border() -> None:
    from noticia_carrusel.web_capture import vision as vision_module

    encoded = vision_module._prepare_image_b64(
        Image.new("RGB", (1080, 1920), "black")
    )
    prepared = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")

    assert prepared.size == (1920, 1920)
    assert min(prepared.getpixel((420, 0))) > 200
    assert max(prepared.getpixel((960, 960))) < 30


def test_check_screenshot_sends_complete_visual_gate(monkeypatch):
    from noticia_carrusel.web_capture import vision as vision_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", "test/model")
    monkeypatch.delenv("PROMPTGATE_VISION_MODEL", raising=False)
    captured: dict = {}

    def fake_post(*args, **kwargs):
        captured.update(kwargs["json"])
        return _fake_response(
            json.dumps({"clean": True, "issues": [], "confidence": 0.99})
        )

    monkeypatch.setattr(
        "noticia_carrusel.web_capture.vision.requests.post",
        fake_post,
    )

    vision_module.check_screenshot(Image.new("RGB", (100, 100), "white"))

    prompt = captured["messages"][0]["content"][0]["text"]
    assert "texto cortado" in prompt
    assert "contraste insuficiente" in prompt
    assert "zonas seguras" in prompt
    assert "logos deformados" in prompt
    assert "objetos focales" in prompt
    assert "borde blanco" in prompt
    assert "frame de transición" in prompt
    image_payload = captured["messages"][0]["content"][1]["image_url"]
    assert image_payload["detail"] == "high"


def test_check_screenshot_dirty_detects_banner(monkeypatch):
    from noticia_carrusel.web_capture import vision as vision_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", "test/model")
    monkeypatch.delenv("PROMPTGATE_VISION_MODEL", raising=False)

    fake_json = json.dumps({"clean": False, "issues": ["publicidad: banner de suscripción", "popup: cookie banner"], "confidence": 0.88})
    monkeypatch.setattr("noticia_carrusel.web_capture.vision.requests.post", lambda *a, **kw: _fake_response(fake_json))

    img = Image.new("RGB", (100, 100), "white")
    result = vision_module.check_screenshot(img)
    assert result.clean is False
    assert any("publicidad" in i for i in result.issues)
    assert result.confidence == pytest.approx(0.88)


def test_check_screenshot_no_provider_fail_open(monkeypatch):
    from noticia_carrusel.web_capture import vision as vision_module

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_VISION_MODEL", raising=False)
    monkeypatch.delenv("PROMPTGATE_VISION_MODEL", raising=False)

    img = Image.new("RGB", (100, 100), "white")
    result = vision_module.check_screenshot(img)
    assert result.clean is True
    assert result.confidence == 0.0


def test_check_screenshot_handles_markdown_fence(monkeypatch):
    from noticia_carrusel.web_capture import vision as vision_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    fake_content = "```json\n{\"clean\": false, \"issues\": [\"popup\"], \"confidence\": 0.7}\n```"
    monkeypatch.setattr("noticia_carrusel.web_capture.vision.requests.post", lambda *a, **kw: _fake_response(fake_content))

    img = Image.new("RGB", (50, 50), "white")
    result = vision_module.check_screenshot(img)
    assert result.clean is False


def test_capture_url_vision_check_false_skips_llm(tmp_path, monkeypatch):
    from noticia_carrusel.tenant import BrandManifest, InstagramManifest, PublishManifest, SocialManifest, TenantContext, TenantManifest
    from noticia_carrusel.web_capture import api as web_capture_api
    from noticia_carrusel.web_capture import browser as web_capture_browser
    from noticia_carrusel.web_capture.models import VisionCheckResult
    import numpy as np

    manifest = TenantManifest(
        id="testtenant",
        name="Test",
        brand=BrandManifest(logo="logo.svg"),
        social=SocialManifest(instagram=InstagramManifest(handle="test")),
        publish=PublishManifest(namespace="test"),
    )
    tenant = TenantContext(id="testtenant", root=tmp_path / "testtenant", manifest=manifest)
    (tmp_path / "testtenant").mkdir()

    calls = []
    def fake_browser(cfg, manager=None, bounds_selector=None, mitigate_overlays=False):
        calls.append(1)
        return web_capture_browser.CaptureResult(image=Image.fromarray(np.zeros((10,10,3), dtype=np.uint8)), bounds=None)
    monkeypatch.setattr(web_capture_api._browser, "capture_url", fake_browser)

    vision_calls = []
    def fake_vision(img, prompt_version="v1"):
        vision_calls.append(1)
        return VisionCheckResult(clean=True, issues=[], confidence=1.0)
    monkeypatch.setattr("noticia_carrusel.web_capture.vision.check_screenshot", fake_vision)

    web_capture_api.capture_url(url="https://example.com/a", tenant=tenant, vision_check=False)
    assert vision_calls == []
    assert len(calls) == 1


def test_capture_url_strict_vision_rejects_dirty(monkeypatch, tmp_path):
    from noticia_carrusel.tenant import BrandManifest, InstagramManifest, PublishManifest, SocialManifest, TenantContext, TenantManifest
    from noticia_carrusel.web_capture import api as web_capture_api
    from noticia_carrusel.web_capture import browser as web_capture_browser
    from noticia_carrusel.web_capture.models import VisionCheckResult
    import numpy as np

    manifest = TenantManifest(
        id="testtenant", name="Test",
        brand=BrandManifest(logo="logo.svg"),
        social=SocialManifest(instagram=InstagramManifest(handle="test")),
        publish=PublishManifest(namespace="test"),
    )
    tenant = TenantContext(id="testtenant", root=tmp_path / "testtenant2", manifest=manifest)
    (tmp_path / "testtenant2").mkdir()

    def fake_browser(cfg, manager=None, bounds_selector=None, mitigate_overlays=False):
        return web_capture_browser.CaptureResult(image=Image.fromarray(np.zeros((10,10,3), dtype=np.uint8)), bounds=None)
    monkeypatch.setattr(web_capture_api._browser, "capture_url", fake_browser)

    def fake_dirty(img, prompt_version="v1"):
        return VisionCheckResult(clean=False, issues=["publicidad: banner"], confidence=0.9, raw_response="{}")
    monkeypatch.setattr("noticia_carrusel.web_capture.vision.check_screenshot", fake_dirty)

    with pytest.raises(ScreenshotRejectedError, match="publicidad"):
        web_capture_api.capture_url(url="https://example.com/a", tenant=tenant, strict_vision=True)


def test_capture_url_soft_vision_retries_once_on_dirty(monkeypatch, tmp_path):
    from noticia_carrusel.tenant import BrandManifest, InstagramManifest, PublishManifest, SocialManifest, TenantContext, TenantManifest
    from noticia_carrusel.web_capture import api as web_capture_api
    from noticia_carrusel.web_capture import browser as web_capture_browser
    from noticia_carrusel.web_capture.models import VisionCheckResult
    import numpy as np

    manifest = TenantManifest(
        id="testtenant", name="Test",
        brand=BrandManifest(logo="logo.svg"),
        social=SocialManifest(instagram=InstagramManifest(handle="test")),
        publish=PublishManifest(namespace="test"),
    )
    tenant = TenantContext(id="testtenant", root=tmp_path / "testtenant3", manifest=manifest)
    (tmp_path / "testtenant3").mkdir()

    browser_calls = []
    def fake_browser(cfg, manager=None, bounds_selector=None, mitigate_overlays=False):
        browser_calls.append(mitigate_overlays)
        return web_capture_browser.CaptureResult(image=Image.fromarray(np.zeros((10,10,3), dtype=np.uint8)), bounds=None)
    monkeypatch.setattr(web_capture_api._browser, "capture_url", fake_browser)

    vision_calls = []
    def fake_vision(img, prompt_version="v1"):
        vision_calls.append(1)
        if len(vision_calls) == 1:
            return VisionCheckResult(clean=False, issues=["popup"], confidence=0.8)
        return VisionCheckResult(clean=True, issues=[], confidence=0.9)
    monkeypatch.setattr("noticia_carrusel.web_capture.vision.check_screenshot", fake_vision)

    path = web_capture_api.capture_url(url="https://example.com/a", tenant=tenant, strict_vision=False)
    assert path.is_file()
    assert len(browser_calls) == 2
    assert browser_calls[0] is False
    assert browser_calls[1] is True
    assert len(vision_calls) == 2


def test_vision_result_cached_avoids_second_llm_call(tmp_path, monkeypatch):
    from noticia_carrusel.tenant import BrandManifest, InstagramManifest, PublishManifest, SocialManifest, TenantContext, TenantManifest
    from noticia_carrusel.web_capture import api as web_capture_api
    from noticia_carrusel.web_capture import browser as web_capture_browser
    from noticia_carrusel.web_capture.models import VisionCheckResult
    import numpy as np

    manifest = TenantManifest(
        id="testtenant", name="Test",
        brand=BrandManifest(logo="logo.svg"),
        social=SocialManifest(instagram=InstagramManifest(handle="test")),
        publish=PublishManifest(namespace="test"),
    )
    tenant = TenantContext(id="testtenant", root=tmp_path / "testtenant4", manifest=manifest)
    (tmp_path / "testtenant4").mkdir()

    def fake_browser(cfg, manager=None, bounds_selector=None, mitigate_overlays=False):
        return web_capture_browser.CaptureResult(image=Image.fromarray(np.zeros((20,20,3), dtype=np.uint8)), bounds=None)
    monkeypatch.setattr(web_capture_api._browser, "capture_url", fake_browser)

    vision_calls = []
    def fake_vision(img, prompt_version="v1"):
        vision_calls.append(1)
        return VisionCheckResult(clean=True, issues=[], confidence=0.95)
    monkeypatch.setattr("noticia_carrusel.web_capture.vision.check_screenshot", fake_vision)

    web_capture_api.capture_url(url="https://example.com/cached-vision", tenant=tenant)
    assert len(vision_calls) == 1
    web_capture_api.capture_url(url="https://example.com/cached-vision", tenant=tenant)
    assert len(vision_calls) == 1

    from noticia_carrusel.web_capture.cache import load_cached_vision
    from noticia_carrusel.web_capture.models import CaptureConfig
    cfg = CaptureConfig(url="https://example.com/cached-vision")
    v = load_cached_vision(tenant, cfg)
    assert v is not None
    assert v["clean"] is True
