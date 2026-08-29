#!/usr/bin/env python3
"""Inventario de proyectos de contenido y configs huérfanas.

Recorre `content/<slug>/` del tenant y reporta el estado de cada
proyecto (brief, caption, config asociada, renders). Cruza además los
YAML de `configs/images/` que declaran `content_slug` contra las
carpetas de `content/` existentes para detectar configs huérfanas.

Ejemplo:
    python scripts/content_status.py --tenant agente32
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from noticia_carrusel.config import load_raw_config  # noqa: E402
from noticia_carrusel.tenant import CONTENT_SLUG_RE, TenantContext, load_tenant  # noqa: E402

BRIEF_SOURCE_ROW_RE = re.compile(r"^\|\s*https?://", re.MULTILINE)
CAPTION_PLACEHOLDER = "(pendiente"


def _brief_summary(project_dir: Path) -> str:
    brief_path = project_dir / "brief.md"
    if not brief_path.is_file():
        return "FALTA brief.md"
    text = brief_path.read_text(encoding="utf-8")
    fuentes = len(BRIEF_SOURCE_ROW_RE.findall(text))
    if fuentes == 0:
        return "sin fuentes cargadas"
    return f"{fuentes} fuente(s)"


def _caption_summary(project_dir: Path) -> str:
    caption_path = project_dir / "caption.md"
    if not caption_path.is_file():
        return "FALTA caption.md"
    text = caption_path.read_text(encoding="utf-8").strip()
    if not text or CAPTION_PLACEHOLDER in text:
        return "borrador pendiente"
    return f"{len(text)} caracteres"


def _renders_summary(project_dir: Path) -> str:
    renders_dir = project_dir / "renders"
    if not renders_dir.is_dir():
        return "sin renders"
    pngs = sorted(renders_dir.glob("*.png"))
    if not pngs:
        return "sin renders"
    return f"{len(pngs)} PNG"


def _linked_configs(tenant: TenantContext, slug: str) -> list[Path]:
    matches = []
    images_dir = tenant.configs_dir / "images"
    if not images_dir.is_dir():
        return matches
    for path in sorted(images_dir.rglob("*")):
        if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        try:
            raw = load_raw_config(path)
        except (ValueError, FileNotFoundError):
            continue
        if raw.get("content_slug") == slug:
            matches.append(path)
    return matches


def _orphan_configs(tenant: TenantContext, known_slugs: set[str]) -> list[tuple[Path, str]]:
    orphans = []
    images_dir = tenant.configs_dir / "images"
    if not images_dir.is_dir():
        return orphans
    for path in sorted(images_dir.rglob("*")):
        if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        try:
            raw = load_raw_config(path)
        except (ValueError, FileNotFoundError):
            continue
        slug = raw.get("content_slug")
        if slug and slug not in known_slugs:
            orphans.append((path, slug))
    return orphans


def report(tenant: TenantContext) -> int:
    content_dir = tenant.content_dir
    if not content_dir.is_dir():
        print(f"[{tenant.id}] sin proyectos de contenido (no existe {content_dir})")
        return 0

    projects = sorted(
        p for p in content_dir.iterdir() if p.is_dir() and CONTENT_SLUG_RE.fullmatch(p.name)
    )
    if not projects:
        print(f"[{tenant.id}] sin proyectos de contenido")
        return 0

    known_slugs = {p.name for p in projects}
    print(f"[{tenant.id}] {len(projects)} proyecto(s) de contenido\n")
    for project_dir in projects:
        slug = project_dir.name
        configs = _linked_configs(tenant, slug)
        config_summary = (
            ", ".join(str(c.relative_to(tenant.root)) for c in configs)
            if configs
            else "sin config asociada"
        )
        print(f"{slug}")
        print(f"  brief:   {_brief_summary(project_dir)}")
        print(f"  caption: {_caption_summary(project_dir)}")
        print(f"  config:  {config_summary}")
        print(f"  renders: {_renders_summary(project_dir)}")

    orphans = _orphan_configs(tenant, known_slugs)
    if orphans:
        print("\nConfigs huérfanas (content_slug sin proyecto):")
        for path, slug in orphans:
            print(f"  {path.relative_to(tenant.root)} -> content_slug={slug!r}")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventario de proyectos de contenido")
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        tenant = load_tenant(args.tenant)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return report(tenant)


if __name__ == "__main__":
    raise SystemExit(main())
