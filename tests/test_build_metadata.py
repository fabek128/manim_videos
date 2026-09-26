from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import build


def test_selected_background_metadata_preserves_explicit_config(monkeypatch) -> None:
    monkeypatch.setattr(build, "ACTIVE_TENANT", None)
    spec = SimpleNamespace(background_image_path="backgrounds/network.png")

    selected = build._selected_background_metadata(spec, {"seed": 42})

    assert selected == "backgrounds/network.png"


def test_selected_background_metadata_replays_seeded_pool(monkeypatch) -> None:
    tenant = object()
    monkeypatch.setattr(build, "ACTIVE_TENANT", tenant)

    def fake_select(received_tenant, rng):
        assert received_tenant is tenant
        return Path(f"bg_{rng.randrange(1000)}.png")

    monkeypatch.setattr(
        "noticia_carrusel.backgrounds.select_random_background",
        fake_select,
    )
    spec = SimpleNamespace(background_image_path=None)

    first = build._selected_background_metadata(spec, {"seed": 42})
    second = build._selected_background_metadata(spec, {"seed": 42})

    assert first == second
