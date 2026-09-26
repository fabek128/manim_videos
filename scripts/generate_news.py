#!/usr/bin/env python3
"""Generador de noticias por niveles de investigación y carga de IA.

Nivel 1 (URL):
    python scripts/generate_news.py --level 1 --url <URL> --format short

Nivel 2/3 (tema):
    python scripts/generate_news.py --level 2 --topic "nuevo modelo de IA"
    python scripts/generate_news.py --level 2 --topic "nuevo modelo de IA" --select 1 --format carousel3

En nivel 2/3, la primera invocación sin `--select` devuelve un informe con
opciones. No genera piezas hasta que el usuario elige un ángulo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from noticia_carrusel.news_generator import (  # noqa: E402
    NewsGeneratorError,
    create_project,
)
from noticia_carrusel.tenant import load_tenant  # noqa: E402

FORMATS = ("short", "long", "carousel3", "carousel5", "story", "story_complete")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Investiga y genera noticias con niveles 1 (URL), 2 (búsqueda) y 3 (investigación profunda)"
    )
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    parser.add_argument("--level", type=int, choices=(1, 2, 3), required=True, help="Carga: 1 URL única, 2 búsqueda, 3 investigación profunda")
    parser.add_argument("--url", help="Nivel 1: URL única; opcional en nivel 2/3 como fuente primaria semilla")
    parser.add_argument("--topic", help="Nivel 2/3: tema a investigar")
    parser.add_argument("--select", type=int, help="Nivel 2/3: id de opción editorial elegida")
    parser.add_argument("--format", choices=FORMATS, default=None, help="Formato visual; en modo interactivo se pregunta; default: short")
    parser.add_argument("--visual", choices=("screenshot", "solid"), default=None, help="Fondo; en modo interactivo se pregunta; default: screenshot")
    parser.add_argument("--logo-ref", action="append", default=[], help="Asset de logo real relativo a assets/; repetir para varios logos")
    parser.add_argument("--non-interactive", action="store_true", help="No preguntar: sin select en nivel 2/3 solo escribe informe")
    return parser.parse_args()


def _show_file(path: Path) -> None:
    print(f"\nInforme: {path}")
    print(path.read_text(encoding="utf-8"))


def _prompt_int(question: str) -> int:
    while True:
        try:
            return int(input(question).strip())
        except ValueError:
            print("Ingresá un número de opción válido.")


def main() -> int:
    args = parse_args()
    try:
        tenant = load_tenant(args.tenant)
        format_name = args.format or ("short" if args.level == 1 else None)
        visual = args.visual or "screenshot"
        if args.level in {2, 3} and args.select is None:
            # Primera etapa obligatoria: investigar y entregar informe antes
            # de pedir una decisión editorial.
            project, _ = create_project(
                tenant=tenant,
                level=args.level,
                url=args.url,
                topic=args.topic,
                format_name="short",
                visual=visual,
                select=None,
                explicit_logos=args.logo_ref,
            )
            _show_file(project / "informe.md")
            if args.non_interactive or not sys.stdin.isatty():
                print("\nNo se generaron piezas. Elegí una opción con --select N y un --format explícito o ejecutá en una terminal interactiva.")
                return 0
            args.select = _prompt_int("\nElegí el ángulo (id): ")
            format_name = input(
                f"Formato [{', '.join(FORMATS)}] (default carousel3): "
            ).strip() or "carousel3"
            if format_name not in FORMATS:
                raise ValueError(f"Formato desconocido: {format_name}")
            visual = input(
                "Fondo [screenshot|solid] (default screenshot): "
            ).strip() or "screenshot"
            if visual not in {"screenshot", "solid"}:
                raise ValueError(f"Fondo desconocido: {visual}")
        project, config_path = create_project(
            tenant=tenant,
            level=args.level,
            url=args.url,
            topic=args.topic,
            format_name=format_name or "short",
            visual=visual,
            select=args.select,
            explicit_logos=args.logo_ref,
        )
    except (NewsGeneratorError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if config_path is None:
        print(f"Proyecto creado con informe, sin piezas: {project}")
        return 0
    print(f"\nProyecto: {project}")
    print(f"Config: {config_path}")
    for path in sorted(project.rglob("*.png")):
        print(f"Render: {path}")
    print(f"Post: {project / 'post.txt'}")
    print(f"Vision review: {project / 'vision_review.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
