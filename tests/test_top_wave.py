from __future__ import annotations

import inspect
import math

import pytest
from manim import FadeIn, FadeOut, Mobject, Transform, config, there_and_back

from noticia_carrusel.video_generators.top.scene import BaseTopScene

from noticia_carrusel.video_generators.top.style import TopStyle


@pytest.fixture(autouse=True)
def _frame_rate_30(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "frame_rate", 30)


class _AnimationRecorder:
    def __init__(self, mob: "_FakeMobject") -> None:
        self.mob = mob
        self.factor: float | None = None
        self.rate_func = None
        self.calls: list[tuple[str, tuple, dict]] = []

    def __call__(self, *, rate_func):
        self.rate_func = rate_func
        return self

    def scale(self, factor: float):
        self.factor = factor
        self.calls.append(("scale", (factor,), {}))
        return self

    def __getattr__(self, name: str):
        def _record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return self

        return _record


class _FakeMobject(Mobject):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label
        self.logical_scale = 1.0

    @property
    def animate(self) -> _AnimationRecorder:
        return _AnimationRecorder(self)

    def scale(self, scale_factor: float, **kwargs):
        self.logical_scale *= scale_factor
        return self


class _FakeScene:
    def __init__(self) -> None:
        self.played: list[tuple[str, float, float]] = []
        self.play_calls: list[tuple[tuple, float]] = []
        self.waited: list[float] = []

    def play(self, *animations, run_time: float) -> None:
        for animation in animations:
            if isinstance(animation, _AnimationRecorder) and animation.factor is not None:
                animation.mob.scale(animation.factor)
                self.played.append((animation.mob.label, animation.factor, run_time))
        self.play_calls.append((animations, run_time))

    def wait(self, duration: float) -> None:
        self.waited.append(duration)


def test_play_scale_wave_respects_order_timings_and_restores_scale() -> None:
    scene = _FakeScene()
    first = _FakeMobject("first")
    second = _FakeMobject("second")

    BaseTopScene.play_scale_wave(
        scene,  # type: ignore[arg-type]
        [first, second],
        scale_factor=1.1,
        transition_time=0.25,
        hold_time=0.2,
        between_items_time=0.1,
        repetitions=2,
        reverse=True,
    )

    assert [label for label, _, _ in scene.played] == [
        "second",
        "second",
        "first",
        "first",
        "second",
        "second",
        "first",
        "first",
    ]
    assert [factor for _, factor, _ in scene.played] == pytest.approx(
        [1.1, 1 / 1.1, 1.1, 1 / 1.1, 1.1, 1 / 1.1, 1.1, 1 / 1.1]
    )
    assert all(run_time == 0.25 for _, _, run_time in scene.played)
    assert scene.waited == pytest.approx([0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2])
    assert first.logical_scale == pytest.approx(1.0)
    assert second.logical_scale == pytest.approx(1.0)


def test_play_scale_wave_empty_sequence_is_noop() -> None:
    scene = _FakeScene()
    BaseTopScene.play_scale_wave(scene, [])  # type: ignore[arg-type]
    assert scene.played == []
    assert scene.waited == []


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"scale_factor": 1.0}, ValueError),
        ({"scale_factor": math.inf}, ValueError),
        ({"transition_time": 0.0}, ValueError),
        ({"hold_time": -0.1}, ValueError),
        ({"between_items_time": -0.1}, ValueError),
        ({"repetitions": 0}, ValueError),
        ({"repetitions": True}, TypeError),
        ({"rate_func": None}, TypeError),
    ],
)
def test_play_scale_wave_rejects_invalid_parameters(kwargs, error) -> None:
    scene = _FakeScene()
    with pytest.raises(error):
        BaseTopScene.play_scale_wave(  # type: ignore[arg-type]
            scene,
            [_FakeMobject("item")],
            **kwargs,
        )


