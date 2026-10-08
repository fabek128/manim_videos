from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path


from .backgrounds import select_for_slide
from .cost_summary import CostEntry, record_image_costs
from .models import AppConfig, ImageGenerationConfig, SlideConfig
from .providers import ImageGenerationResult, ImageProviderError, OpenRouterImageProvider
from .render.canvas import CanvasSpec
from .render.templates import NewsCardRenderer
from .tenant import TenantContext
from .web_capture import api as web_capture_api
from .web_capture.cache import cached_path as web_capture_cached_path

QUALITY_ALIASES = frozenset({"draft", "low", "medium", "high"})
MODEL_CATALOG_PATH = Path(__file__).with_name("image_models.jsonl")


@dataclass
class ModelEntry:
    model: str
    categories: list[str]
    weight: float = 1.0


def _load_model_catalog(path: Path | None = None) -> list[ModelEntry]:
    catalog_path = path or MODEL_CATALOG_PATH
    entries: list[ModelEntry] = []
    if not catalog_path.is_file():
        return entries
    for line_number, line in enumerate(catalog_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            model, categories = record["model"], record["categories"]
            weight = record.get("weight", 1)
            if not isinstance(model, str) or not model.strip():
                raise ValueError("model debe ser un string no vacío")
            if not isinstance(categories, list) or not all(isinstance(c, str) for c in categories):
                raise ValueError("categories debe ser una lista de strings")
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
                raise ValueError("weight debe ser numérico y no negativo")
            entries.append(ModelEntry(model.strip(), categories, float(weight)))
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise ImageProviderError(f"Catálogo JSONL inválido, línea {line_number}: {exc}") from exc
    return entries


def _select_model_for_category(category: str, catalog: list[ModelEntry] | None = None) -> str | None:
    entries = _load_model_catalog() if catalog is None else catalog
    eligible = [entry for entry in entries if category in entry.categories and entry.weight > 0]
    if not eligible:
        return None
    return random.choices([e.model for e in eligible], weights=[e.weight for e in eligible], k=1)[0]


def _model_for(image_config: ImageGenerationConfig, quality: str | None = None) -> str:
    configured = (image_config.model or "").strip()
    category = (quality or configured or "draft").strip().lower()
    if category == "example":
        category = "draft"
    if configured and configured.lower() not in {"draft", "example", "low", "medium", "high"}:
        return configured
    model = _select_model_for_category(category)
    if model:
        return model
    raise ImageProviderError(f"No hay modelos configurados para la categoría '{category}' en {MODEL_CATALOG_PATH}")


@dataclass
class GenerateOutput:
    paths: list[Path] = field(default_factory=list)
    cost_entries: list[CostEntry] = field(default_factory=list)
    run_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    resumen_path: Path | None = None
    reused_paths: list[Path] = field(default_factory=list)


def _intermediate_path(tenant: TenantContext, output_dir: Path, index: int) -> Path:
    return tenant.resolve_inside(output_dir, Path("intermediate") / f"base_{index:02d}.png")


def intermediate_images(config: AppConfig, tenant: TenantContext) -> list[Path]:
    """Imágenes base ya generadas para esta config, sin llamar a ninguna API.

    Uso: chequear antes de un prototipo si ya hay algo generado en
    `intermediate/`, para preguntarle al usuario si regenerar o reusar
    (ver AGENTS.md § Costos / reuso de imágenes intermedias).
    """
    output_dir = config.resolved_output_dir(tenant)
    slides = config.resolved_slides()
    existing = []
    for index, slide in enumerate(slides, start=1):
        image_config = slide.image_generation or config.image_generation
        if not image_config.enabled:
            continue
        path = _intermediate_path(tenant, output_dir, index)
        if path.is_file():
            existing.append(path)
    return existing


def _web_capture_path(
    tenant: TenantContext,
    slide: SlideConfig,
    reuse_intermediate: bool,
) -> tuple[Path, bool]:
    """Resuelve el fondo `web_capture` de un slide vía `web_capture.api`.

    Cachea en `tenant.cache_dir` por `(url, viewport, scale, selector, ...)`
    (ver `web_capture/cache.py`) — **no** en `output_dir/intermediate/`:
    varias configs que capturan la misma URL comparten la misma entrada de
    caché en vez de una copia por config. `reuse_intermediate=True` reusa
    un hit existente sin renavegar; `False` (default) siempre recaptura.
    """
    cfg = slide.web_capture
    assert cfg is not None
    already_cached = reuse_intermediate and web_capture_cached_path(tenant, cfg).is_file()
    path = web_capture_api.capture_url(
        url=cfg.url,
        width=cfg.viewport[0],
        height=cfg.viewport[1],
        scale=cfg.scale,
        selector=cfg.selector,
        full_page=cfg.full_page,
        wait_for_selector=cfg.wait_for_selector,
        wait_for_network_idle=cfg.wait_for_network_idle,
        delay_ms=cfg.delay_ms,
        timeout_ms=cfg.timeout_ms,
        tenant=tenant,
        force_capture=not reuse_intermediate,
    )
    return path, already_cached


def _base_image(
    config: AppConfig,
    slide: SlideConfig,
    tenant: TenantContext,
    output_dir: Path,
    index: int,
    quality: str | None = None,
    reuse_intermediate: bool = False,
) -> tuple[Path | None, ImageGenerationResult | None, bool]:
    image_config = slide.image_generation or config.image_generation
    source_ref = slide.background_image_path or config.background_image_path
    source = tenant.resolve_asset(source_ref) if source_ref else None
    if slide.web_capture is not None:
        # El screenshot se recorta al aspect ratio del post por el pipeline
        # de render existente (`_background()` -> `load_and_prepare()` ->
        # `smart_crop`, ver `render/templates.py`): sin costo, sin código
        # nuevo de cropping acá.
        path, reused = _web_capture_path(tenant, slide, reuse_intermediate)
        return path, None, reused
    if image_config.enabled:
        path = _intermediate_path(tenant, output_dir, index)
        if reuse_intermediate and path.is_file():
            return path, None, True
        spec = CanvasSpec.from_format(config.format)
        width, height = spec.width, spec.height
        provider = OpenRouterImageProvider(
            timeout=float(os.environ.get("OPENROUTER_IMAGE_TIMEOUT", "180"))
        )
        result = provider.generate(
            prompt=image_config.prompt,
            negative_prompt=image_config.negative_prompt,
            model=_model_for(image_config, quality),
            width=image_config.width or width,
            height=image_config.height or height,
            seed=image_config.seed,
            variations=image_config.variations,
            output_path=path,
        )
        return result.path, result, False
    if source is not None:
        return source, None, False
    if config.background_mode == "pool":
        # Fallback automático para cualquier post/carrusel que no declare
        # fondo: se elige un fondo del tenant de forma estable por proyecto,
        # slide y título. Si la carpeta no existe/vacía, el renderer conserva
        # su fondo procedural anterior.
        background = select_for_slide(tenant, config.project_name, index, slide.title)
        return background, None, False
    # `background_mode=solid` conserva el fondo procedural del renderer.
    return None, None, False


def _resumen_path(config: AppConfig, tenant: TenantContext, output_dir: Path) -> Path:
    if config.content_slug:
        return tenant.content_path(config.content_slug, "resumen.md")
    return output_dir / "resumen.md"


def generate(
    config: AppConfig,
    tenant: TenantContext,
    quality: str | None = None,
    reuse_intermediate: bool = False,
) -> GenerateOutput:
    output_dir = config.resolved_output_dir(tenant)
    output_dir.mkdir(parents=True, exist_ok=True)
    renderer = NewsCardRenderer(config, tenant)
    output = GenerateOutput()
    for index, slide in enumerate(config.resolved_slides(), start=1):
        background, image_result, reused = _base_image(
            config, slide, tenant, output_dir, index, quality, reuse_intermediate
        )
        result_path = tenant.resolve_inside(output_dir, f"slide_{index:02d}.png")
        renderer.render(slide, background).save(result_path, format="PNG", optimize=True)
        output.paths.append(result_path)
        if reused and background is not None:
            output.reused_paths.append(background)
        if image_result is not None and image_result.cost_usd is not None:
            entry = CostEntry(
                model=image_result.model,
                slide_label=f"slide_{index:02d} ({slide.type})",
                cost_usd=image_result.cost_usd,
            )
            output.cost_entries.append(entry)

    if output.cost_entries:
        output.run_cost_usd = sum(entry.cost_usd for entry in output.cost_entries)
        resumen_path = _resumen_path(config, tenant, output_dir)
        project_label = config.content_slug or config.project_name
        output.total_cost_usd = record_image_costs(resumen_path, project_label, output.cost_entries)
        output.resumen_path = resumen_path

    return output
