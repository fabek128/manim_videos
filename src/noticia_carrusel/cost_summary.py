"""Registro de costos reales de generación de imágenes por IA.

Cada llamada a la API de un modelo de imagen que devuelva `usage.cost`
se acumula en un `resumen.md` junto al proyecto de contenido (o junto
al output, si la config no está vinculada a un proyecto). Nunca se
inventa un costo: si el proveedor no lo informó, no se registra.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

ROW_RE = re.compile(
    r"^\|\s*(?P<fecha>[^|]+?)\s*\|\s*(?P<modelo>[^|]+?)\s*\|\s*(?P<slide>[^|]+?)\s*\|\s*(?P<costo>[\d.]+)\s*\|\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class CostEntry:
    model: str
    slide_label: str
    cost_usd: float
    when: dt.datetime | None = None


def _existing_rows(resumen_path: Path) -> list[tuple[str, str, str, float]]:
    if not resumen_path.is_file():
        return []
    text = resumen_path.read_text(encoding="utf-8")
    rows = []
    for match in ROW_RE.finditer(text):
        rows.append(
            (match.group("fecha"), match.group("modelo"), match.group("slide"), float(match.group("costo")))
        )
    return rows


def record_image_costs(
    resumen_path: Path,
    project_label: str,
    entries: list[CostEntry],
) -> float:
    """Agrega `entries` a `resumen_path` y devuelve el total acumulado en USD.

    Si `entries` está vacío (ningún proveedor informó costo en esta
    corrida), no toca el archivo y devuelve el total ya existente.
    """
    existing = _existing_rows(resumen_path)
    if not entries:
        return sum(row[3] for row in existing)

    new_rows = [
        (
            (entry.when or dt.datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
            entry.model,
            entry.slide_label,
            entry.cost_usd,
        )
        for entry in entries
    ]
    all_rows = existing + new_rows
    total = sum(row[3] for row in all_rows)

    lines = [
        f"# Resumen de costos de imagen IA — {project_label}",
        "",
        "| Fecha | Modelo | Slide | Costo USD |",
        "|---|---|---|---|",
    ]
    for fecha, modelo, slide, costo in all_rows:
        lines.append(f"| {fecha} | {modelo} | {slide} | {costo:.4f} |")
    lines.append("")
    lines.append(f"**Total acumulado: ${total:.4f} USD**")
    lines.append("")

    resumen_path.parent.mkdir(parents=True, exist_ok=True)
    resumen_path.write_text("\n".join(lines), encoding="utf-8")
    return total
