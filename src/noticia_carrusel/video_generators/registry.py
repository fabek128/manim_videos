from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from noticia_carrusel.tenant import TenantContext

GENERATORS_ROOT = Path(__file__).resolve().parents[3] / "generators" / "videos"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CLASS_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class GeneratorDescriptor(BaseModel):
    id: str
    aliases: list[str] = Field(default_factory=list)
    engine: Literal["manim", "web"] = "manim"
    entrypoint: str
    scene_class: str
    config_subdir: str

    @field_validator("id")
    @classmethod
    def _valid_id(cls, v: str) -> str:
        if not ID_RE.fullmatch(v):
            raise ValueError(f"id inválido: {v!r}")
        return v

    @field_validator("aliases")
    @classmethod
    def _valid_aliases(cls, v: list[str]) -> list[str]:
        for alias in v:
            if not ID_RE.fullmatch(alias):
                raise ValueError(f"alias inválido: {alias!r}")
        if len(v) != len(set(v)):
            raise ValueError("aliases duplicados")
        return v

    @field_validator("entrypoint", "config_subdir")
    @classmethod
    def _relative_no_traversal(cls, v: str) -> str:
        p = Path(v)
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(f"path debe ser relativo sin '..': {v!r}")
        if not v.strip():
            raise ValueError("path no puede estar vacío")
        return v

    @field_validator("scene_class")
    @classmethod
    def _valid_class(cls, v: str) -> str:
        if not CLASS_RE.fullmatch(v):
            raise ValueError(f"scene_class inválido: {v!r}")
        return v


@dataclass(frozen=True)
class VideoGenerator:
    id: str
    aliases: tuple[str, ...]
    engine: str
    entrypoint: Path
    scene_class: str
    config_dir: Path
    descriptor_path: Path
    implementation_source: Literal["global", "tenant_override"] = "global"


def discover_global_generators(root: Path | None = None) -> dict[str, VideoGenerator]:
    base = (root or GENERATORS_ROOT).resolve()
    if not base.is_dir():
        return {}
    by_id: dict[str, VideoGenerator] = {}
    by_alias: dict[str, str] = {}
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        descriptor_path = entry / "generator.yaml"
        if not descriptor_path.is_file():
            continue
        try:
            raw = yaml.safe_load(descriptor_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML inválido {descriptor_path}: {exc}") from exc
        desc = GeneratorDescriptor.model_validate(raw)
        entrypoint = (entry / desc.entrypoint).resolve()
        if not entrypoint.is_file():
            raise FileNotFoundError(f"entrypoint no existe: {entrypoint}")
        # Detectar colisiones de id/alias
        if desc.id in by_id:
            raise ValueError(f"id duplicado: {desc.id!r}")
        for alias in desc.aliases:
            if alias in by_alias or alias in by_id:
                raise ValueError(f"alias duplicado: {alias!r} (id={desc.id})")
            by_alias[alias] = desc.id
        # config_dir es tenant.configs_dir / videos / config_subdir (se resuelve por tenant)
        # Guardamos solo el subdir relativo para resolver después
        gen = VideoGenerator(
            id=desc.id,
            aliases=tuple(desc.aliases),
            engine=desc.engine,
            entrypoint=entrypoint,
            scene_class=desc.scene_class,
            config_dir=Path(desc.config_subdir),  # relativo, se expande con tenant
            descriptor_path=descriptor_path,
            implementation_source="global",
        )
        by_id[desc.id] = gen
    return by_id


def _tenant_override_path(tenant: TenantContext, generator: VideoGenerator) -> Path | None:
    # Convención: tenants/<id>/overrides/videos/<generator.id>/scene.py
    candidate = tenant.root / "overrides" / "videos" / generator.id / "scene.py"
    if candidate.is_file():
        # Validar confinamiento
        try:
            candidate.resolve().relative_to(tenant.root.resolve())
        except ValueError:
            raise ValueError(f"override fuera del tenant: {candidate}")
        return candidate.resolve()
    return None


def resolve_generator(tenant: TenantContext, name: str, *, root: Path | None = None) -> VideoGenerator:
    """Resuelve un generador por id o alias, considerando override del tenant."""
    normalized = name.strip().lower()
    # Normalizar removiendo acentos y separadores? Reutilizar lógica fuzzy mínima
    # Para registry usamos match exacto lower; build.py hará fuzzy adicional
    by_id = discover_global_generators(root)
    # Mapa alias -> id
    alias_map: dict[str, str] = {}
    for gen in by_id.values():
        alias_map[gen.id.lower()] = gen.id
        for alias in gen.aliases:
            alias_map[alias.lower()] = gen.id
    target_id = alias_map.get(normalized)
    if target_id is None:
        # Intentar sin guiones/espacios
        compact = re.sub(r"[^a-z0-9]", "", normalized)
        for key, gid in alias_map.items():
            if re.sub(r"[^a-z0-9]", "", key) == compact:
                target_id = gid
                break
    if target_id is None:
        raise FileNotFoundError(f"Generador no encontrado: {name!r}")
    gen = by_id[target_id]
    override = _tenant_override_path(tenant, gen)
    if override:
        return VideoGenerator(
            id=gen.id,
            aliases=gen.aliases,
            engine=gen.engine,
            entrypoint=override,
            scene_class=gen.scene_class,
            config_dir=gen.config_dir,
            descriptor_path=gen.descriptor_path,
            implementation_source="tenant_override",
        )
    return gen


def resolve_video_config(tenant: TenantContext, generator: VideoGenerator, value: str | None) -> Path:
    """Resuelve un config dentro del tenant para un generador.

    Si ``value`` es None, elige el JSON más reciente alfabéticamente (YYYY-MM-DD_...).
    Valida confinamiento y existencia.
    """
    base = tenant.configs_dir / "videos" / generator.config_dir
    # Permitir que base no exista -> error claro
    if value:
        # value debe ser relativo sin traversal
        p = Path(value)
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(f"config debe ser relativo sin '..': {value!r}")
        # Permitir tanto solo nombre como subpath dentro del config_subdir
        target = tenant.resolve_inside(base, p)
        if not target.is_file():
            raise FileNotFoundError(f"No existe el config: {target}")
        return target.resolve()
    # Más reciente
    if not base.is_dir():
        raise FileNotFoundError(f"No hay configs para {generator.id} en {base}")
    candidates = sorted(base.glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"No hay JSONs en {base}")
    return candidates[-1].resolve()

