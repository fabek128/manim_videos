from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .tenant import TenantContext

from pydantic import BaseModel, Field, model_validator

SlideType = Literal["cover", "text", "bullets", "code"]


class BrandConfig(BaseModel):
    name: str
    logo_path: str | None = None


class FontsConfig(BaseModel):
    title: str
    body: str
    code: str | None = None

class ColorsConfig(BaseModel):
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#D9D9D9"
    highlight_bg: str = "#0057D9"
    footer_text: str = "#FFFFFF"
    divider: str = "#666666"
    overlay_start: str = "#00000000"
    overlay_end: str = "#000000E6"


class SafeAreaConfig(BaseModel):
    """Override de los márgenes seguros del formato (fracción 0.0-1.0).

    Campo en `None` conserva el default calculado por
    `CanvasSpec.from_format()` para ese formato; solo se sobrescriben
    los lados declarados explícitamente.
    """

    left: float | None = Field(default=None, ge=0.0, le=0.45)
    top: float | None = Field(default=None, ge=0.0, le=0.45)
    right: float | None = Field(default=None, ge=0.0, le=0.45)
    bottom: float | None = Field(default=None, ge=0.0, le=0.45)


class MarginConfig(BaseModel):
    """Margen extra en píxeles, sumado al `safe_area` ya calculado.

    A diferencia de `safe_area` (fracción del lienzo, define el límite
    donde no puede haber contenido), este es un valor absoluto en
    píxeles para ajustar la separación entre ese límite y el contenido
    real, sin recalcular porcentajes. Default 20px por lado (baseline
    para todos los posts/videos); declarar `margin:` en la config solo
    hace falta para ajustar ese valor, no para activarlo.
    """

    left: int = Field(default=20, ge=0, le=200)
    top: int = Field(default=20, ge=0, le=200)
    right: int = Field(default=20, ge=0, le=200)
    bottom: int = Field(default=20, ge=0, le=200)


class ImageGenerationConfig(BaseModel):
    enabled: bool = False
    provider: Literal["openrouter"] = "openrouter"
    model: str | None = None
    prompt: str = ""
    negative_prompt: str | None = None
    width: int | None = None
    height: int | None = None
    seed: int | None = None
    variations: int = Field(default=1, ge=1, le=4)


class SlideConfig(BaseModel):
    type: SlideType = "cover"
    title: str = ""
    body: str = ""
    code: str = ""
    bullets: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    subtitle: str = ""
    footer_text: str | None = None
    source_text: str = ""
    background_image_path: str | None = None
    image_generation: ImageGenerationConfig | None = None
    entity_logos: list[str] = Field(
        default_factory=list,
        description="Logos SVG/PNG de las entidades mencionadas (paths relativos a assets/)",
    )


class ContentConfig(BaseModel):
    title: str
    highlights: list[str] = Field(default_factory=list)
    subtitle: str = ""
    footer_text: str = ""
    source_text: str = ""
    body: str = ""
    bullets: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    project_name: str
    output_dir: str
    format: str
    template: str = "news_card"
    brand: BrandConfig
    fonts: FontsConfig
    colors: ColorsConfig = Field(default_factory=ColorsConfig)
    safe_area: SafeAreaConfig | None = None
    margin: MarginConfig = Field(default_factory=MarginConfig)
    image_generation: ImageGenerationConfig = Field(default_factory=ImageGenerationConfig)
    background_image_path: str | None = None
    title: str | None = None
    subtitle: str = ""
    highlights: list[str] = Field(default_factory=list)
    footer_text: str = ""
    slides: list[SlideConfig] = Field(default_factory=list)
    content: ContentConfig | None = None
    content_slug: str | None = Field(
        default=None,
        description="Slug YYYY-MM-DD_tema; si está, la salida va a content/<slug>/renders/",
    )

    @model_validator(mode="after")
    def validate_content(self) -> "AppConfig":
        if not self.slides and self.content is None and not self.title:
            raise ValueError("La configuración necesita slides, content o title")
        if self.format not in {
            "post_square",
            "post_vertical",
            "story",
            "carousel_square",
            "carousel_vertical",
        }:
            raise ValueError(f"Formato no soportado: {self.format}")
        return self

    def resolved_output_dir(self, tenant: "TenantContext") -> Path:
        if self.content_slug:
            return tenant.content_path(self.content_slug, "renders")
        relative = Path(self.output_dir or self.project_name)
        return tenant.output_path(relative)

    def resolved_slides(self) -> list[SlideConfig]:
        if self.slides:
            return self.slides
        content = self.content
        assert content is not None or self.title
        if content:
            title = content.title
            highlights = content.highlights
            subtitle = content.subtitle
            footer_text = content.footer_text
            source_text = content.source_text
            body = content.body
            bullets = content.bullets
        else:
            title = self.title or ""
            highlights = self.highlights
            subtitle = self.subtitle
            footer_text = self.footer_text
            source_text = ""
            body = ""
            bullets = []
        image_config = self.image_generation.model_copy(deep=True)
        if self.background_image_path:
            background = self.background_image_path
        else:
            background = None
        return [
            SlideConfig(
                type="cover",
                title=title,
                highlights=highlights,
                subtitle=subtitle,
                footer_text=footer_text,
                source_text=source_text,
                body=body,
                bullets=bullets,
                background_image_path=background,
                image_generation=image_config,
            )
        ]
