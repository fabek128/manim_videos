#!/usr/bin/env python3
"""Descarga y registra un logo para un tenant.

Valida Content-Type y tamaño, guarda el archivo en
`tenants/<id>/assets/logos/<slug>/` junto a un README con el origen,
fecha y licencia declarada. Con `--for-manim`, además genera la versión
`<slug>_paths.svg` convertida a curvas (procedimiento de
`skills/global.md` §3), lista para `SVGMobject`.

Ejemplos:
    python scripts/fetch_logo.py --slug openai \
        --url https://example.com/openai.svg
    python scripts/fetch_logo.py --tenant agente32 --slug openai \
        --url https://example.com/openai.svg --for-manim \
        --license "Marca registrada de OpenAI, uso editorial"
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from noticia_carrusel.tenant import TenantContext, load_tenant  # noqa: E402

MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MiB, igual límite que otros descargadores del repo
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CONTENT_TYPE_EXT = {
    "image/svg+xml": ".svg",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}
INKSCAPE_CANDIDATES = (
    "inkscape",
    "/Applications/Inkscape.app/Contents/MacOS/inkscape",
)


class FetchLogoError(Exception):
    pass


def _download(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "redes2-fetch-logo/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if content_type not in CONTENT_TYPE_EXT:
                raise FetchLogoError(
                    f"Content-Type no soportado: {content_type or '(vacío)'}; "
                    f"esperado uno de {sorted(CONTENT_TYPE_EXT)}"
                )
            data = response.read(MAX_LOGO_BYTES + 1)
            if len(data) > MAX_LOGO_BYTES:
                raise FetchLogoError(
                    f"El archivo supera el límite de {MAX_LOGO_BYTES // (1024 * 1024)} MiB"
                )
            if not data:
                raise FetchLogoError("La descarga devolvió 0 bytes")
            return data, CONTENT_TYPE_EXT[content_type]
    except HTTPError as exc:
        raise FetchLogoError(f"HTTP {exc.code} al descargar {url}") from exc
    except URLError as exc:
        raise FetchLogoError(f"No se pudo descargar {url}: {exc.reason}") from exc


def _find_inkscape() -> str | None:
    for candidate in INKSCAPE_CANDIDATES:
        found = shutil.which(candidate) if "/" not in candidate else (
            candidate if Path(candidate).is_file() else None
        )
        if found:
            return found
    return None


def _sanitize_for_manim(svg_text: str) -> str:
    """Aplica el saneo de `skills/global.md` §3 sobre un SVG ya convertido a curvas."""
    svg_text = re.sub(r'stroke\s*=\s*"currentColor"', 'stroke="none"', svg_text)
    svg_text = re.sub(r"fill\s*:\s*currentColor", "fill:#000000", svg_text)
    svg_text = re.sub(r'fill\s*=\s*"url\(#[^)]*\)"', 'fill="#000000"', svg_text)
    svg_text = re.sub(r"stroke\s*:\s*[^;\"']+;?", "stroke:none;", svg_text)
    svg_text = re.sub(r"stroke-width\s*:\s*[^;\"']+;?", "", svg_text)
    svg_text = re.sub(r"paint-order\s*:\s*[^;\"']+;?", "", svg_text)
    return svg_text


def _convert_to_paths(src_svg: Path, dest_svg: Path) -> None:
    inkscape = _find_inkscape()
    if not inkscape:
        raise FetchLogoError(
            "Inkscape no encontrado; instalar o convertir manualmente a curvas "
            "(ver skills/global.md §3) antes de usar --for-manim"
        )
    with tempfile.TemporaryDirectory() as tmp:
        raw_path = Path(tmp) / "raw_paths.svg"
        try:
            subprocess.run(
                [
                    inkscape,
                    "--export-type=svg",
                    "--export-text-to-path",
                    f"--export-filename={raw_path}",
                    str(src_svg),
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
            raise FetchLogoError(f"Inkscape falló al convertir a curvas: {stderr[:400]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise FetchLogoError("Inkscape no respondió dentro del tiempo límite") from exc
        if not raw_path.is_file():
            raise FetchLogoError("Inkscape no generó el archivo esperado")
        sanitized = _sanitize_for_manim(raw_path.read_text(encoding="utf-8"))
        dest_svg.write_text(sanitized, encoding="utf-8")


def fetch_logo(
    tenant: TenantContext,
    slug: str,
    url: str,
    license_note: str,
    for_manim: bool,
) -> list[Path]:
    if not SLUG_RE.fullmatch(slug):
        raise FetchLogoError(f"Slug inválido: {slug!r}; usar minúsculas, dígitos y guiones")

    data, ext = _download(url)

    logo_dir = tenant.resolve_inside(tenant.assets_dir / "logos", slug)
    logo_dir.mkdir(parents=True, exist_ok=True)

    dest = logo_dir / f"{slug}{ext}"
    dest.write_bytes(data)
    written = [dest]

    if for_manim:
        if ext != ".svg":
            raise FetchLogoError("--for-manim requiere un logo SVG (image/svg+xml)")
        paths_dest = logo_dir / f"{slug}_paths.svg"
        _convert_to_paths(dest, paths_dest)
        written.append(paths_dest)

    readme = logo_dir / "README.md"
    readme.write_text(
        f"# Logo: {slug}\n\n"
        f"- **Origen**: {url}\n"
        f"- **Descargado**: {dt.date.today().isoformat()}\n"
        f"- **Licencia declarada**: {license_note or 'sin declarar; verificar en la fuente antes de publicar'}\n"
        f"- **Archivo**: `{dest.name}`\n"
        + (f"- **Versión Manim (curvas)**: `{paths_dest.name}`\n" if for_manim else "")
        + "\nRegenerar con:\n\n"
        "```bash\n"
        f"python scripts/fetch_logo.py --tenant {tenant.id} --slug {slug} "
        f"--url {url}{' --for-manim' if for_manim else ''}\n"
        "```\n",
        encoding="utf-8",
    )
    written.append(readme)
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Descarga y registra un logo para un tenant")
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    parser.add_argument("--slug", required=True, help="Nombre del logo en kebab-case")
    parser.add_argument("--url", required=True, help="URL del SVG/PNG/JPG/WEBP de origen")
    parser.add_argument("--license", default="", help="Licencia declarada de la fuente")
    parser.add_argument(
        "--for-manim",
        action="store_true",
        help="Generar además <slug>_paths.svg convertido a curvas para Manim",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        tenant = load_tenant(args.tenant)
        paths = fetch_logo(tenant, args.slug, args.url, args.license, args.for_manim)
    except (FetchLogoError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
