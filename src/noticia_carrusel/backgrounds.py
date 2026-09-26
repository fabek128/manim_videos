"""Selección de fondos reutilizables para el pipeline de posts.

Los fondos viven en ``tenants/<id>/assets/backgrounds/`` y ``assets/backgrounds/``.
La selección es estable para posts (hash) y reproducible para videos (seed).
Un fondo explícito siempre tiene prioridad y este módulo solo se consulta
como fallback.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

from .tenant import TenantContext

BACKGROUND_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})


def available_backgrounds(tenant: TenantContext) -> list[Path]:
    """Devuelve fondos válidos combinando global y tenant, ordenados por key lógica.

    Usa ``TenantContext.iter_assets`` para fusionar ``assets/backgrounds`` y
    ``tenants/<id>/assets/backgrounds``. Si la misma key existe en ambas capas,
    gana el tenant. ``manifest.json``/``vision_review.json`` no entran porque
    no son imágenes.
    """
    return list(tenant.iter_assets("backgrounds", extensions=BACKGROUND_EXTENSIONS))


def select_background(tenant: TenantContext, key: str) -> Path | None:
    """Selecciona un fondo de forma determinística a partir de ``key`` (hash)."""
    backgrounds = available_backgrounds(tenant)
    if not backgrounds:
        return None
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    index = int.from_bytes(digest[:8], "big") % len(backgrounds)
    return backgrounds[index]


def select_for_slide(tenant: TenantContext, project_name: str, index: int, title: str = "") -> Path | None:
    """Fondo estable para un slide, aislando tenant/proyecto/posición/título."""
    key = f"{tenant.id}:{project_name}:{index}:{title.strip()}"
    return select_background(tenant, key)


def select_random_background(tenant: TenantContext, rng: random.Random) -> Path | None:
    """Selección aleatoria pero reproducible vía ``rng`` (videos)."""
    backgrounds = available_backgrounds(tenant)
    if not backgrounds:
        return None
    return rng.choice(backgrounds)
