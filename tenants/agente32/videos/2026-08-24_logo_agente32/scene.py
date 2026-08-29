from pathlib import Path

from manim import *



class LogoAgente32(Scene):
    """Logo AGENTE32 importado desde assets/agente32_paths.svg.

    El SVG debe estar convertido a curvas (texto -> paths) y sin
    stroke-width residuales. Ver docs del asset.
    """

    BAR_GROW_PX = 6  # crecimiento TOTAL de la barra azul, en pixeles del render

    def construct(self):
        logo = SVGMobject(Path(__file__).parents[2] / "assets" / "logos" / "agente32" / "agente32_paths.svg")
        logo.width = 12

        bar = logo[0]
        self._grow_bar(bar)

        self.play(FadeIn(logo), run_time=0.3)
        self.play(
            logo.animate(rate_func=there_and_back).scale(1.06),
            run_time=0.4,
        )

    def _grow_bar(self, bar):
        """Expande la barra BAR_GROW_PX en total (centrado), texto fijo."""
        units_per_px = config.frame_width / config.pixel_width
        grow = self.BAR_GROW_PX * units_per_px
        bar.stretch_to_fit_width(bar.width + grow)
        bar.stretch_to_fit_height(bar.height + grow)
