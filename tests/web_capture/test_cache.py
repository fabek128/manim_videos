"""Tests de caché de `web_capture.api`. Sin Playwright real: se mockea
`browser.capture_url` para contar navegaciones — la caché debe evitarlas."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from noticia_carrusel.tenant import (
    BrandManifest,
    InstagramManifest,
    PublishManifest,
    SocialManifest,
    TenantContext,
    TenantManifest,
)
from noticia_carrusel.web_capture import api as web_capture_api
from noticia_carrusel.web_capture import browser as web_capture_browser


def _fake_tenant(tmp_path) -> TenantContext:
    manifest = TenantManifest(
        id="testtenant",
        name="Test Tenant",
        brand=BrandManifest(logo="logo.svg"),
        social=SocialManifest(instagram=InstagramManifest(handle="test")),
        publish=PublishManifest(namespace="test"),
    )
    root = tmp_path / "testtenant"
    root.mkdir()
    return TenantContext(id="testtenant", root=root, manifest=manifest)


def _patch_capture_url(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def _fake(cfg, manager=None, bounds_selector=None, mitigate_overlays=False):
        calls.append(cfg.url)
        image = Image.fromarray(np.zeros((10, 10, 3), dtype=np.uint8))
        bounds = {"x": 0, "y": 0, "width": 5, "height": 5} if bounds_selector else None
        return web_capture_browser.CaptureResult(image=image, bounds=bounds)

    monkeypatch.setattr(web_capture_api._browser, "capture_url", _fake)
    return calls


def test_second_capture_uses_cache_without_navigating(tmp_path, monkeypatch):
    tenant = _fake_tenant(tmp_path)
    calls = _patch_capture_url(monkeypatch)

    path1 = web_capture_api.capture_url(url="https://example.com/a", tenant=tenant)
    path2 = web_capture_api.capture_url(url="https://example.com/a", tenant=tenant)

    assert path1 == path2
    assert calls == ["https://example.com/a"]


def test_force_capture_ignores_existing_cache(tmp_path, monkeypatch):
    tenant = _fake_tenant(tmp_path)
    calls = _patch_capture_url(monkeypatch)

    web_capture_api.capture_url(url="https://example.com/a", tenant=tenant)
    web_capture_api.capture_url(url="https://example.com/a", tenant=tenant, force_capture=True)

    assert len(calls) == 2


def test_different_config_is_a_cache_miss(tmp_path, monkeypatch):
    tenant = _fake_tenant(tmp_path)
    calls = _patch_capture_url(monkeypatch)

    web_capture_api.capture_url(url="https://example.com/a", tenant=tenant, width=800)
    web_capture_api.capture_url(url="https://example.com/a", tenant=tenant, width=1200)

    assert len(calls) == 2


def test_cache_file_lives_under_tenant_cache_dir(tmp_path, monkeypatch):
    tenant = _fake_tenant(tmp_path)
    _patch_capture_url(monkeypatch)

    path = web_capture_api.capture_url(url="https://example.com/a", tenant=tenant)

    assert path.is_relative_to(tenant.cache_dir)
    assert path.suffix == ".png"


def test_bounds_are_cached_and_avoid_renavigating_when_zoom_to_repeats(tmp_path, monkeypatch):
    tenant = _fake_tenant(tmp_path)
    calls = _patch_capture_url(monkeypatch)

    # Primera vez sin bounds_selector: cachea la imagen, sin bounds.
    web_capture_api.capture_url(url="https://example.com/a", tenant=tenant)
    assert len(calls) == 1

    # Pedir bounds ahora es un miss de bounds (no de imagen): recaptura una vez.
    from noticia_carrusel.web_capture.models import CaptureConfig

    cfg = CaptureConfig(url="https://example.com/a")
    path, bounds = web_capture_api._capture_cached(
        cfg, tenant, force_capture=False, manager=None, bounds_selector="#grafico"
    )
    assert len(calls) == 2
    assert bounds is not None

    # Repetir con los mismos bounds_selector ahora sí pega en caché completa.
    path2, bounds2 = web_capture_api._capture_cached(
        cfg, tenant, force_capture=False, manager=None, bounds_selector="#grafico"
    )
    assert len(calls) == 2
    assert path2 == path
    assert bounds2 == bounds
