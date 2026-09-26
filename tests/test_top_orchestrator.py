from __future__ import annotations

from types import SimpleNamespace

from noticia_carrusel.video_generators.top.composer import TopComposer


def test_animar_top_completo_calls_every_stage_in_order() -> None:
    composer = object.__new__(TopComposer)
    composer.spec = SimpleNamespace(items=("primero", "segundo"))
    calls: list[tuple] = []
    scene = object()

    composer.configurar_layout = lambda value: calls.append(("layout", value))
    composer.agregar_audio = lambda value: calls.append(("audio", value))
    composer.agregar_fondo = lambda value: calls.append(("fondo", value))
    composer.agregar_footer = lambda value: calls.append(("footer", value))
    composer.animar_titulo = lambda value: calls.append(("titulo", value))
    composer.animar_tarjeta_puesto = (
        lambda value, puesto, item: calls.append(("tarjeta", value, puesto, item))
    )
    composer.animar_cierre = lambda value: calls.append(("cierre", value))

    composer.animar_top_completo(scene)

    assert calls == [
        ("layout", scene),
        ("audio", scene),
        ("fondo", scene),
        ("footer", scene),
        ("titulo", scene),
        ("tarjeta", scene, 2, "segundo"),
        ("tarjeta", scene, 1, "primero"),
        ("cierre", scene),
    ]
