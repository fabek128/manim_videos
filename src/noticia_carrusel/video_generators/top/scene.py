from __future__ import annotations

import math

import numpy as np
from collections.abc import Callable, Iterable
from typing import NamedTuple

from manim import (
    Mobject,
    FadeIn,
    FadeOut,
    Transform,
    config,
    smooth,
    there_and_back,
)

from utils.theme import DEFAULT, AGENTE32, ThemedScene

from .composer import TopComposer
from .context import TopRenderContext, build_context_from_env

from .style import TopStyle


def _quantize_wait(duration: float) -> float:
    """Alinea una pausa positiva a frames completos sin acortarla."""
    if duration <= 0:
        return 0.0
    fps = config.frame_rate
    return math.ceil(duration * fps) / fps


def _recorrer_pulsos_escala(
    scene: object,
    sequence: tuple[Mobject, ...],
    *,
    scale_factor: float,
    transition_time: float,
    hold_time: float,
    between_items_time: float,
    repetitions: int,
    reverse: bool,
    rate_func: Callable[[float], float],
) -> None:
    """Ejecuta los pulsos de escala secuencialmente sobre la secuencia."""
    if not sequence:
        return
    ordered = tuple(reversed(sequence)) if reverse else sequence
    total_items = len(ordered) * repetitions
    completed = 0
    inverse_factor = 1.0 / scale_factor

    # Las pausas se alinean a frames completos: Manim descartaría una
    # duración positiva menor a un frame.

    for _ in range(repetitions):
        for mob in ordered:
            scene.play(
                mob.animate(rate_func=rate_func).scale(scale_factor),
                run_time=transition_time,
            )
            if hold_time:
                scene.wait(_quantize_wait(hold_time))
            scene.play(
                mob.animate(rate_func=rate_func).scale(inverse_factor),
                run_time=transition_time,
            )
            completed += 1
            if between_items_time and completed < total_items:
                scene.wait(_quantize_wait(between_items_time))


def _validar_pulsos_escala(
    objects: Iterable[Mobject],
    scale_factor: float,
    transition_time: float,
    hold_time: float,
    between_items_time: float,
    repetitions: int,
    rate_func: Callable[[float], float],
) -> tuple[Mobject, ...]:
    """Valida parámetros de pulso de escala y devuelve la secuencia."""
    sequence = tuple(objects)
    if not sequence:
        return sequence
    for index, mob in enumerate(sequence):
        if not isinstance(mob, Mobject):
            raise TypeError(
                f"objects[{index}] debe ser Mobject, recibido {type(mob).__name__}"
            )
    if not math.isfinite(scale_factor) or scale_factor <= 1:
        raise ValueError("scale_factor debe ser finito y mayor que 1")
    for name, value in (
        ("transition_time", transition_time),
        ("hold_time", hold_time),
        ("between_items_time", between_items_time),
    ):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} debe ser finito y no negativo")
    if transition_time == 0:
        raise ValueError("transition_time debe ser mayor que 0")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int):
        raise TypeError("repetitions debe ser un entero")
    if repetitions < 1:
        raise ValueError("repetitions debe ser al menos 1")
    if not callable(rate_func):
        raise TypeError("rate_func debe ser callable")
    return sequence


class _IngresoTarjetaParams(NamedTuple):
    """Parámetros validados de :meth:`ingreso_tarjeta_puesto`."""

    atenuar_entrada: tuple[Mobject, ...]
    opacidad_entrada: float
    atenuar_vuelo: tuple[tuple[Mobject, float], ...]
    restaurar_vuelo: tuple[Mobject, ...]
    opacidad_restaurar: float
    pulso: float
    pulso_time: float
    shift: np.ndarray
    entrada_time: float
    espera_time: float
    vuelo_time: float
    vuelo_move_ratio: float
    entrada_rate_func: Callable[[float], float]
    vuelo_rate_func: Callable[[float], float]
    pulso_rate_func: Callable[[float], float]


