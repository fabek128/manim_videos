#!/usr/bin/env python3
"""Publica archivos validados en la carpeta final compartida.

Este script no se ejecuta desde build.py. Solo copia archivos cuando el
usuario confirma explícitamente que el contenido está aprobado.

Multi-tenant: el namespace de publicación se aísla por tenant.

Ejemplos:
    python scripts/publish_final.py --video lostops
    python scripts/publish_final.py --type images --source media/images/post.png \\
        --date 2026-08-23 --slug modelos-semana
    python scripts/publish_final.py --video lostops --tenant agente32
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:_|$)")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

sys.path.insert(0, str(REPO_ROOT / "src"))

from noticia_carrusel.tenant import load_tenant, TenantContext  # noqa: E402


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _final_root(tenant: TenantContext) -> Path:
    """Raíz de publicación: FINAL_OUTPUT_DIR obligatorio (tenant manifest o entorno)."""
    value = os.environ.get("FINAL_OUTPUT_DIR")
    if value:
        root = Path(value).expanduser()
        if not root.is_absolute():
            raise ValueError("FINAL_OUTPUT_DIR debe ser una ruta absoluta")
        return root
    # Fallback portable: apuntar a un directorio dentro del repo para evitar
    # rutas personales, pero exigir FINAL_OUTPUT_DIR en publicación real.
    raise ValueError(
        "Falta FINAL_OUTPUT_DIR: definilo en .env o exportalo para publicar. "
        "Ejemplo: FINAL_OUTPUT_DIR=/ruta/absoluta/de/salida"
    )

def _validate_slug(value: str, label: str) -> str:
    if not SLUG_RE.fullmatch(value):
        raise ValueError(f"{label} inválido: solo se permiten letras, números, '.', '_' y '-'")
    return value


def _content_date(tenant: TenantContext, video: str, explicit: str | None) -> str:
    if explicit:
        if not DATE_RE.fullmatch(explicit):
            raise ValueError("--date debe tener formato YYYY-MM-DD")
        return explicit
    json_dir = tenant.videos_dir / video / "json"
    candidates = sorted(json_dir.glob("*.json"))
    if candidates:
        match = DATE_RE.match(candidates[-1].name)
        if match:
            return match.group(1)
    raise ValueError("No se pudo inferir la fecha; indica --date YYYY-MM-DD")


def _sources(tenant: TenantContext, args: argparse.Namespace) -> list[Path]:
    if args.video and args.source:
        raise ValueError("Usa --video o --source, no ambos")
    if not args.video and not args.source:
        raise ValueError("Debes indicar --video o al menos un --source")
    if args.video:
        video_dir = tenant.media_videos_dir / args.video
        paths = sorted(video_dir.glob("*.mp4"))
        if not paths:
            raise FileNotFoundError(f"No hay videos finales en {video_dir}")
        return paths
    return [Path(item).expanduser() for item in args.source]


def publish(args: argparse.Namespace, tenant: TenantContext) -> list[Path]:
    root = _final_root(tenant)
    slug = _validate_slug(args.slug or args.video or "contenido", "slug")
    content_date = (
        _content_date(tenant, args.video, args.date)
        if args.video
        else args.date
    )
    if not content_date:
        raise ValueError("Para imágenes debes indicar --date YYYY-MM-DD")
    if not DATE_RE.fullmatch(content_date):
        raise ValueError("--date debe tener formato YYYY-MM-DD")

    # `root` ya incluye el namespace del tenant por defecto
    # (`<FINAL_OUTPUT_DIR>/<namespace>`). El tipo decide el subdirectorio;
    # no repetir el namespace en la ruta final.
    content_type = "videos" if args.type == "videos" else "images"
    destination = root / content_type / f"{content_date}_{slug}"
    output_paths = []
    for source in _sources(tenant, args):
        source = source.resolve()
        if REPO_ROOT not in source.parents:
            raise ValueError(f"El source debe estar dentro del repositorio: {source}")
        if not source.is_file():
            raise FileNotFoundError(f"No existe el archivo: {source}")
        target = destination / source.name
        if target.exists() and not args.force:
            raise FileExistsError(f"Ya existe {target}; usa --force para reemplazarlo")
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        output_paths.append(target)
    return output_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copia contenido aprobado a FINAL_OUTPUT_DIR; nunca se ejecuta automáticamente."
    )
    parser.add_argument("--type", choices=("videos", "images"), default="videos")
    parser.add_argument("--video", help="Slug de media/videos/<slug> con los MP4 finales")
    parser.add_argument("--source", nargs="+", help="Uno o más archivos finales dentro del repo")
    parser.add_argument("--date", help="Fecha YYYY-MM-DD; se infiere desde el JSON de un video")
    parser.add_argument("--slug", help="Nombre del grupo de publicación")
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    parser.add_argument("--force", action="store_true", help="Reemplazar archivos existentes")
    return parser.parse_args()


def main() -> int:
    _load_dotenv(ENV_PATH)
    args = parse_args()
    try:
        tenant = load_tenant(args.tenant)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"⚠ Configuración de tenant omitida: {exc}", file=sys.stderr)
        tenant = None
    try:
        if tenant is None:
            # Fallback legacy sin tenant (rutas relativas al repo).
            outputs = publish(args, _make_legacy_tenant())
        else:
            outputs = publish(args, tenant)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    for output in outputs:
        print(output)
    return 0

def _make_legacy_tenant() -> TenantContext:
    """Tenant de respaldo que resuelve rutas relativas al repo raíz."""
    return TenantContext(
        id=os.environ.get("TENANT", "default"),
        root=REPO_ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
