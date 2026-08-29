from pathlib import Path

from manim import *

LOGO = Path(__file__).parents[2] / "assets" / "logos" / "fabian128k" / "fabian128k_paths.svg"


class LogoFabian128k(Scene):
    """Logo @fabian128k: FadeIn rápido, sin zoom."""

    def construct(self):
        logo = SVGMobject(LOGO)
        logo.width = 8

        self.play(FadeIn(logo), run_time=0.3)