def _validar_ingreso_tarjeta(
    puesto: int,
    objeto: Mobject,
    destino: Mobject | None,
    atenuar_entrada: Iterable[Mobject],
    opacidad_entrada: float,
    atenuar_vuelo: Iterable[tuple[Mobject, float]],
    restaurar_vuelo: Iterable[Mobject],
    opacidad_restaurar: float,
    pulso: float,
    pulso_time: float,
    shift: Iterable[float],
    entrada_time: float,
    espera_time: float,
    vuelo_time: float,
    vuelo_move_ratio: float,
    entrada_rate_func: Callable[[float], float],
    vuelo_rate_func: Callable[[float], float],
    pulso_rate_func: Callable[[float], float],
) -> _IngresoTarjetaParams:
    """Valida parámetros de ingreso y devuelve la configuración normalizada."""
    if isinstance(puesto, bool) or not isinstance(puesto, int):
        raise TypeError("puesto debe ser un entero")
    if puesto < 1:
        raise ValueError("puesto debe ser al menos 1")
    chequear_mobs: list[tuple[str, Mobject]] = [("objeto", objeto)]
    if destino is not None:
        chequear_mobs.append(("destino", destino))
    for nombre, valor in chequear_mobs:
        if not isinstance(valor, Mobject):
            raise TypeError(f"{nombre} debe ser Mobject, recibido {type(valor).__name__}")
    atenuar_entrada_t = tuple(atenuar_entrada)
    restaurar_vuelo_t = tuple(restaurar_vuelo)
    for mob in (*atenuar_entrada_t, *restaurar_vuelo_t):
        if not isinstance(mob, Mobject):
            raise TypeError("los objetos a atenuar o restaurar deben ser Mobject")
    atenuar_vuelo_t = tuple(atenuar_vuelo)
    for par in atenuar_vuelo_t:
        mob, opacidad = par
        if not isinstance(mob, Mobject):
            raise TypeError("los pares de atenuar_vuelo deben ser (Mobject, float)")
        if not math.isfinite(opacidad) or not 0 <= opacidad <= 1:
            raise ValueError("las opacidades de atenuar_vuelo deben estar en [0, 1]")
    for nombre, valor in (
        ("opacidad_entrada", opacidad_entrada),
        ("opacidad_restaurar", opacidad_restaurar),
    ):
        if not math.isfinite(valor) or not 0 <= valor <= 1:
            raise ValueError(f"{nombre} debe ser un float en [0, 1]")
    if not math.isfinite(pulso) or pulso < 0:
        raise ValueError("pulso debe ser finito y no negativo")
    if pulso != 0 and pulso <= 1:
        raise ValueError("pulso debe ser mayor que 1 o 0 para deshabilitarlo")
    for nombre, valor in (
        ("entrada_time", entrada_time),
        ("vuelo_time", vuelo_time),
    ):
        if not math.isfinite(valor) or valor <= 0:
            raise ValueError(f"{nombre} debe ser finito y mayor que 0")
    if not math.isfinite(vuelo_move_ratio) or not 0 < vuelo_move_ratio < 1:
        raise ValueError("vuelo_move_ratio debe ser finito y estar entre 0 y 1")
    for nombre, valor in (
        ("pulso_time", pulso_time),
        ("espera_time", espera_time),
    ):
        if not math.isfinite(valor) or valor < 0:
            raise ValueError(f"{nombre} debe ser finito y no negativo")
    if pulso and pulso_time == 0:
        raise ValueError(
            "pulso_time debe ser mayor que 0 cuando pulso está habilitado"
        )
    shift_t = np.asarray(tuple(float(v) for v in shift), dtype=float)
    if shift_t.shape != (3,) or not np.all(np.isfinite(shift_t)):
        raise ValueError("shift debe ser un vector de 3 componentes finitas")
    for nombre, valor in (
        ("entrada_rate_func", entrada_rate_func),
        ("vuelo_rate_func", vuelo_rate_func),
        ("pulso_rate_func", pulso_rate_func),
    ):
        if not callable(valor):
            raise TypeError(f"{nombre} debe ser callable")
    return _IngresoTarjetaParams(
        atenuar_entrada_t,
        opacidad_entrada,
        atenuar_vuelo_t,
        restaurar_vuelo_t,
        opacidad_restaurar,
        pulso,
        pulso_time,
        shift_t,
        entrada_time,
        espera_time,
        vuelo_time,
        vuelo_move_ratio,
        entrada_rate_func,
        vuelo_rate_func,
        pulso_rate_func,
    )


