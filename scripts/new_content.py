#!/usr/bin/env python3
"""Crea el andamiaje de un proyecto de contenido: brief, caption, assets.

Ejemplos:
    python scripts/new_content.py --slug nvidia-huggingface \
        --tema "Compra de Hugging Face por Nvidia"
    python scripts/new_content.py --tenant agente32 \
        --slug nvidia-huggingface --tema "..." --force
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from noticia_carrusel.tenant import load_tenant  # noqa: E402

BRIEF_TEMPLATE = """\
# Brief: {tema}

- **Fecha de creación**: {fecha}
- **Tenant**: {tenant_id}
- **Estado**: sin_investigar

## Confirmado

- (sin datos aún)

## Sin confirmar

- (sin datos aún)

## Contradicciones entre fuentes

- (ninguna detectada aún)

## Por qué importa

- (completar tras la investigación)

## Fuentes

| URL | Medio | Fecha | Tipo |
|---|---|---|---|
| | | | primaria / secundaria |

## No encontrado

- (qué se buscó y no apareció)
"""

CAPTION_TEMPLATE = """\
# Caption: {tema}

- **Template usado**: (post_noticia / post_analisis / post_lista_top / ...)
- **Red**: instagram
- **Estado**: borrador

## Texto

(pendiente — generar con `scripts/generate_caption.py` o redactar a mano
siguiendo `templates/posts/`)
"""


def _slugify_check(slug: str) -> str:
    import re

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise ValueError(
            f"Slug inválido: {slug!r}; usar minúsculas, dígitos y guiones"
        )
    return slug


def create_content_project(
    tenant_id: str | None,
    slug: str,
    tema: str,
    fecha: str | None,
    force: bool,
) -> Path:
    tenant = load_tenant(tenant_id)
    _slugify_check(slug)
    fecha = fecha or dt.date.today().isoformat()
    try:
        dt.date.fromisoformat(fecha)
    except ValueError as exc:
        raise ValueError(f"--date debe ser YYYY-MM-DD: {fecha!r}") from exc

    full_slug = f"{fecha}_{slug}"
    project_dir = tenant.content_path(full_slug)

    if project_dir.exists() and not force:
        raise FileExistsError(
            f"Ya existe el proyecto de contenido: {project_dir}; usa --force"
        )

    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "assets").mkdir(exist_ok=True)

    brief_path = project_dir / "brief.md"
    caption_path = project_dir / "caption.md"
    brief_path.write_text(
        BRIEF_TEMPLATE.format(tema=tema, fecha=fecha, tenant_id=tenant.id),
        encoding="utf-8",
    )
    caption_path.write_text(CAPTION_TEMPLATE.format(tema=tema), encoding="utf-8")

    return project_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crea el andamiaje de un proyecto de contenido (brief + caption + assets)"
    )
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    parser.add_argument("--slug", required=True, help="Slug en kebab-case, sin fecha")
    parser.add_argument("--tema", required=True, help="Descripción corta del tema")
    parser.add_argument("--date", help="Fecha YYYY-MM-DD; default hoy")
    parser.add_argument("--force", action="store_true", help="Reescribir si ya existe")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_dir = create_content_project(
            args.tenant, args.slug, args.tema, args.date, args.force
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(project_dir)
    print(project_dir / "brief.md")
    print(project_dir / "caption.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
