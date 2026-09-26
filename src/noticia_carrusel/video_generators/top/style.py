from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class TopStyle:
    """Tokens visuales inmutables del generador top."""

    theme_name: str = "theme_default"
    # Zonas seguras Instagram (px) — franja superior/inferior reservada para UI
    safe_top_px: int = 220
    safe_bottom_px: int = 220
    # Margen horizontal: 15% por lado → 70% útil
    horizontal_margin_ratio: float = 0.15
    # Fondo
    background_image_opacity: float = 0.92
    background_overlay_opacity: float = 0.32
    # Colores
    highlighted_rank_color: str = "#FFD700"
    secondary_text_color: str = "#B9B9B9"
    # Entrada y traslado del título
    title_entry_shift_y: float = 0.3
    title_entry_time: float = 0.6
    title_hold_time: float = 4.0
    title_header_scale: float = 0.8
    title_header_time: float = 0.8
    # Entrada, lectura y aterrizaje de cada tarjeta
    card_entry_shift_y: float = 0.4
    card_entry_time: float = 0.5
    card_hold_time: float = 5.0
    card_flight_time: float = 0.7
    card_flight_move_ratio: float = 0.72
    card_entry_dim_opacity: float = 0.15
    card_landed_chip_opacity: float = 0.55
    card_landed_content_opacity: float = 0.5
    card_restore_opacity: float = 1.0
    card_highlight_pulse_factor: float = 1.05
    card_highlight_pulse_time: float = 0.4
    central_card_fill_opacity: float = 1.0
    central_card_height: float = 3.8
    ranking_card_height: float = 1.2
    central_comment_font_size: int = 34
    central_spec_label_font_size: int = 30
    central_spec_value_font_size: int = 34
    # El detalle se muestra en la tarjeta central; el ranking final prioriza legibilidad.
    ranking_show_comments: bool = False
    ranking_show_specs: bool = False
    # Zoom deliberado reusable
    zoom_scale_factor: float = 1.3
    zoom_transition_time: float = 0.3
    zoom_hold_time: float = 0.6
    # Revelado y hold del cierre
    reveal_opacity: float = 1.0
    reveal_time: float = 0.6
    final_min_frames: int = 2
    # Ola final del ranking
    wave_scale_factor: float = 1.05
    wave_transition_time: float = 0.12
    wave_hold_time: float = 0.04
    wave_between_items_time: float = 0.02
    wave_repetitions: int = 1
    wave_reverse: bool = False

    def with_overrides(self, **kwargs: object) -> TopStyle:
        return replace(self, **kwargs)  # type: ignore[arg-type]

    @property
    def horizontal_usable_ratio(self) -> float:
        return 1.0 - 2.0 * self.horizontal_margin_ratio
