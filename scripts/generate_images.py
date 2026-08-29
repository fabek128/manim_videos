#!/usr/bin/env python3
"""CLI para generar placas y carruseles de imágenes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from noticia_carrusel.config import load_config  # noqa: E402
from noticia_carrusel.generator import generate, intermediate_images  # noqa: E402
from noticia_carrusel.providers import ImageProviderError  # noqa: E402
from noticia_carrusel.tenant import list_tenants, load_tenant  # noqa: E402

QUALITY_CHOICES = ("draft", "low", "medium", "high")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generador multi-tenant de imágenes")
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    parser.add_argument(
        "--list-tenants", action="store_true", help="Listar tenants disponibles y salir"
    )
    subparsers = parser.add_subparsers(dest="command", required=False)
    post = subparsers.add_parser("post", help="Generar una placa individual")
    carousel = subparsers.add_parser("carousel", help="Generar un carrusel")
    for subparser in (post, carousel):
        subparser.add_argument(
            "--config",
            required=True,
            help="Path relativo dentro de configs/images del tenant",
        )
        subparser.add_argument(
            "--quality",
            choices=QUALITY_CHOICES,
            default="draft",
            help="Calidad de la imagen generada por IA (default: draft)",
        )
        subparser.add_argument(
            "--check-intermediate",
            action="store_true",
            help="Listar imágenes base ya generadas (intermediate/) y salir, sin generar ni llamar a ninguna API",
        )
        subparser.add_argument(
            "--reuse-intermediate",
            action="store_true",
            help="Reusar las imágenes base ya generadas en intermediate/ en vez de volver a llamar a la IA",
        )

    args = parser.parse_args()

    if args.list_tenants:
        for tenant_id in list_tenants():
            print(tenant_id)
        return 0

    if not args.command:
        parser.error("se requiere un subcomando: post o carousel")

    try:
        tenant = load_tenant(args.tenant)
        config_path = tenant.config_path("images", args.config)
        config = load_config(config_path)
        if args.command == "carousel" and not config.format.startswith("carousel_"):
            raise ValueError("carousel requiere format=carousel_square o carousel_vertical")
        if args.command == "post" and config.format.startswith("carousel_"):
            raise ValueError("post requiere un formato individual: post_square, post_vertical o story")

        if args.check_intermediate:
            existing = intermediate_images(config, tenant)
            if not existing:
                print("No hay imágenes base generadas en intermediate/ para esta config.")
                return 0
            print(f"{len(existing)} imagen(es) base ya generada(s) en intermediate/:")
            for path in existing:
                print(path)
            return 0

        result = generate(
            config, tenant, quality=args.quality, reuse_intermediate=args.reuse_intermediate
        )
    except (FileNotFoundError, ValueError, OSError, ImageProviderError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    for path in result.paths:
        print(path)
    if result.reused_paths:
        print(f"Reusó {len(result.reused_paths)} imagen(es) base existente(s) (sin costo, sin llamar a la IA)")
    if result.cost_entries:
        print(
            f"Costo de esta generación: ${result.run_cost_usd:.4f} USD "
            f"({len(result.cost_entries)} imagen(es) por IA)"
        )
        print(f"Costo acumulado del proyecto: ${result.total_cost_usd:.4f} USD")
        print(f"Resumen: {result.resumen_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
