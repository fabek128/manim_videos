#!/usr/bin/env python3
"""Diagnóstico de entorno portable para redes2.

Verifica que el entorno local tenga lo necesario para ejecutar los flujos
del proyecto: Python, dependencias Python, herramientas externas, Chromium
de Playwright, tenant activo, variables de entorno y assets del tenant.

Uso:
    python scripts/doctor.py                 # diagnostico completo, tenant por defecto
    python scripts/doctor.py --tenant agente32
    python scripts/doctor.py --flow publish  # validacion de publicacion

Exit code:
    0  si el flujo solicitado puede ejecutarse.
    1  si falta algo bloqueante para el flujo solicitado.

Solo reportado como warning (no bloqueante):
    - funciones opcionales sin configurar (PromptGate, OpenRouter, vision);
    - herramientas para flujos especificos que no fueron pedidos.

Opciones:
    --flow {all,images,video,web,publish}  validar solo las herramientas
        requeridas por ese flujo (por defecto: all).
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

BLOCKER = "BLOCKER"
WARNING = "warning"
OK = "ok"


def _python_issues() -> list[tuple[str, str]]:
    """(severity, message) para el interprete y las dependencias Python."""
    issues: list[tuple[str, str]] = []
    version_info = sys.version_info
    if version_info < (3, 12):
        issues.append((BLOCKER, f"Python {version_info.major}.{version_info.minor} < 3.12 (requerido >=3.12)"))
    else:
        issues.append((OK, f"Python {version_info.major}.{version_info.minor}.{version_info.micro}"))
    return issues


def _python_modules(required: list[str]) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    for module in required:
        try:
            importlib.import_module(module)
            issues.append((OK, f"import {module}"))
        except Exception as exc:  # noqa: BLE001
            issues.append((BLOCKER, f"no se puede importar {module}: {exc}"))
    return issues


def _binaries(required: list[str]) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    for binary in required:
        found = shutil.which(binary)
        if found:
            issues.append((OK, f"{binary} en PATH: {found}"))
        else:
            issues.append((BLOCKER, f"{binary} no esta en PATH (instalar el paquete del sistema)"))
    return issues


def _playwright_chromium() -> tuple[str, str]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        return BLOCKER, f"playwright no instalado: {exc}"
    try:
        with sync_playwright() as p:
            path = p.chromium.executable_path
    except Exception as exc:  # noqa: BLE001
        return BLOCKER, f"no se pudo inicializar Playwright: {exc}"
    if path and Path(path).is_file():
        return OK, f"Chromium de Playwright instalado: {path}"
    return BLOCKER, f"Chromium de Playwright no instalado: {path} (ejecutar: playwright install chromium)"


def _tenant_issues(tenant_id: str | None) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    selected = (
        tenant_id
        or os.environ.get("TENANT")
        or os.environ.get("DEFAULT_TENANT")
    )
    if not selected:
        issues.append((BLOCKER, "falta --tenant, TENANT o DEFAULT_TENANT"))
        return issues
    issues.append((OK, f"tenant seleccionado: {selected}"))
    tenant_root = ROOT / "tenants" / selected
    if not (tenant_root / "tenant.yaml").is_file():
        issues.append((BLOCKER, f"no existe tenants/{selected}/tenant.yaml"))
        return issues
    try:
        from noticia_carrusel.tenant import load_tenant

        tenant = load_tenant(selected, load_env=False) or load_tenant(selected)
        issues.append((OK, f"tenant cargado: {tenant.id}"))
    except Exception as exc:  # noqa: BLE001
        issues.append((BLOCKER, f"no se pudo cargar el tenant: {exc}"))
        return issues

    # Fonts y assets declarados por el tenant
    try:
        from noticia_carrusel.backgrounds import available_backgrounds

        backgrounds = available_backgrounds(tenant)
        issues.append((OK if backgrounds else WARNING, f"backgrounds disponibles: {len(backgrounds)}"))
    except Exception as exc:  # noqa: BLE001
        issues.append((BLOCKER, f"error listando backgrounds: {exc}"))
    return issues


def _env_issues(check_publish: bool, check_promptgate: bool) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    dotenv = ROOT / ".env"
    if not dotenv.is_file():
        issues.append((WARNING, ".env no existe; copiar desde .env.example"))
    if check_publish:
        value = os.environ.get("FINAL_OUTPUT_DIR")
        if not value:
            issues.append(
                (BLOCKER, "publication: falta FINAL_OUTPUT_DIR (requerido para scripts/publish_final.py)")
            )
        elif not Path(value).expanduser().is_absolute():
            issues.append((BLOCKER, f"publication: FINAL_OUTPUT_DIR no es absolute: {value}"))
        else:
            issues.append((OK, f"publication: FINAL_OUTPUT_DIR={value}"))
    if check_promptgate:
        url = os.environ.get("PROMPTGATE_BASE_URL", "").strip()
        if not url:
            issues.append((WARNING, "promptgate: falta PROMPTGATE_BASE_URL; textos IA deshabilitados"))
        elif not url.startswith(("http://", "https://")):
            issues.append((BLOCKER, f"promptgate: PROMPTGATE_BASE_URL debe usar http:// o https://: {url}"))
        else:
            issues.append((OK, f"promptgate: PROMPTGATE_BASE_URL={url}"))
        model = os.environ.get("PROMPTGATE_MODEL", "").strip()
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not model and not key:
            issues.append(
                (WARNING, "image AI: falta PROMPTGATE_MODEL y OPENROUTER_API_KEY; generacion IA deshabilitada")
            )
    return issues


def _severity_weight(severity: str) -> int:
    return {OK: 0, WARNING: 1, BLOCKER: 2}[severity]


def run_doctor(
    tenant: str | None,
    flows: list[str],
) -> list[tuple[str, str]]:
    flows = flows or ["images", "video", "web", "publish", "promptgate"]
    check_publish = "publish" in flows
    check_promptgate = "promptgate" in flows
    results: list[tuple[str, str]] = []
    results.extend(_python_issues())
    results.extend(_python_modules(["manim", "PIL", "cv2", "pydantic", "yaml", "requests", "playwright"]))
    try:
        importlib.import_module("cairosvg")
        results.append((OK, "import cairosvg"))
    except Exception:  # noqa: BLE001
        results.append(
            (
                WARNING,
                "cairosvg no disponible (solo necesario para logos SVG en "
                "placas/carruseles). Instalar con: uv sync --group svg",
            )
        )
    binaries: list[str] = []
    if "video" in flows:
        binaries.extend(["manim", "ffmpeg", "ffprobe"])
    if binaries:
        results.extend(_binaries(binaries))
    if "web" in flows:
        results.append(_playwright_chromium())
    if "ink" in flows:
        results.extend(_binaries(["inkscape"]))
    results.extend(_tenant_issues(tenant))
    results.extend(_env_issues(check_publish, check_promptgate))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnostico de entorno portable para redes2")
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    parser.add_argument(
        "--flow",
        choices=["all", "images", "video", "web", "publish", "promptgate", "ink"],
        nargs="+",
        default=["all"],
        help="Validar solo las herramientas de estos flujos (default: all)",
    )
    return parser.parse_args()


def main() -> int:  # noqa: PLR0911
    args = parse_args()
    selected = args.tenant or os.environ.get("TENANT") or os.environ.get("DEFAULT_TENANT")
    flows = ["images", "video", "web", "publish", "promptgate", "ink"] if "all" in args.flow else args.flow
    results = run_doctor(selected, flows)
    print("Diagnostico de entorno redes2:")
    max_severity = max((_severity_weight(sev) for sev, _ in results), default=0)
    for severity, message in sorted(results, key=lambda item: _severity_weight(item[0]), reverse=True):
        prefix = {"ok": "  OK ", WARNING: " warn", BLOCKER: " FAIL"}[severity]
        print(f"{prefix} {message}")
    blockers = [msg for sev, msg in results if sev == BLOCKER]
    warnings = [msg for sev, msg in results if sev == WARNING]
    print(f"\n{len(blockers)} bloqueo(s), {len(warnings)} warning(s)")
    return 1 if max_severity >= _severity_weight(BLOCKER) else 0


if __name__ == "__main__":
    raise SystemExit(main())