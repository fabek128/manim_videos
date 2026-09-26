from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from noticia_carrusel.news_generator import (
    NewsFactAnalysis,
    NewsOption,
    SearchNewsAnalysis,
    SearchResult,
    SourceFetchError,
    VisualReviewStoppedError,
    VisionReviewRecord,
    _SearchParser,
    _format_spec,
    analyze_single_source,
    build_config,
    create_project,
    review_visual_outputs,
    slugify,
    validate_http_url,
)
from noticia_carrusel.tenant import (
    BrandManifest,
    InstagramManifest,
    PublishManifest,
    SocialManifest,
    TenantContext,
    TenantManifest,
)


def _tenant(tmp_path: Path) -> TenantContext:
    root = tmp_path / "tenant"
    root.mkdir()
    manifest = TenantManifest(
        id="testtenant",
        name="Test Tenant",
        brand=BrandManifest(logo="logos/agente32/agente32.svg"),
        social=SocialManifest(instagram=InstagramManifest(handle="test")),
        publish=PublishManifest(namespace="test"),
    )
    return TenantContext(id="testtenant", root=root, manifest=manifest)


def test_validate_http_url_rejects_non_http_and_private_hosts():
    with pytest.raises(ValueError):
        validate_http_url("file:///tmp/private.txt")
    with pytest.raises(ValueError):
        validate_http_url("ftp://example.com/file")
    with pytest.raises(ValueError):
        validate_http_url("http://127.0.0.1:8000/private")


def test_slugify_is_safe_and_kebab_case():
    assert slugify("Nuevo modelo de IA: versión 2") == "nuevo-modelo-de-ia-version-2"
    assert slugify("   ") == "noticia"


def test_search_parser_extracts_ddg_result_urls():
    parser = _SearchParser()
    parser.feed(
        '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa">Título A</a>'
        '<a class="result__snippet">Resumen A</a>'
        '<a class="result__a" href="https://example.com/b">Título B</a>'
        '<a class="result__snippet">Resumen B</a>'
    )
    assert [item.url for item in parser.results] == ["https://example.com/a", "https://example.com/b"]
    assert parser.results[0].title == "Título A"


def test_format_spec_supports_three_workloads():
    assert _format_spec("short") == ("post_vertical", "cover")
    assert _format_spec("long") == ("post_vertical", "text")
    assert _format_spec("carousel3") == ("carousel_vertical", "carousel3")
    assert _format_spec("carousel5") == ("carousel_vertical", "carousel5")
    assert _format_spec("story_complete") == ("story", "text")


def test_analyze_single_source_parses_promptgate_json(monkeypatch):
    from noticia_carrusel import news_generator

    payload = {
        "fact": "OpenAI publicó un reporte",
        "headline": "OPENAI PUBLICA UN REPORTE",
        "description": "Reporte sobre un incidente",
        "development": "El documento describe el incidente.",
        "actors": ["OpenAI"],
        "date": "2026-08-26",
        "status": "confirmado",
        "why_it_matters": "Aporta contexto técnico.",
        "unconfirmed": [],
        "contradictions": [],
    }
    monkeypatch.setattr(news_generator, "_call_ai", lambda *args, **kwargs: json.dumps(payload))
    source = news_generator.ResearchSource(url="https://example.com", title="Fuente", text="Datos")
    result = analyze_single_source(source)
    assert result.headline == payload["headline"]
    assert result.status == "en_curso"
    assert result.unconfirmed


def test_build_config_writes_web_capture_config(tmp_path):
    tenant = _tenant(tmp_path)
    fact = NewsFactAnalysis(
        fact="OpenAI publicó un reporte",
        headline="OpenAI publica un reporte",
        description="Detalle breve",
        development="Desarrollo de la noticia.",
        actors=["OpenAI"],
        status="confirmado",
        why_it_matters="Importa por seguridad.",
    )
    path = build_config(
        tenant,
        "2026-09-02_demo",
        fact,
        "long",
        "https://example.com/news",
        "screenshot",
        ["logos/openai/openai_black.svg"],
    )
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "vision_check: true" in text
    assert "type: text" in text
    assert "content_slug: 2026-09-02_demo" in text


def test_review_visual_outputs_stops_after_three_retries(tmp_path):
    image_path = tmp_path / "slide.png"
    Image.new("RGB", (20, 20), "white").save(image_path)
    calls = {"regenerate": 0, "review": 0}

    def regenerate():
        calls["regenerate"] += 1
        return [image_path]

    def review(path: Path, attempt: int) -> VisionReviewRecord:
        calls["review"] += 1
        return VisionReviewRecord(
            attempt=attempt,
            clean=False,
            issues=["texto tapa rostro"],
            confidence=0.9,
            status="pending",
        )

    with pytest.raises(VisualReviewStoppedError, match="3 reintentos"):
        review_visual_outputs(
            [image_path], regenerate, review=review, record_path=tmp_path / "vision_review.json"
        )
    assert calls["review"] == 4
    assert calls["regenerate"] == 3
    data = json.loads((tmp_path / "vision_review.json").read_text(encoding="utf-8"))
    assert data["status"] == "stopped_after_3_retries"


def test_review_visual_outputs_passes_first_attempt(tmp_path):
    image_path = tmp_path / "slide.png"
    Image.new("RGB", (20, 20), "white").save(image_path)

    def review(path: Path, attempt: int) -> VisionReviewRecord:
        return VisionReviewRecord(attempt=attempt, clean=True, confidence=0.95, status="pending")

    paths = review_visual_outputs(
        [image_path], lambda: [image_path], review=review, record_path=tmp_path / "vision_review.json"
    )
    assert paths == [image_path]
    data = json.loads((tmp_path / "vision_review.json").read_text(encoding="utf-8"))
    assert data["status"] == "passed"


def test_search_analysis_requires_options():
    with pytest.raises(Exception):
        SearchNewsAnalysis(options=[])
    option = NewsOption(
        id=1,
        angle="Seguridad",
        headline="OpenAI frena entrenamiento",
        description="Descripción",
        development="Desarrollo",
        why_it_matters="Impacto",
    )
    analysis = SearchNewsAnalysis(options=[option])
    assert analysis.options[0].id == 1




def test_create_project_level2_without_selection_only_writes_report(tmp_path, monkeypatch):
    from noticia_carrusel import news_generator

    tenant = _tenant(tmp_path)
    source = news_generator.ResearchSource(
        url="https://example.com/news",
        title="Fuente local",
        text="Contenido de prueba",
        source_type="primaria",
    )
    option = NewsOption(
        id=1,
        angle="Seguridad",
        headline="OPENAI PAUSA SU IA",
        description="Descripción breve",
        development="Desarrollo verificable",
        why_it_matters="Impacto concreto",
        actors=["OpenAI"],
        status="en_curso",
        source_urls=[source.url],
    )
    monkeypatch.setattr(news_generator, "fetch_source", lambda url: source)
    monkeypatch.setattr(
        news_generator,
        "analyze_search",
        lambda topic, sources, level: SearchNewsAnalysis(options=[option]),
    )

    project, config = create_project(
        tenant=tenant,
        level=2,
        url=None,
        topic="nuevo modelo de OpenAI",
        format_name="short",
        visual="solid",
        select=None,
        search_fn=lambda topic, limit: [SearchResult(source.url, source.title, "snippet")],
    )

    assert config is None
    assert (project / "informe.md").is_file()
    assert (project / "brief.md").is_file()
    assert not (project / "post.txt").exists()
def test_fetch_source_error_type_is_specific():
    assert issubclass(SourceFetchError, RuntimeError)
