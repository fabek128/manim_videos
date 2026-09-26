from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

try:
    import cairosvg
except (ImportError, OSError):
    cairosvg = None
    if sys.platform == "darwin":
        # Fundido a las librerías de cairo del sistema si Homebrew las expone.
        brew_lib = Path("/opt/homebrew/lib")
        if brew_lib.is_dir():
            current = os.environ.get("DYLD_LIBRARY_PATH", "")
            os.environ["DYLD_LIBRARY_PATH"] = f"{brew_lib}:{current}" if current else str(brew_lib)
    try:
        import cairosvg  # noqa: F811
    except (ImportError, OSError):
        cairosvg = None

from PIL import Image, ImageDraw

from ..models import AppConfig, SlideConfig
from ..vision.image_ops import load_and_prepare
from ..tenant import TenantContext
from .canvas import CanvasSpec, draw_divider
from .overlays import add_gradient
from .text_engine import TextEngine, TextStyle


class NewsCardRenderer:
    """Renderiza placas editoriales sin delegar texto a la IA."""

    def __init__(self, config: AppConfig, tenant: TenantContext):
        self.config = config
        self.tenant = tenant
        safe = config.safe_area
        canvas = CanvasSpec.from_format(
            config.format,
            safe_left=safe.left if safe else None,
            safe_top=safe.top if safe else None,
            safe_right=safe.right if safe else None,
            safe_bottom=safe.bottom if safe else None,
        )
        margin = config.margin
        if margin.left or margin.top or margin.right or margin.bottom:
            canvas = CanvasSpec(
                canvas.width,
                canvas.height,
                canvas.safe.expand(margin.left, margin.top, margin.right, margin.bottom),
            )
        self.canvas = canvas
        self.title_font = tenant.resolve_asset(config.fonts.title)
        self.body_font = tenant.resolve_asset(config.fonts.body)
        self.code_font = tenant.resolve_asset(
            config.fonts.code or "fonts/FiraCode-Regular.ttf"
        )
        self.engine = TextEngine(self.title_font, self.body_font, self.code_font)

    def _background(
        self,
        slide: SlideConfig,
        path: Path | None = None,
        start_at: float = 0.70,
        end_at: float = 1.0,
    ) -> Image.Image:
        source = path
        if source and source.is_file():
            image = load_and_prepare(source, (self.canvas.width, self.canvas.height))
        else:
            image = self.canvas.new_image("#15243A")
            draw = ImageDraw.Draw(image)
            for x in range(0, image.width, 80):
                draw.line((x, 0, image.width - x // 3, image.height), fill="#203A5D", width=3)
            diameter = round(image.width * 0.42)
            center_x = round(image.width * 0.68)
            center_y = round(image.height * 0.30)
            draw.ellipse(
                (center_x - diameter // 2, center_y - diameter // 2,
                 center_x + diameter // 2, center_y + diameter // 2),
                fill="#244D83",
            )
        colors = self.config.colors
        return add_gradient(image, colors.overlay_start, colors.overlay_end, start_at=start_at, end_at=end_at)

    def _load_image_asset(self, path: Path, max_size: tuple[int, int]) -> Image.Image | None:
        try:
            if path.suffix.lower() == ".svg":
                if cairosvg is None:
                    raise RuntimeError(
                        f"cairosvg no disponible para renderizar SVG {path}. "
                        "Instalalo: pip install cairosvg (o uv pip install cairosvg)"
                    )
                png_bytes = cairosvg.svg2png(url=str(path), output_width=720)
                image = Image.open(BytesIO(png_bytes)).convert("RGBA")
            elif path.suffix.lower() != ".svg":
                image = Image.open(path).convert("RGBA")
            else:
                return None
            bbox = image.getbbox()
            if bbox:
                image = image.crop(bbox)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            return image
        except (OSError, ValueError):
            return None

    def _load_logo(self) -> Image.Image | None:
        logo_ref = self.config.brand.logo_path or self.tenant.manifest.brand.logo
        try:
            logo_path = self.tenant.resolve_asset(logo_ref)
        except (FileNotFoundError, ValueError):
            return None
        return self._load_image_asset(logo_path, (360, 88))

    def _load_entity_logos(self, slide: SlideConfig) -> list[Image.Image]:
        logos = []
        for ref in slide.entity_logos:
            try:
                path = self.tenant.resolve_asset(ref)
            except (FileNotFoundError, ValueError):
                continue
            logo = self._load_image_asset(path, (200, 140))
            if logo is not None:
                logos.append(logo)
        return logos

    def _draw_entity_logos(self, image: Image.Image, slide: SlideConfig, bottom_y: int) -> None:
        logos = self._load_entity_logos(slide)
        if not logos:
            return
        chip_pad = 22
        chip_gap = 24
        chip_h = max(logo.height for logo in logos) + chip_pad * 2
        chip_widths = [logo.width + chip_pad * 2 for logo in logos]
        total_width = sum(chip_widths) + chip_gap * (len(logos) - 1)
        x = (image.width - total_width) // 2
        y = bottom_y - chip_h
        draw = ImageDraw.Draw(image)
        for logo, chip_w in zip(logos, chip_widths):
            draw.rounded_rectangle(
                (x, y, x + chip_w, y + chip_h), radius=18, fill="#FFFFFF"
            )
            paste_x = x + (chip_w - logo.width) // 2
            paste_y = y + (chip_h - logo.height) // 2
            image.alpha_composite(logo, (paste_x, paste_y))
            x += chip_w + chip_gap

    def _draw_social_icon(self, image: Image.Image, xy: tuple[int, int], size: int) -> None:
        draw = ImageDraw.Draw(image)
        x, y = xy
        color = self.config.colors.footer_text
        draw.rounded_rectangle((x, y, x + size, y + size), radius=size // 4, outline=color, width=max(2, size // 14))
        inset = size // 4
        draw.ellipse((x + inset, y + inset, x + size - inset, y + size - inset), outline=color, width=max(2, size // 14))
        dot = max(3, size // 10)
        draw.ellipse((x + size - inset, y + inset // 2, x + size - inset + dot, y + inset // 2 + dot), fill=color)
    def _draw_divider_logo(self, image: Image.Image, center_x: int, y: int) -> None:
        logo = self._load_logo()
        if logo is not None:
            logo.thumbnail((288, 70), Image.Resampling.LANCZOS)
            image.alpha_composite(logo, (center_x - logo.width // 2, y - logo.height // 2))
            return
        draw = ImageDraw.Draw(image)
        font = self.engine.font(self.body_font, 22)
        label = self.config.brand.name
        width = draw.textbbox((0, 0), label, font=font)[2]
        draw.text((center_x - width // 2, y - 14), label, font=font, fill=self.config.colors.footer_text)

    def _draw_brand(self, image: Image.Image, slide: SlideConfig) -> None:
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = self.canvas.safe.box(image)
        footer_font = self.engine.font(self.body_font, 31)
        handle = "@fabian128k"
        handle_width = draw.textbbox((0, 0), handle, font=footer_font)[2]
        icon_size = 41
        footer_y = bottom - max(icon_size, footer_font.size)
        icon_x = right - icon_size
        handle_x = icon_x - 16 - handle_width
        draw.text((handle_x, footer_y), handle, font=footer_font, fill=self.config.colors.footer_text)
        self._draw_social_icon(image, (icon_x, footer_y), icon_size)
        if slide.source_text:
            source_font = self.engine.font(self.body_font, 24)
            draw.text((left, footer_y + 5), slide.source_text, font=source_font, fill=self.config.colors.text_secondary)

    # Altura mínima reservada para título+descripción de portada, medida
    # desde el divisor hasta el límite real de contenido (ver abajo).
    # Evita que un `safe_area.bottom` grande empuje el divisor tan abajo
    # que no quede lugar para el texto (ver theme_carousel_system.md →
    # "Safe area configurable").
    MIN_COVER_TEXT_HEIGHT = 200

    # El footer (_draw_brand: handle + ícono social) vive pegado al
    # borde inferior de la zona segura y no lo mueve ningún override.
    # Todo el resto del contenido (título, cuerpo, bullets, código)
    # debe terminar ANTES de esta franja, no en `safe_bottom_edge`
    # directamente, o el footer y el texto terminan superpuestos.
    FOOTER_RESERVED_HEIGHT = 70

    def render(self, slide: SlideConfig, background_path: Path | None = None) -> Image.Image:
        safe_top = self.canvas.safe.top
        safe_bottom_edge = self.canvas.height - self.canvas.safe.bottom
        content_bottom_limit = safe_bottom_edge - self.FOOTER_RESERVED_HEIGHT
        is_cover = slide.type == "cover"

        if is_cover:
            # 70% del lienzo es el default visual; nunca empuja el texto
            # más allá de lo que la zona segura inferior (menos el
            # footer) permite.
            split_y = min(
                round(self.canvas.height * 0.70),
                max(safe_top, content_bottom_limit - self.MIN_COVER_TEXT_HEIGHT),
            )
            divider_line_y = split_y
            gradient_end_span = 0.12
        else:
            divider_y = safe_top + round((safe_bottom_edge - safe_top) * 0.10)
            divider_line_y = divider_y
            gradient_end_span = 0.32

        # El degradado arranca un poco antes de la línea divisoria (donde
        # vive el logo), en todos los casos, para que la imagen ya esté
        # oscureciendo cuando aparece el divisor y el logo. Llega a
        # oscuridad total antes del final de la zona de texto de cada
        # slide (spec en templates/prompts/theme_carousel_system.md).
        gradient_start_at = max(0.0, (divider_line_y - 60) / self.canvas.height)
        gradient_end_at = min(1.0, gradient_start_at + gradient_end_span)

        image = self._background(
            slide, background_path, start_at=gradient_start_at, end_at=gradient_end_at
        )
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = self.canvas.safe.box(image)
        content_width = right - left
        title = slide.title.strip().upper()

        if is_cover:
            self._draw_entity_logos(image, slide, split_y - 95)
            draw_divider(draw, split_y, self.canvas, self.config.colors.divider, width=2)
            self._draw_divider_logo(image, self.canvas.width // 2, split_y)
            title_y = split_y + 46
            _, title_height = self.engine.draw_highlights(
                image, (left, title_y), title, slide.highlights, content_width,
                font_size=60 if self.canvas.height <= 1350 else 72,
                text_color=self.config.colors.text_primary,
                highlight_color=self.config.colors.highlight_bg,
                padding=10, line_spacing=8, max_lines=3,
                max_height=max(0, content_bottom_limit - title_y),
            )
            description = slide.body.strip() or slide.subtitle.strip()
            description_y = title_y + title_height + 14
            description_max_height = content_bottom_limit - description_y
            if description and description_max_height > 20:
                self.engine.draw_block(
                    image, (left, description_y), description,
                    content_width, max_lines=2,
                    font_size=26 if self.canvas.height <= 1350 else 30,
                    style=TextStyle(color=self.config.colors.text_secondary, line_spacing=8, shadow=True),
                    max_height=description_max_height,
                )
        else:
            draw_divider(draw, divider_y, self.canvas, self.config.colors.divider, width=2)
            self._draw_divider_logo(image, self.canvas.width // 2, divider_y)
            title_y = divider_y + 48
            _, title_height = self.engine.draw_block(
                image, (left, title_y), title, content_width, max_lines=4,
                font_size=76 if self.canvas.height <= 1350 else 84,
                style=TextStyle(color=self.config.colors.text_primary, line_spacing=12, shadow=True),
                title=True, uppercase=True,
                max_height=max(0, content_bottom_limit - title_y),
            )
            body_y = max(title_y + title_height + 28, top + round((bottom - top) * 0.28))
            if slide.subtitle and body_y < content_bottom_limit:
                subtitle_font = self.engine.font(self.body_font, 28)
                draw.text((left, body_y), slide.subtitle, font=subtitle_font, fill=self.config.colors.text_secondary)
                body_y += 44
            remaining_height = max(0, content_bottom_limit - body_y)
            if slide.type == "code":
                self.engine.draw_code_block(
                    image, (left, body_y), slide.code or slide.body, content_width,
                    max_height=remaining_height,
                    font_size=28 if self.canvas.height <= 1350 else 34,
                )
            else:
                body = (
                    "\n".join(f"• {item}" for item in slide.bullets)
                    if slide.type == "bullets"
                    else slide.body
                )
                self.engine.draw_block(
                    image, (left, body_y), body, content_width, max_lines=8,
                    font_size=38 if self.canvas.height <= 1350 else 42,
                    style=TextStyle(color=self.config.colors.text_secondary, line_spacing=12, shadow=True),
                    max_height=remaining_height,
                )

        self._draw_brand(image, slide)
        return image.convert("RGB")