def _animar_ingreso_tarjeta(
    scene: object,
    objeto: Mobject,
    destino: Mobject | None,
    params: _IngresoTarjetaParams,
) -> Mobject:
    """Ejecuta entrada, espera, vuelo y pulso de aterrizaje de la tarjeta."""
    entrada = [
        FadeIn(
            objeto,
            shift=params.shift,
            rate_func=params.entrada_rate_func,
        )
    ]
    entrada += [
        mob.animate.set_opacity(params.opacidad_entrada)  # type: ignore[union-attr]
        for mob in params.atenuar_entrada
    ]
    scene.play(*entrada, run_time=params.entrada_time)  # type: ignore[attr-defined]
    if params.espera_time:
        scene.wait(_quantize_wait(params.espera_time))  # type: ignore[attr-defined]
    if destino is None:
        return objeto
    ancho_origen = objeto.width
    alto_origen = objeto.height
    escala_destino = min(
        destino.width / ancho_origen if ancho_origen > 0 else 1.0,
        destino.height / alto_origen if alto_origen > 0 else 1.0,
    )
    movimiento = [
        objeto.animate(rate_func=params.vuelo_rate_func)
        .scale(escala_destino)
        .move_to(destino.get_center())
    ]
    movimiento += [
        mob.animate.set_opacity(opacidad)  # type: ignore[union-attr]
        for mob, opacidad in params.atenuar_vuelo
    ]
    movimiento += [
        mob.animate.set_opacity(params.opacidad_restaurar)  # type: ignore[union-attr]
        for mob in params.restaurar_vuelo
    ]
    movimiento_time = params.vuelo_time * params.vuelo_move_ratio
    scene.play(*movimiento, run_time=movimiento_time)  # type: ignore[attr-defined]
    scene.play(  # type: ignore[attr-defined]
        FadeOut(objeto, rate_func=params.vuelo_rate_func),
        FadeIn(destino, rate_func=params.vuelo_rate_func),
        run_time=params.vuelo_time - movimiento_time,
    )
    if params.pulso:
        scene.play(  # type: ignore[attr-defined]
            destino.animate(rate_func=params.pulso_rate_func).scale(params.pulso),
            run_time=params.pulso_time,
        )
    return destino


