"""Curvas de easing para el motor de cámara.

Implementadas desde cero, sin importar `manim` (que ya tiene equivalentes en
`rate_functions`): este módulo debe poder usarse también desde el pipeline de
posts estáticos (`generator.py`), sin arrastrar la dependencia de Manim. Ver
"Decisiones de diseño" #2 en `docs/web-capture-plan.md`.
"""

from __future__ import annotations

from typing import Callable


def linear(t: float) -> float:
    return t


def ease_in(t: float) -> float:
    """Cuadrática: arranca lento, acelera."""
    return t * t


def ease_out(t: float) -> float:
    """Cuadrática: arranca rápido, frena."""
    return 1.0 - (1.0 - t) * (1.0 - t)


def ease_in_out(t: float) -> float:
    """Cúbica simétrica: lento-rápido-lento."""
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


EASING_FUNCS: dict[str, Callable[[float], float]] = {
    "linear": linear,
    "ease_in": ease_in,
    "ease_out": ease_out,
    "ease_in_out": ease_in_out,
}


def apply_easing(name: str, t: float) -> float:
    """Aplica la curva `name` a `t` (clampeado a `[0, 1]` antes de evaluar)."""
    try:
        func = EASING_FUNCS[name]
    except KeyError as exc:
        known = ", ".join(sorted(EASING_FUNCS))
        raise ValueError(f"Easing desconocido {name!r}; disponibles: {known}") from exc
    clamped = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return func(clamped)
