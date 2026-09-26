from __future__ import annotations

from pathlib import Path

from PIL import Image

from noticia_carrusel.backgrounds import available_backgrounds, select_background, select_for_slide
from noticia_carrusel.generator import _base_image
from noticia_carrusel.models import AppConfig, BrandConfig, FontsConfig, SlideConfig
from noticia_carrusel.tenant import (
    BrandManifest,
    InstagramManifest,
    PublishManifest,
    SocialManifest,
    TenantContext,
    TenantManifest,
)


def _tenant(tmp_path: Path) -> TenantContext:
    root = tmp_path / "tenant"
    (root / "assets" / "backgrounds").mkdir(parents=True)
    (root / "assets" / "explicit").mkdir(parents=True)
    manifest = TenantManifest(
        id="testtenant",
        name="Test Tenant",
        brand=BrandManifest(logo="logos/agente32/agente32.svg"),
        social=SocialManifest(instagram=InstagramManifest(handle="test")),
        publish=PublishManifest(namespace="test"),
    )
    return TenantContext(id="testtenant", root=root, manifest=manifest)


def _config(mode: str = "pool") -> AppConfig:
    return AppConfig(
        project_name="demo",
        output_dir="demo",
        format="post_vertical",
        title="Demo",
        background_mode=mode,
        brand=BrandConfig(name="Test", logo_path="logo.svg"),
        fonts=FontsConfig(title="title.ttf", body="body.ttf"),
    )


def test_available_backgrounds_ignores_metadata_files(tmp_path):
    tenant = _tenant(tmp_path)
    bg_dir = tenant.assets_dir / "backgrounds"
    Image.new("RGB", (10, 10), "blue").save(bg_dir / "z.png")
    Image.new("RGB", (10, 10), "red").save(bg_dir / "a.jpg")
    (bg_dir / "manifest.json").write_text("{}")
    assert [p.name for p in available_backgrounds(tenant)] == ["a.jpg", "z.png"]


def test_select_background_is_deterministic(tmp_path):
    tenant = _tenant(tmp_path)
    bg_dir = tenant.assets_dir / "backgrounds"
    for name in ("one.png", "two.png", "three.png"):
        Image.new("RGB", (10, 10), "blue").save(bg_dir / name)
    assert select_background(tenant, "same-key") == select_background(tenant, "same-key")
    assert select_for_slide(tenant, "demo", 1, "title") == select_for_slide(tenant, "demo", 1, "title")


def test_select_background_returns_none_when_pool_is_empty(tmp_path):
    tenant = _tenant(tmp_path)
    assert select_background(tenant, "key") is None


def test_base_image_uses_pool_when_no_background_is_declared(tmp_path):
    tenant = _tenant(tmp_path)
    bg = tenant.assets_dir / "backgrounds" / "bg.png"
    Image.new("RGB", (20, 20), "blue").save(bg)
    path, result, reused = _base_image(_config(), SlideConfig(title="News"), tenant, tenant.output_dir / "demo", 1)
    assert path == bg
    assert result is None
    assert reused is False


def test_base_image_solid_mode_preserves_renderer_fallback(tmp_path):
    tenant = _tenant(tmp_path)
    Image.new("RGB", (20, 20), "blue").save(tenant.assets_dir / "backgrounds" / "bg.png")
    path, result, reused = _base_image(_config("solid"), SlideConfig(title="News"), tenant, tenant.output_dir / "demo", 1)
    assert path is None
    assert result is None
    assert reused is False


def test_explicit_asset_has_priority_over_pool(tmp_path):
    tenant = _tenant(tmp_path)
    explicit = tenant.assets_dir / "explicit" / "source.png"
    pool = tenant.assets_dir / "backgrounds" / "pool.png"
    Image.new("RGB", (20, 20), "red").save(explicit)
    Image.new("RGB", (20, 20), "blue").save(pool)
    config = _config()
    config = config.model_copy(update={"background_image_path": "explicit/source.png"})
    path, _, _ = _base_image(config, SlideConfig(title="News"), tenant, tenant.output_dir / "demo", 1)
    assert path == explicit
