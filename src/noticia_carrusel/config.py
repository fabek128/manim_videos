from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .models import AppConfig


def load_raw_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"No existe la configuración: {path}")
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            raise ValueError("La configuración debe ser .json, .yaml o .yml")
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"Configuración inválida en {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("La configuración debe ser un objeto raíz")
    return data


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser().resolve()
    return AppConfig.model_validate(load_raw_config(config_path))


def resolve_path(value: str | None, config_path: Path) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else (config_path.parent / path).resolve()
