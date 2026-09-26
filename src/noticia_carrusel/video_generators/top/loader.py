from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import TopSpec


def load_top_spec(path: Path) -> TopSpec:
    """Carga y valida un TopSpec desde un JSON ya resuelto.

    No selecciona "el más reciente", no toca variables de entorno,
    no hace I/O aleatoria. El path debe haber sido validado por el builder.
    """
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileNotFoundError(f"No se pudo leer el config: {path}") from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido en {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"El config debe ser un objeto JSON: {path}")
    try:
        return TopSpec.model_validate(data)
    except ValidationError as exc:
        # Mensaje con archivo y campos
        raise ValueError(f"Config inválido {path}: {exc}") from exc