class BaseTopScene(ThemedScene):
    """Escena base para el generador top — resuelve contexto y delega a composer."""

    def construct(self) -> None:
        context = self.load_context()
        self._apply_theme(context)
        renderer = self.create_renderer(context)
        renderer.animar_top_completo(self)

    def load_context(self) -> TopRenderContext:
        return build_context_from_env()

    def create_renderer(self, context: TopRenderContext) -> TopComposer:
        return TopComposer(context)

    def ingreso_titulo_top(
        self,
        objeto: Mobject,
        destino: Mobject,
        *,
        shift: Iterable[float] = (0.0, TopStyle.title_entry_shift_y, 0.0),
        entrada_time: float = TopStyle.title_entry_time,
        hold_time: float = TopStyle.title_hold_time,
        traslado_time: float = TopStyle.title_header_time,
        entrada_rate_func: Callable[[float], float] = smooth,
        traslado_rate_func: Callable[[float], float] = smooth,
    ) -> None:
        """Presenta el título centrado y lo traslada a su cabecera final."""
        if not isinstance(objeto, Mobject) or not isinstance(destino, Mobject):
            raise TypeError("objeto y destino deben ser Mobject")
        for nombre, valor in (
            ("entrada_time", entrada_time),
            ("traslado_time", traslado_time),
        ):
            if not math.isfinite(valor) or valor <= 0:
                raise ValueError(f"{nombre} debe ser finito y mayor que 0")
        if not math.isfinite(hold_time) or hold_time < 0:
            raise ValueError("hold_time debe ser finito y no negativo")
        if not callable(entrada_rate_func) or not callable(traslado_rate_func):
            raise TypeError("las rate functions deben ser callables")
        shift_v = np.asarray(tuple(float(v) for v in shift), dtype=float)
        if shift_v.shape != (3,) or not np.all(np.isfinite(shift_v)):
            raise ValueError("shift debe ser un vector de 3 componentes finitas")
        self.play(
            FadeIn(objeto, shift=shift_v, rate_func=entrada_rate_func),
            run_time=entrada_time,
        )
        if hold_time:
            self.wait(_quantize_wait(hold_time))
        self.play(
            Transform(objeto, destino, rate_func=traslado_rate_func),
            run_time=traslado_time,
        )

    def revelar_top(
        self,
        objects: Iterable[Mobject],
        *,
        opacity: float = TopStyle.reveal_opacity,
        run_time: float = TopStyle.reveal_time,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        """Restaura en una sola animación la opacidad de todos los objetos."""
        sequence = tuple(objects)
        if not sequence:
            return
        if not all(isinstance(mob, Mobject) for mob in sequence):
            raise TypeError("todos los objetos a revelar deben ser Mobject")
        if not math.isfinite(opacity) or not 0 <= opacity <= 1:
            raise ValueError("opacity debe ser finito y estar en [0, 1]")
        if not math.isfinite(run_time) or run_time <= 0:
            raise ValueError("run_time debe ser finito y mayor que 0")
        if not callable(rate_func):
            raise TypeError("rate_func debe ser callable")
        self.play(
            *[
                mob.animate(rate_func=rate_func).set_opacity(opacity)
                for mob in sequence
            ],
            run_time=run_time,
        )

    def espera_final_top(
        self,
        duration: float,
        *,
        min_frames: int = TopStyle.final_min_frames,
    ) -> None:
        """Mantiene el ranking final al menos ``min_frames``."""
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("duration debe ser finito y no negativo")
        if isinstance(min_frames, bool) or not isinstance(min_frames, int):
            raise TypeError("min_frames debe ser un entero")
        if min_frames < 1:
            raise ValueError("min_frames debe ser al menos 1")
        self.wait(_quantize_wait(max(duration, min_frames / config.frame_rate)))

    def play_scale_wave(
        self,
        objects: Iterable[Mobject],
        *,
        scale_factor: float = TopStyle.wave_scale_factor,
        transition_time: float = TopStyle.wave_transition_time,
        hold_time: float = TopStyle.wave_hold_time,
        between_items_time: float = TopStyle.wave_between_items_time,
        repetitions: int = TopStyle.wave_repetitions,
        reverse: bool = TopStyle.wave_reverse,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        """Recorre objetos con un pulso de escala para producir una ola.

        Cada objeto aumenta hasta ``scale_factor``, permanece ampliado durante
        ``hold_time`` y vuelve a su escala anterior. Recién entonces avanza al
        siguiente objeto, opcionalmente esperando ``between_items_time``.

        Args:
            objects: Objetos Manim en el orden recorrido por la ola.
            scale_factor: Multiplicador máximo; debe ser mayor que ``1``.
            transition_time: Segundos de cada tramo, tanto aumento como vuelta.
            hold_time: Segundos que cada objeto permanece en tamaño máximo.
            between_items_time: Pausa entre un objeto y el siguiente. Un valor
                menor hace que los saltos de la ola sean más rápidos.
            repetitions: Cantidad de recorridos completos.
            reverse: Recorre la secuencia desde el último objeto.
            rate_func: Curva Manim aplicada a ambos tramos de escala.

        La escala final se restaura mediante el factor recíproco. La función no
        altera posiciones, opacidades ni el orden de los objetos.
        Las pausas (``hold_time``, ``between_items_time``) se cuantizan a
        frames: un valor mayor que 0 pero menor a un frame se eleva a 1 frame.

        Ver también :meth:`play_zoom_pulse`, la variante con dwell largo y sin
        pausa entre objetos.
        """
        sequence = _validar_pulsos_escala(
            objects,
            scale_factor,
            transition_time,
            hold_time,
            between_items_time,
            repetitions,
            rate_func,
        )
        _recorrer_pulsos_escala(
            self,
            sequence,
            scale_factor=scale_factor,
            transition_time=transition_time,
            hold_time=hold_time,
            between_items_time=between_items_time,
            repetitions=repetitions,
            reverse=reverse,
            rate_func=rate_func,
        )

    def play_zoom_pulse(
        self,
        objects: Iterable[Mobject],
        *,
        scale_factor: float = TopStyle.zoom_scale_factor,
        transition_time: float = TopStyle.zoom_transition_time,
        hold_time: float = TopStyle.zoom_hold_time,
        rate_func: Callable[[float], float] = smooth,
    ) -> None:
        """Zoom de cada objeto: crece, permanece ampliado y vuelve.

        Variante deliberada de la ola: cada objeto se agranda hasta
        ``scale_factor``, se mantiene ``hold_time`` (dwell) y regresa a su
        escala original antes de pasar al siguiente. Sin pausa entre objetos y
        con un único recorrido por defecto, pensado para destacar tarjetas una
        por una.

        Args:
            objects: Objetos Manim en el orden del zoom.
            scale_factor: Multiplicador máximo; debe ser mayor que ``1``.
            transition_time: Segundos de cada tramo, tanto aumento como vuelta.
            hold_time: Segundos que cada objeto permanece ampliado (dwell).
            rate_func: Curva Manim aplicada a ambos tramos de escala.

        La escala final se restaura con el factor recíproco; las pausas se
        cuantizan a frames igual que en :meth:`play_scale_wave`.
        """
        sequence = _validar_pulsos_escala(
            objects,
            scale_factor,
            transition_time,
            hold_time,
            0.0,
            1,
            rate_func,
        )
        _recorrer_pulsos_escala(
            self,
            sequence,
            scale_factor=scale_factor,
            transition_time=transition_time,
            hold_time=hold_time,
            between_items_time=0.0,
            repetitions=1,
            reverse=False,
            rate_func=rate_func,
        )

    def ingreso_tarjeta_puesto(
        self,
        puesto: int,
        objeto: Mobject,
        destino: Mobject | None = None,
        *,
        atenuar_entrada: Iterable[Mobject] = (),
        opacidad_entrada: float = TopStyle.card_entry_dim_opacity,
        atenuar_vuelo: Iterable[tuple[Mobject, float]] = (),
        restaurar_vuelo: Iterable[Mobject] = (),
        opacidad_restaurar: float = TopStyle.card_restore_opacity,
        pulso: float = 0.0,
        pulso_time: float = TopStyle.card_highlight_pulse_time,
        shift: Iterable[float] = (0.0, TopStyle.card_entry_shift_y, 0.0),
        entrada_time: float = TopStyle.card_entry_time,
        espera_time: float = TopStyle.card_hold_time,
        vuelo_time: float = TopStyle.card_flight_time,
        vuelo_move_ratio: float = TopStyle.card_flight_move_ratio,
        entrada_rate_func: Callable[[float], float] = smooth,
        vuelo_rate_func: Callable[[float], float] = smooth,
        pulso_rate_func: Callable[[float], float] = there_and_back,
    ) -> Mobject:
        """Entrada animada de una tarjeta del ranking en su puesto.

        Tres fases: la tarjeta aparece desde abajo (``FadeIn`` con ``shift``)
        mientras ``atenuar_entrada`` baja a ``opacidad_entrada``; luego vuela
        como bloque estable hacia el slot y hace un crossfade a ``destino``.
        Durante el vuelo, ``atenuar_vuelo`` fija opacidades por objeto y
        ``restaurar_vuelo`` vuelve a ``opacidad_restaurar``. Con ``pulso``
        mayor que 1, el destino aterriza con un pulso ``there_and_back``.

        Args:
            puesto: Puesto 1-indexado de la tarjeta; solo informativo para
                errores y trazabilidad de la animación.
            objeto: Tarjeta que ingresa.
            destino: Forma final (slot) del vuelo; ``None`` saltea el vuelo.
            atenuar_entrada: Objetos que se atenúan al aparecer la tarjeta.
            opacidad_entrada: Opacidad final de los atenuados en la entrada.
            atenuar_vuelo: Pares ``(objeto, opacidad)`` fijados en el vuelo.
            restaurar_vuelo: Objetos restaurados a ``opacidad_restaurar``.
            opacidad_restaurar: Opacidad de los restaurados en el vuelo.
            pulso: Factor del pulso de aterrizaje; ``0`` lo deshabilita.
            pulso_time: Duración del pulso en segundos.
            shift: Vector de desplazamiento de la entrada.
            entrada_time: Duración de la entrada en segundos.
            espera_time: Pausa entre entrada y vuelo; ``0`` la saltea.
            vuelo_time: Duración del vuelo en segundos.
            vuelo_move_ratio: Fracción de ``vuelo_time`` dedicada al movimiento;
                el resto se usa para el crossfade al slot final.
        """
        params = _validar_ingreso_tarjeta(
            puesto,
            objeto,
            destino,
            atenuar_entrada,
            opacidad_entrada,
            atenuar_vuelo,
            restaurar_vuelo,
            opacidad_restaurar,
            pulso,
            pulso_time,
            shift,
            entrada_time,
            espera_time,
            vuelo_time,
            vuelo_move_ratio,
            entrada_rate_func,
            vuelo_rate_func,
            pulso_rate_func,
        )
        return _animar_ingreso_tarjeta(
            self,
            objeto,
            destino,
            params,
        )

    def _apply_theme(self, context: TopRenderContext) -> None:
        name = context.style.theme_name
        if name == "theme_agente32":
            self.theme = AGENTE32
        elif name == "theme_default":
            self.theme = DEFAULT
        else:
            # Fallback a default si theme desconocido (validación previa debería fallar)
            self.theme = DEFAULT
        # Aplicar background del theme inmediatamente
        self.camera.background_color = self.theme.background  # type: ignore[attr-defined]
