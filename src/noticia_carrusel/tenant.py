from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TENANTS_DIR = PROJECT_ROOT / "tenants"
TENANT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CONTENT_SLUG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_[a-z0-9][a-z0-9-]*$")
POST_TEMPLATES = frozenset(
    {
        "post_noticia",
        "post_analisis",
        "post_lista_top",
        "post_tutorial",
        "post_lanzamiento",
        "carousel_noticia",
        "story_teaser",
    }
)


class BrandManifest(BaseModel):
    logo: str
    default_theme: str = "theme_default"


class InstagramManifest(BaseModel):
    handle: str


class SocialManifest(BaseModel):
    instagram: InstagramManifest


class PublishManifest(BaseModel):
    namespace: str


class ContentManifest(BaseModel):
    """Preferencias editoriales del tenant."""

    default_post_template: str = "post_noticia"

    @field_validator("default_post_template")
    @classmethod
    def _known_template(cls, value: str) -> str:
        if value not in POST_TEMPLATES:
            known = ", ".join(sorted(POST_TEMPLATES))
            raise ValueError(f"Template desconocido '{value}'; disponibles: {known}")
        return value


class TenantManifest(BaseModel):
    id: str
    name: str
    brand: BrandManifest
    social: SocialManifest
    publish: PublishManifest
    content: ContentManifest = Field(default_factory=ContentManifest)


def _dotenv_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class TenantContext:
    id: str
    root: Path
    manifest: TenantManifest
    project_root: Path = PROJECT_ROOT

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def shared_assets_dir(self) -> Path:
        return self.project_root / "assets"

    @property
    def configs_dir(self) -> Path:
        return self.root / "configs"

    @property
    def videos_dir(self) -> Path:
        return self.root / "videos"

    @property
    def media_dir(self) -> Path:
        return self.root / "media"

    @property
    def output_dir(self) -> Path:
        return self.root / "output"

    @property
    def content_dir(self) -> Path:
        return self.root / "content"

    @property
    def media_videos_dir(self) -> Path:
        return self.media_dir / "videos"

    @property
    def env_path(self) -> Path:
        return self.root / ".env"

    def resolve_inside(self, base: Path, relative: str | Path) -> Path:
        value = Path(relative)
        target = value.resolve() if value.is_absolute() else (base / value).resolve()
        resolved_base = base.resolve()
        if not _is_within(target, resolved_base):
            raise ValueError(f"Ruta fuera del tenant '{self.id}': {relative}")
        return target

    def config_path(self, kind: str, value: str | Path) -> Path:
        if kind not in {"images", "videos"}:
            raise ValueError(f"Tipo de configuración inválido: {kind}")
        path = self.resolve_inside(self.configs_dir / kind, value)
        if not path.is_file():
            raise FileNotFoundError(f"No existe la configuración del tenant: {path}")
        return path

    def resolve_asset(self, relative: str | Path) -> Path:
        value = Path(relative)
        if value.is_absolute() or ".." in value.parts:
            raise ValueError(f"Asset debe ser relativo y sin '..': {relative}")
        tenant_asset = (self.assets_dir / value).resolve()
        shared_asset = (self.shared_assets_dir / value).resolve()
        if tenant_asset.is_file():
            return tenant_asset
        if shared_asset.is_file():
            return shared_asset
        raise FileNotFoundError(
            f"Asset no encontrado; tenant={tenant_asset}, shared={shared_asset}"
        )

    def output_path(self, relative: str | Path) -> Path:
        return self.resolve_inside(self.output_dir, relative)

    def media_path(self, relative: str | Path) -> Path:
        return self.resolve_inside(self.media_dir, relative)

    def content_path(self, slug: str, *relative: str | Path) -> Path:
        if not CONTENT_SLUG_RE.fullmatch(slug):
            raise ValueError(
                f"Slug de contenido inválido: {slug!r}; "
                "formato esperado YYYY-MM-DD_tema-en-kebab-case"
            )
        base = self.resolve_inside(self.content_dir, slug)
        if not relative:
            return base
        return self.resolve_inside(base, Path(*[str(part) for part in relative]))


def list_tenants() -> list[str]:
    """IDs de tenants válidos: subdirectorios de tenants/ con tenant.yaml."""
    if not TENANTS_DIR.is_dir():
        return []
    ids = []
    for entry in sorted(TENANTS_DIR.iterdir()):
        if (
            entry.is_dir()
            and TENANT_ID_RE.fullmatch(entry.name)
            and (entry / "tenant.yaml").is_file()
        ):
            ids.append(entry.name)
    return ids


def _read_manifest(path: Path) -> TenantManifest:
    if not path.is_file():
        raise FileNotFoundError(f"Falta manifest del tenant: {path}")
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Manifest YAML inválido: {path}") from exc
    return TenantManifest.model_validate(raw)


def load_tenant(tenant_id: str | None = None, *, load_env: bool = True) -> TenantContext:
    shared_values = _dotenv_values(PROJECT_ROOT / ".env")
    selected = (
        tenant_id
        or os.environ.get("TENANT")
        or os.environ.get("DEFAULT_TENANT")
        or shared_values.get("DEFAULT_TENANT")
    )
    if not selected:
        raise ValueError("Falta --tenant, TENANT o DEFAULT_TENANT")
    if not TENANT_ID_RE.fullmatch(selected):
        raise ValueError(f"ID de tenant inválido: {selected!r}")

    tenant_root = (TENANTS_DIR / selected).resolve()
    if not _is_within(tenant_root, TENANTS_DIR.resolve()):
        raise ValueError(f"Tenant fuera de tenants/: {selected!r}")
    if not tenant_root.is_dir():
        raise FileNotFoundError(f"No existe el tenant: {tenant_root}")

    manifest = _read_manifest(tenant_root / "tenant.yaml")
    if manifest.id != selected:
        raise ValueError(
            f"tenant.yaml declara id={manifest.id!r}, esperado {selected!r}"
        )
    context = TenantContext(selected, tenant_root, manifest)

    if load_env:
        exported = set(os.environ)
        for key, value in shared_values.items():
            if key not in exported:
                os.environ[key] = value
        for key, value in _dotenv_values(context.env_path).items():
            if key not in exported:
                os.environ[key] = value
        os.environ["TENANT"] = selected
    return context
