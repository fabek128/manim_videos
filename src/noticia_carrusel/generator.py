from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


from .cost_summary import CostEntry, record_image_costs
from .models import AppConfig, ImageGenerationConfig, SlideConfig
from .providers import ImageGenerationResult, ImageProviderError, OpenRouterImageProvider
from .render.canvas import CanvasSpec
from .render.templates import NewsCardRenderer
from .tenant import TenantContext

QUALITY_ALIASES = frozenset({"draft", "low", "medium", "high"})


@dataclass
class GenerateOutput:
    paths: list[Path] = field(default_factory=list)
    cost_entries: list[CostEntry] = field(default_factory=list)
    run_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    resumen_path: Path | None = None
    reused_paths: list[Path] = field(default_factory=list)


def _model_for(image_config: ImageGenerationConfig, quality: str | None = None) -> str:
    configured = (quality or image_config.model or "").strip()
    if configured and configured != "MODEL_NAME_HERE":
        aliases = {
            "high": os.environ.get("OPENROUTER_IMAGE_QUALITY_HIGH_MODEL"),
            "medium": os.environ.get("OPENROUTER_IMAGE_QUALITY_MEDIUM_MODEL"),
            "low": os.environ.get("OPENROUTER_IMAGE_QUALITY_LOW_MODEL"),
        }
        if configured in {"draft", "example"}:
            configured = os.environ.get("OPENROUTER_IMAGE_DRAFT_MODELS", "").split(",")[0].strip()
        else:
            configured = aliases.get(configured, configured)
        if configured:
            return configured
    quality_fallback = os.environ.get("OPENROUTER_IMAGE_QUALITY_HIGH_MODEL")
    if quality_fallback:
        return quality_fallback
    raise ImageProviderError(
        "Falta image_generation.model o OPENROUTER_IMAGE_QUALITY_HIGH_MODEL"
    )


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
    return source, None, False


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