def test_play_scale_wave_rejects_non_mobject() -> None:
    scene = _FakeScene()
    with pytest.raises(TypeError, match=r"objects\[1\] debe ser Mobject"):
        BaseTopScene.play_scale_wave(  # type: ignore[arg-type]
            scene,
            [_FakeMobject("valid"), object()],  # type: ignore[list-item]
        )


def test_play_scale_wave_defaults_mirror_top_style() -> None:
    sig = inspect.signature(BaseTopScene.play_scale_wave)
    assert sig.parameters["scale_factor"].default == TopStyle.wave_scale_factor
    assert sig.parameters["transition_time"].default == TopStyle.wave_transition_time
    assert sig.parameters["hold_time"].default == TopStyle.wave_hold_time
    assert (
        sig.parameters["between_items_time"].default
        == TopStyle.wave_between_items_time
    )
    assert sig.parameters["repetitions"].default == TopStyle.wave_repetitions
    assert sig.parameters["reverse"].default == TopStyle.wave_reverse


def test_play_scale_wave_quantizes_sub_frame_waits() -> None:
    scene = _FakeScene()
    BaseTopScene.play_scale_wave(  # type: ignore[arg-type]
        scene,
        [_FakeMobject("a"), _FakeMobject("b")],
        transition_time=0.05,
        hold_time=0.02,
        between_items_time=0.01,
    )

    # hold (0.6 frames) y between (0.3 frames) a 30 fps se elevan a 1 frame.
    # La pausa entre saltos no ocurre tras el último objeto: 3 waits en total.
    assert scene.waited == pytest.approx([1 / 30, 1 / 30, 1 / 30])


def test_play_zoom_pulse_zooms_each_object_and_restores_scale() -> None:
    scene = _FakeScene()
    first = _FakeMobject("first")
    second = _FakeMobject("second")
    third = _FakeMobject("third")

    BaseTopScene.play_zoom_pulse(  # type: ignore[arg-type]
        scene,
        [first, second, third],
        scale_factor=1.4,
        transition_time=0.25,
        hold_time=0.5,
    )

    assert [label for label, _, _ in scene.played] == [
        "first",
        "first",
        "second",
        "second",
        "third",
        "third",
    ]
    assert [factor for _, factor, _ in scene.played] == pytest.approx(
        [1.4, 1 / 1.4, 1.4, 1 / 1.4, 1.4, 1 / 1.4]
    )
    assert all(run_time == 0.25 for _, _, run_time in scene.played)
    # Dwell por objeto; sin pausa entre saltos.
    assert scene.waited == pytest.approx([0.5, 0.5, 0.5])
    for mob in (first, second, third):
        assert mob.logical_scale == pytest.approx(1.0)


def test_play_zoom_pulse_defaults() -> None:
    scene = _FakeScene()
    BaseTopScene.play_zoom_pulse(scene, [_FakeMobject("a")])  # type: ignore[arg-type]

    assert [factor for _, factor, _ in scene.played] == pytest.approx([1.3, 1 / 1.3])
    assert [run_time for _, _, run_time in scene.played] == pytest.approx([0.3, 0.3])
    assert scene.waited == pytest.approx([0.6])


def test_play_zoom_pulse_rejects_invalid_scale_factor() -> None:
    scene = _FakeScene()
    with pytest.raises(ValueError, match="scale_factor debe ser finito y mayor que 1"):
        BaseTopScene.play_zoom_pulse(  # type: ignore[arg-type]
            scene,
            [_FakeMobject("a")],
            scale_factor=1.0,
        )


def _opacity_builders(animations) -> list[tuple]:
    pares: list[tuple] = []
    for anim in animations:
        if isinstance(anim, _AnimationRecorder):
            pares.append((anim.mob, anim.calls[0][1]))
        else:
            pares.append((anim.mobject, anim.methods[0].args))
    return pares


