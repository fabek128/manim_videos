from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class TextStyle:
    color: str = "#FFFFFF"
    line_spacing: int = 8
    tracking: int = 0
    stroke_width: int = 0
    stroke_fill: str = "#000000"
    shadow: bool = False

class TextEngine:
    """Render de texto TTF/OTF con wrap, ajuste de tamaño y highlights."""

    def __init__(self, title_font: str | Path, body_font: str | Path, code_font: str | Path | None = None):
        self.title_font = Path(title_font)
        self.body_font = Path(body_font)
        self.code_font = Path(code_font) if code_font else self.body_font
        for font_path in (self.title_font, self.body_font, self.code_font):
            if not font_path.is_file():
                raise FileNotFoundError(f"No existe la fuente configurada: {font_path}")

    @staticmethod
    def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(path), size=size)

    @staticmethod
    def bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, stroke_width: int = 0) -> tuple[int, int, int, int]:
        return draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)

    def wrap(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int, uppercase: bool = False) -> list[str]:
        value = text.upper() if uppercase else text
        lines: list[str] = []
        for paragraph in value.splitlines() or [""]:
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if self.bbox(draw, candidate, font)[2] <= max_width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines

    def fit_lines(self, draw: ImageDraw.ImageDraw, text: str, font_path: Path, max_width: int, max_lines: int, max_size: int, min_size: int, uppercase: bool = False) -> tuple[ImageFont.FreeTypeFont, list[str]]:
        for size in range(max_size, min_size - 1, -1):
            font = self.font(font_path, size)
            lines = self.wrap(draw, text, font, max_width, uppercase)
            if len(lines) <= max_lines:
                return font, lines
        font = self.font(font_path, min_size)
        return font, self.wrap(draw, text, font, max_width, uppercase)

    @staticmethod
    def block_height(draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.FreeTypeFont, line_spacing: int) -> int:
        if not lines:
            return 0
        heights = [draw.textbbox((0, 0), line or " ", font=font)[3] for line in lines]
        return sum(heights) + line_spacing * (len(lines) - 1)

    @classmethod
    def _clip_to_height(
        cls,
        draw: ImageDraw.ImageDraw,
        lines: list[str],
        font: ImageFont.FreeTypeFont,
        line_spacing: int,
        max_height: int,
    ) -> list[str]:
        """Descarta líneas finales hasta que el bloque entre en `max_height`.

        Nunca dibuja fuera del límite disponible (p. ej. el área segura),
        sin importar cuánto texto haya. `max_height <= 0` -> sin líneas.
        """
        if max_height <= 0:
            return []
        while lines and cls.block_height(draw, lines, font, line_spacing) > max_height:
            lines = lines[:-1]
        return lines


    @staticmethod
    def draw_text(
        draw: ImageDraw.ImageDraw,
        xy: tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: str,
        tracking: int = 0,
        stroke_width: int = 0,
        stroke_fill: str = "#000000",
    ) -> None:
        if tracking == 0:
            draw.text(xy, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            return
        x, y = xy
        for char in text:
            draw.text((x, y), char, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            x += round(draw.textlength(char, font=font)) + tracking
    def draw_block(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        text: str,
        max_width: int,
        max_lines: int,
        font_size: int,
        style: TextStyle | None = None,
        title: bool = False,
        uppercase: bool = False,
        align: str = "left",
        max_height: int | None = None,
    ) -> tuple[int, int]:
        style = style or TextStyle()
        draw = ImageDraw.Draw(image)
        font_path = self.title_font if title else self.body_font
        font, lines = self.fit_lines(draw, text, font_path, max_width, max_lines, font_size, max(16, font_size // 2), uppercase)
        if max_height is not None:
            lines = self._clip_to_height(draw, lines, font, style.line_spacing, max_height)
        y = xy[1]
        width = 0
        for line in lines:
            box = self.bbox(draw, line or " ", font, style.stroke_width)
            line_width = box[2] - box[0]
            width = max(width, line_width)
            x = xy[0] if align == "left" else xy[0] + (max_width - line_width) // 2 if align == "center" else xy[0] + max_width - line_width
            if style.shadow:
                self.draw_text(
                    draw, (x + 2, y + 3), line, font, "#000000AA",
                    style.tracking, style.stroke_width, "#000000AA"
                )
            self.draw_text(
                draw, (x, y), line, font, style.color, style.tracking,
                style.stroke_width, style.stroke_fill
            )

            y += box[3] - box[1] + style.line_spacing
        return width, y - xy[1] - style.line_spacing
    def draw_code_block(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        code: str,
        max_width: int,
        max_height: int,
        font_size: int = 28,
        padding: int = 24,
        line_spacing: int = 8,
    ) -> tuple[int, int]:
        """Renderiza <code>...</code> con fuente monoespaciada y numeración."""
        draw = ImageDraw.Draw(image)
        clean_code = html.unescape(re.sub(r"</?code(?:\s[^>]*)?>", "", code, flags=re.IGNORECASE)).strip("\n")
        lines = clean_code.splitlines() or [""]
        number_width = max(32, len(str(len(lines))) * max(12, font_size // 2))
        available_width = max_width - padding * 2 - number_width - 18
        for size in range(font_size, 13, -1):
            font = self.font(self.code_font, size)
            if max(
                draw.textlength(line, font=font) for line in lines
            ) <= available_width:
                break
        line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + line_spacing
        max_lines = (max_height - padding * 2) // line_height
        if max_lines <= 0:
            return max_width, 0
        visible = lines[:max_lines]
        if len(lines) > max_lines:
            visible[-1] = "…"
        panel_height = padding * 2 + len(visible) * line_height - line_spacing
        draw.rounded_rectangle(
            (xy[0], xy[1], xy[0] + max_width, xy[1] + panel_height),
            radius=14,
            fill="#0B1220",
            outline="#314764",
            width=2,
        )
        for index, line in enumerate(visible, start=1):
            y = xy[1] + padding + (index - 1) * line_height
            draw.text((xy[0] + padding, y), str(index), font=font, fill="#6F86A8")
            draw.text((xy[0] + padding + number_width + 18, y), line, font=font, fill="#F2F5F8")
        return max_width, panel_height

    def draw_highlights(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        text: str,
        highlights: list[str],
        max_width: int,
        font_size: int,
        text_color: str,
        highlight_color: str,
        padding: int = 10,
        line_spacing: int = 10,
        uppercase: bool = True,
        max_lines: int = 5,
        max_height: int | None = None,
    ) -> tuple[int, int]:
        draw = ImageDraw.Draw(image)
        font, lines = self.fit_lines(
            draw, text, self.title_font, max_width, max_lines, font_size,
            max(18, font_size // 2), uppercase
        )
        if max_height is not None:
            lines = self._clip_to_height(draw, lines, font, line_spacing, max_height)
        highlight_set = sorted(
            (item.strip().upper() for item in highlights if item.strip()),
            key=len,
            reverse=True,
        )
        y = xy[1]
        max_right = xy[0]
        for line in lines:
            upper_line = line.upper()
            for phrase in highlight_set:
                start = upper_line.find(phrase)
                if start < 0:
                    continue
                x0 = xy[0] + round(draw.textlength(line[:start], font=font))
                x1 = x0 + round(draw.textlength(line[start:start + len(phrase)], font=font))
                draw.rounded_rectangle(
                    (x0 - padding, y - padding // 2, x1 + padding, y + font.size + padding // 2),
                    radius=6,
                    fill=highlight_color,
                )
            draw.text((xy[0], y), line, font=font, fill=text_color)
            line_width = round(draw.textlength(line, font=font))
            max_right = max(max_right, xy[0] + line_width)
            y += draw.textbbox((0, 0), line or " ", font=font)[3] + line_spacing
        return max_right - xy[0], y - xy[1] - line_spacing
