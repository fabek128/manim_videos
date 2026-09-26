from __future__ import annotations

import os
import random
from dataclasses import dataclass, replace
from pathlib import Path

from noticia_carrusel.tenant import TenantContext, load_tenant

from .loader import load_top_spec
from .models import TopSpec
from .style import TopStyle


@dataclass(frozen=True)
class TopRenderContext:
    tenant: TenantContext
    spec_path: Path
    spec: TopSpec
    style: TopStyle
    rng: random.Random
    output_dir: Path
    seed: int

    def with_style(self, style: TopStyle) -> TopRenderContext:
        return replace(self, style=style)


def build_context_from_env(*, tenant: TenantContext | None = None) -> TopRenderContext:
    """Construye el contexto validando las variables internas del builder.

    Variables:
      TENANT, VIDEO_CONFIG, RENDER_SEED
    La escena nunca debe confiar en un path no validado.
    """
    # Tenant
    ctx_tenant = tenant or load_tenant(load_env=False)
    # Config
    raw_config = os.environ.get("VIDEO_CONFIG")
    if not raw_config:
        raise ValueError("Falta VIDEO_CONFIG (debe inyectarlo build.py)")
    spec_path = Path(raw_config).resolve()
    # Defensa: debe permanecer dentro del configs del tenant
    try:
        # Validar que esté dentro de tenants/<id>/configs/videos/top o configs/videos/top genérico
        allowed_root = (ctx_tenant.configs_dir / "videos").resolve()
        spec_path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError(f"VIDEO_CONFIG fuera de {allowed_root}: {spec_path}") from exc
    if not spec_path.is_file():
        raise FileNotFoundError(f"VIDEO_CONFIG no existe: {spec_path}")

    spec = load_top_spec(spec_path)

    # Style: theme desde manifest o override.
    theme_name = ctx_tenant.manifest.brand.default_theme or "theme_default"
    style = TopStyle(theme_name=theme_name)

    # Seed
    raw_seed = os.environ.get("RENDER_SEED")
    if raw_seed is None:
        # Fallback determinístico por config si el builder no inyectó seed
        seed = hash(spec_path.name) & 0x7FFFFFFF
    else:
        try:
            seed = int(raw_seed)
        except ValueError as exc:
            raise ValueError(f"RENDER_SEED inválido: {raw_seed!r}") from exc
    rng = random.Random(seed)

    # Output dir: media/videos/top/<config-stem> — derivado, no inyectado
    output_dir = ctx_tenant.media_dir / "videos" / "top" / spec_path.stem

    return TopRenderContext(
        tenant=ctx_tenant,
        spec_path=spec_path,
        spec=spec,
        style=style,
        rng=rng,
        output_dir=output_dir,
        seed=seed,
    )
