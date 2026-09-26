import pytest

from noticia_carrusel.web_capture.easing import (
    EASING_FUNCS,
    apply_easing,
    ease_in,
    ease_in_out,
    ease_out,
    linear,
)


@pytest.mark.parametrize("func", [linear, ease_in, ease_out, ease_in_out])
def test_boundaries_are_exact(func):
    assert func(0.0) == 0.0
    assert func(1.0) == 1.0


@pytest.mark.parametrize("func", [linear, ease_in, ease_out, ease_in_out])
def test_monotonic_increasing(func):
    samples = [func(i / 20) for i in range(21)]
    assert samples == sorted(samples)


def test_ease_in_starts_slower_than_ease_out_at_midpoint():
    assert ease_in(0.5) < 0.5 < ease_out(0.5)


def test_ease_in_out_symmetric_at_midpoint():
    assert ease_in_out(0.5) == pytest.approx(0.5)


def test_apply_easing_dispatches_by_name():
    assert apply_easing("linear", 0.3) == linear(0.3)
    assert apply_easing("ease_in", 0.3) == ease_in(0.3)
    assert apply_easing("ease_out", 0.3) == ease_out(0.3)
    assert apply_easing("ease_in_out", 0.3) == ease_in_out(0.3)


def test_apply_easing_clamps_out_of_range_t():
    assert apply_easing("linear", -1.0) == 0.0
    assert apply_easing("linear", 2.0) == 1.0


def test_apply_easing_unknown_name_raises():
    with pytest.raises(ValueError, match="Easing desconocido"):
        apply_easing("bounce", 0.5)


def test_all_curves_registered():
    assert set(EASING_FUNCS) == {"linear", "ease_in", "ease_out", "ease_in_out"}
