from __future__ import annotations

import ast
import json
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _load_generator_namespace(catalog_path: Path) -> tuple[dict, type]:
    """Extrae y ejecuta solo las funciones puras de selección de modelos.

    Evita importar noticia_carrusel.generator completo, que arrastra
    dependencias de Manim/Pillow que pueden no estar disponibles en CI.
    """
    source_path = Path(__file__).parents[1] / "src/noticia_carrusel/generator.py"
    source = source_path.read_text(encoding="utf-8")
    module = ast.parse(source)
    selected = [
        node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        and node.name in {"ModelEntry", "_load_model_catalog", "_select_model_for_category", "_model_for"}
    ]
    namespace = {
        "json": json,
        "random": random,
        "Path": Path,
        "dataclass": dataclass,
        "ImageProviderError": RuntimeError,
        "MODEL_CATALOG_PATH": catalog_path,
        "ImageGenerationConfig": type("ImageGenerationConfig", (), {"__init__": lambda self, model=None: setattr(self, "model", model)}),
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace, namespace["ImageGenerationConfig"]


def test_model_for_selects_weighted_model_from_category_jsonl():
    with tempfile.TemporaryDirectory() as td:
        catalogue = Path(td) / "models.jsonl"
        catalogue.write_text(
            "\n".join(
                json.dumps(item)
                for item in [
                    {"model": "draft-a", "categories": ["draft"], "weight": 0},
                    {"model": "draft-b", "categories": ["draft"], "weight": 1},
                    {"model": "high-a", "categories": ["high"], "weight": 1},
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        namespace, ImageGenerationConfig = _load_generator_namespace(catalogue)

        # Forzar selección determinista (el modelo con weight 0 nunca debe elegirse)
        original_choices = namespace["random"].choices
        namespace["random"].choices = lambda population, weights, k: [population[0]]
        try:
            assert namespace["_model_for"](ImageGenerationConfig(model="draft")) == "draft-b"
            assert namespace["_model_for"](ImageGenerationConfig(), quality="high") == "high-a"
        finally:
            namespace["random"].choices = original_choices


def test_model_for_uses_explicit_model_without_catalog():
    with tempfile.TemporaryDirectory() as td:
        catalogue = Path(td) / "models.jsonl"
        catalogue.write_text("", encoding="utf-8")  # catálogo vacío
        namespace, ImageGenerationConfig = _load_generator_namespace(catalogue)

        # Modelo explícito en el YAML se usa tal cual, sin consultar el catálogo
        assert namespace["_model_for"](ImageGenerationConfig(model="meta/muse-image")) == "meta/muse-image"
        assert (
            namespace["_model_for"](ImageGenerationConfig(model="openai/gpt-image-2.5-sunburst"))
            == "openai/gpt-image-2.5-sunburst"
        )


def test_model_for_raises_when_category_missing():
    with tempfile.TemporaryDirectory() as td:
        catalogue = Path(td) / "models.jsonl"
        catalogue.write_text(
            '{"model": "only-draft", "categories": ["draft"], "weight": 1}\n',
            encoding="utf-8",
        )
        namespace, ImageGenerationConfig = _load_generator_namespace(catalogue)

        # Categoría 'high' sin entradas debe fallar
        try:
            namespace["_model_for"](ImageGenerationConfig(), quality="high")
            raise AssertionError("Debía lanzar ImageProviderError para categoría vacía")
        except RuntimeError as exc:
            assert "high" in str(exc)


def test_production_catalogue_has_all_six_draft_models():
    catalogue = Path(__file__).parents[1] / "src/noticia_carrusel/image_models.jsonl"
    namespace, ImageGenerationConfig = _load_generator_namespace(catalogue)
    entries = namespace["_load_model_catalog"](catalogue)
    assert len(entries) == 6
    assert all("draft" in e.categories for e in entries)
    models = {e.model for e in entries}
    assert models == {
        "inclusionai/ming-image-0.1-design",
        "meta/muse-image",
        "recraft/recraft-v4.1-flash",
        "sourceful/riverflow-v2.5-fast",
        "bytedance-seed/seedream-5-0-pro",
        "openai/gpt-image-2.5-sunburst",
    }