def test_ingreso_tarjeta_puesto_secuencia_completa() -> None:
    scene = _FakeScene()
    tarjeta = _FakeMobject("tarjeta")
    slot = _FakeMobject("slot")
    previo_chip = _FakeMobject("previo_chip")
    previo_contenido = _FakeMobject("previo_contenido")
    titulo = _FakeMobject("titulo")

    resultado = BaseTopScene.ingreso_tarjeta_puesto(  # type: ignore[arg-type]
        scene,
        3,
        tarjeta,
        slot,
        atenuar_entrada=[previo_chip, titulo],
        atenuar_vuelo=[(previo_chip, 0.55), (previo_contenido, 0.5)],
        restaurar_vuelo=[titulo],
        pulso=1.05,
        pulso_time=0.4,
        entrada_time=0.5,
        espera_time=5.0,
        vuelo_time=0.7,
    )

    assert resultado is slot
    assert [rt for _, rt in scene.play_calls] == pytest.approx(
        [0.5, 0.7 * 0.72, 0.7 * 0.28, 0.4]
    )
    entrada, movimiento, crossfade, pulso_anim = (
        animations for animations, _ in scene.play_calls
    )
    assert isinstance(entrada[0], FadeIn)
    assert _opacity_builders(entrada[1:]) == [
        (previo_chip, (TopStyle.card_entry_dim_opacity,)),
        (titulo, (TopStyle.card_entry_dim_opacity,)),
    ]
    assert movimiento[0].calls[0][0] == "scale"
    assert movimiento[0].calls[1][0] == "move_to"
    assert _opacity_builders(movimiento[1:]) == [
        (previo_chip, (0.55,)),
        (previo_contenido, (0.5,)),
        (titulo, (1.0,)),
    ]
    assert isinstance(crossfade[0], FadeOut)
    assert isinstance(crossfade[1], FadeIn)
    assert pulso_anim[0].mob is slot
    assert pulso_anim[0].rate_func is there_and_back
    assert pulso_anim[0].calls[0] == ("scale", (1.05,), {})
    assert scene.waited == pytest.approx([5.0])


def test_ingreso_tarjeta_puesto_sin_destino_saltea_vuelo_y_pulso() -> None:
    scene = _FakeScene()
    tarjeta = _FakeMobject("tarjeta")

    resultado = BaseTopScene.ingreso_tarjeta_puesto(  # type: ignore[arg-type]
        scene,
        1,
        tarjeta,
    )

    assert len(scene.play_calls) == 1
    entrada, rt = scene.play_calls[0]
    assert isinstance(entrada[0], FadeIn)
    assert rt == 0.5
    assert scene.waited == pytest.approx([5.0])
    assert resultado is tarjeta


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"puesto": 0}, ValueError),
        ({"puesto": True}, TypeError),
        ({"opacidad_entrada": 1.5}, ValueError),
        ({"pulso": 1.0}, ValueError),
        ({"pulso": 1.1, "pulso_time": 0.0}, ValueError),
        ({"entrada_time": 0.0}, ValueError),
        ({"shift": (0.0, 0.4)}, ValueError),
        ({"vuelo_move_ratio": 0.0}, ValueError),
        ({"vuelo_move_ratio": 1.0}, ValueError),
    ],
)
def test_ingreso_tarjeta_puesto_rechaza_parametros_invalidos(kwargs, error) -> None:
    scene = _FakeScene()
    with pytest.raises(error):
        BaseTopScene.ingreso_tarjeta_puesto(  # type: ignore[arg-type]
            scene,
            kwargs.pop("puesto", 1),
            _FakeMobject("tarjeta"),
            **kwargs,
        )


def test_ingreso_tarjeta_puesto_rechaza_objeto_no_mobject() -> None:
    scene = _FakeScene()
    with pytest.raises(TypeError, match="objeto debe ser Mobject"):
        BaseTopScene.ingreso_tarjeta_puesto(  # type: ignore[arg-type]
            scene,
            1,
            object(),  # type: ignore[arg-type]
        )


