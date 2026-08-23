from manim import *


class IntroScene(Scene):
    """Animación de introducción: título con geometría básica."""

    def construct(self):
        # Título
        title = Text("Manim Videos", font_size=72, color=BLUE)
        subtitle = Text("Mi colección de animaciones", font_size=36, color=GRAY)

        # Geometría decorativa
        circle = Circle(radius=1, color=YELLOW, fill_opacity=0.2)
        square = Square(side_length=1.5, color=GREEN, fill_opacity=0.2)
        triangle = Triangle(color=RED, fill_opacity=0.2).scale(0.8)

        # Posicionar figuras
        shapes = VGroup(circle, square, triangle).arrange(RIGHT, buff=1)
        shapes.next_to(subtitle, DOWN, buff=1)

        # Animación
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle, shift=UP * 0.3))
        self.play(
            Create(circle),
            Create(square),
            Create(triangle),
            run_time=1.5,
        )
        self.play(
            circle.animate.set_fill(YELLOW, opacity=0.5),
            square.animate.set_fill(GREEN, opacity=0.5),
            triangle.animate.set_fill(RED, opacity=0.5),
            run_time=0.8,
        )

        # Rotación suave
        self.play(Rotate(shapes, angle=PI / 4), run_time=1)
        self.play(Rotate(shapes, angle=-PI / 4), run_time=1)

        # Pausa final
        self.wait(2)