def test_ingreso_titulo_top_animates_entry_hold_and_transfer() -> None:
    scene = _FakeScene()
    titulo = _FakeMobject("titulo")
    destino = _FakeMobject("destino")

    BaseTopScene.ingreso_titulo_top(  # type: ignore[arg-type]
        scene,
        titulo,
        destino,
        shift=(0.0, 0.2, 0.0),
        entrada_time=0.4,
        hold_time=0.7,
        traslado_time=0.6,
    )

    assert [run_time for _, run_time in scene.play_calls] == [0.4, 0.6]
    assert isinstance(scene.play_calls[0][0][0], FadeIn)
    assert isinstance(scene.play_calls[1][0][0], Transform)
    assert scene.waited == pytest.approx([0.7])


def test_revelar_top_restores_all_opacities() -> None:
    scene = _FakeScene()
    first = _FakeMobject("first")
    second = _FakeMobject("second")

    BaseTopScene.revelar_top(  # type: ignore[arg-type]
        scene,
        [first, second],
        opacity=0.8,
        run_time=0.4,
    )

    animations, run_time = scene.play_calls[0]
    assert run_time == 0.4
    assert _opacity_builders(animations) == [
        (first, (0.8,)),
        (second, (0.8,)),
    ]


def test_espera_final_top_enforces_minimum_frames() -> None:
    scene = _FakeScene()
    BaseTopScene.espera_final_top(  # type: ignore[arg-type]
        scene,
        0.0,
        min_frames=2,
    )
    assert scene.waited == pytest.approx([2 / 30])


def test_animation_defaults_are_single_sourced_from_top_style() -> None:
    titulo = inspect.signature(BaseTopScene.ingreso_titulo_top).parameters
    assert titulo["entrada_time"].default == TopStyle.title_entry_time
    assert titulo["hold_time"].default == TopStyle.title_hold_time
    assert titulo["traslado_time"].default == TopStyle.title_header_time

    reveal = inspect.signature(BaseTopScene.revelar_top).parameters
    assert reveal["opacity"].default == TopStyle.reveal_opacity
    assert reveal["run_time"].default == TopStyle.reveal_time

    final = inspect.signature(BaseTopScene.espera_final_top).parameters
    assert final["min_frames"].default == TopStyle.final_min_frames

    zoom = inspect.signature(BaseTopScene.play_zoom_pulse).parameters
    assert zoom["scale_factor"].default == TopStyle.zoom_scale_factor
    assert zoom["transition_time"].default == TopStyle.zoom_transition_time
    assert zoom["hold_time"].default == TopStyle.zoom_hold_time

    tarjeta = inspect.signature(BaseTopScene.ingreso_tarjeta_puesto).parameters
    assert tarjeta["opacidad_entrada"].default == TopStyle.card_entry_dim_opacity
    assert tarjeta["pulso_time"].default == TopStyle.card_highlight_pulse_time
    assert tarjeta["entrada_time"].default == TopStyle.card_entry_time
    assert tarjeta["espera_time"].default == TopStyle.card_hold_time
    assert tarjeta["vuelo_time"].default == TopStyle.card_flight_time
    assert (
        tarjeta["vuelo_move_ratio"].default == TopStyle.card_flight_move_ratio
    )


@pytest.mark.parametrize(
    ("method", "args", "kwargs", "error"),
    [
        ("ingreso_titulo_top", (_FakeMobject("a"), _FakeMobject("b")), {"entrada_time": 0.0}, ValueError),
        ("revelar_top", ([_FakeMobject("a")],), {"opacity": 1.1}, ValueError),
        ("espera_final_top", (0.0,), {"min_frames": 0}, ValueError),
    ],
)
def test_reusable_animation_functions_reject_invalid_parameters(
    method, args, kwargs, error
) -> None:
    scene = _FakeScene()
    with pytest.raises(error):
        getattr(BaseTopScene, method)(scene, *args, **kwargs)
