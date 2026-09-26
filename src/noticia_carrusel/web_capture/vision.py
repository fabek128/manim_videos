"""Validación visual de screenshots con un modelo de visión (LLM).

Detecta publicidad, banners, popups, cookie banners, paywalls, 404,
captchas y artefactos de render antes de que la captura se use como
fondo de un post/video. Ver `docs/web-capture-plan.md` Fase A6.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from .models import VisionCheckResult

logger = logging.getLogger(__name__)

PROMPT_V1 = """Analizá esta pieza final o frame de video ya compuesto. Respondé SOLO JSON válido con esta forma exacta:
{"clean": bool, "issues": ["..."], "confidence": 0.0-1.0}

Marcá clean=false si observás CUALQUIERA de estos problemas:
- publicidad, banners de suscripción, popups, modales, cookies o paywalls que ocupan área visible;
- errores 404/500, captchas, páginas en blanco, carga incompleta, fuentes rotas o artefactos de render;
- texto cortado, truncado, fuera del lienzo o invadiendo las zonas seguras superior/inferior de una pieza para redes;
- texto ilegible por tamaño, contraste insuficiente, solapamiento entre textos o jerarquía visual confusa;
- logos deformados, falsos, reemplazados por placeholders o monogramas cuando corresponde un logo de marca;
- texto o degradados que cubren ojos, boca, rostros, pantallas, gráficos, código, logos u otros objetos focales.

No marques superposición si el texto solo cubre torso, fondo decorativo o una zona oscura sin ocultar el objeto focal. No marques un logo como falso solo por ser monocromático: evaluá si conserva la geometría reconocible de la marca.

La línea blanca rectangular delimita exactamente el frame original; el relleno oscuro exterior es solo diagnóstico y no forma parte de la pieza. Usá esa línea como evidencia del límite real: un texto está cortado únicamente si sus glifos tocan o cruzan esa línea.

Antes de denunciar texto cortado, comprobá que algún glifo realmente intersecta o excede el borde blanco; no infieras recorte porque una línea esté cerca del borde. En un frame de transición, el elemento que está moviéndose, escalándose o fundiéndose puede ser pequeño de forma temporal: evaluá deformación, duplicación y recorte, pero no exijas que su texto transitorio sea legible. Estas excepciones no aplican al título, tarjetas estáticas ni ranking final.

Si está limpia, devolvé {"clean": true, "issues": [], "confidence": 0.95}.
Si está sucia, describí cada problema de forma concreta y breve en español, indicando su ubicación y evidencia visual cuando sea posible.
"""

DEFAULT_VISION_MODEL = "google/gemini-2.5-flash"
MAX_SIDE = 1920


def _prepare_image_b64(image: Image.Image | Path | bytes) -> str:
    if isinstance(image, Path):
        pil = Image.open(image).convert("RGB")
    elif isinstance(image, bytes):
        pil = Image.open(io.BytesIO(image)).convert("RGB")
    elif isinstance(image, Image.Image):
        pil = image.convert("RGB")
    else:
        raise ValueError(f"Tipo de imagen no soportado: {type(image)}")
    # Conserva la resolución de lectura y agrega un marco diagnóstico cuadrado:
    # algunos proveedores recortan internamente imágenes 9:16 y alucinan bordes.
    if max(pil.size) > MAX_SIDE:
        pil.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
    side = max(pil.size)
    canvas = Image.new("RGB", (side, side), (12, 16, 24))
    offset = ((side - pil.width) // 2, (side - pil.height) // 2)
    canvas.paste(pil, offset)
    ImageDraw.Draw(canvas).rectangle(
        (
            offset[0],
            offset[1],
            offset[0] + pil.width - 1,
            offset[1] + pil.height - 1,
        ),
        outline=(255, 255, 255),
        width=2,
    )
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def _resolve_vision_config() -> tuple[str | None, str | None, str | None]:
    """Devuelve (base_url, api_key, model) o (None, None, None) si no hay proveedor configurado."""
    # Preferencia 1: PromptGate con modelo de visión explícito
    pg_model = os.environ.get("PROMPTGATE_VISION_MODEL", "").strip()
    if pg_model:
        base = os.environ.get("PROMPTGATE_BASE_URL", "").strip().rstrip("/")
        if not base:
            logger.warning(
                "Vision QA: PROMPTGATE_VISION_MODEL definido pero falta PROMPTGATE_BASE_URL; se asume clean=true"
            )
            return None, None, None
        auth = os.environ.get("PROMPTGATE_AUTH", "none").strip().lower()
        key = os.environ.get("PROMPTGATE_API_KEY") if auth != "none" else None
        return base, key, pg_model
    # Preferencia 2: OpenRouter
    or_model = os.environ.get("OPENROUTER_VISION_MODEL", "").strip()
    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    or_base = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1").rstrip("/")
    if or_model and or_key:
        return or_base, or_key, or_model
    if or_key:
        # Default barato si hay key pero no modelo explícito
        return or_base, or_key, DEFAULT_VISION_MODEL
    return None, None, None


def _extract_json(text: str) -> dict:
    text = text.strip()
    # Quitar fences ```json ... ```
    if "```" in text:
        # Extraer primer bloque entre fences
        import re
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1).strip()
    # Fallback: buscar primer { y último }
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return json.loads(text)


def check_screenshot(
    image: Image.Image | Path | bytes,
    prompt_version: str = "v1",
) -> VisionCheckResult:
    """Analiza `image` con el rol de visión y devuelve `VisionCheckResult`.

    Si no hay proveedor de visión configurado o el llamado falla, hace
    fail-open: loguea un warning y devuelve `clean=True` (no bloquea el
    pipeline, ver Decision 9 en el plan).
    """
    b64 = _prepare_image_b64(image)
    base_url, api_key, model = _resolve_vision_config()
    if not model or not base_url:
        logger.warning("Vision QA sin proveedor configurado (PROMPTGATE_VISION_MODEL / OPENROUTER_VISION_MODEL); se asume clean=true")
        return VisionCheckResult(clean=True, issues=[], confidence=0.0, raw_response=None)

    prompt = PROMPT_V1 if prompt_version == "v1" else PROMPT_V1

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        # OpenRouter requiere estos headers para ranking
        if "openrouter" in base_url:
            headers["HTTP-Referer"] = "https://agentee32.local"
            headers["X-Title"] = "Agente E32 Vision QA"

    payload: dict = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        "max_tokens": 512,
        "temperature": 0.0,
    }

    # Primer intento sin response_format (más compatible)
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise ValueError("Respuesta de visión sin content")
        raw = content if isinstance(content, str) else json.dumps(content)
        data = _extract_json(raw)
        result = VisionCheckResult.model_validate({**data, "raw_response": raw})
        logger.info("Vision QA: clean=%s issues=%s confidence=%.2f model=%s", result.clean, result.issues, result.confidence, model)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("Vision QA falló (modelo=%s): %s — fail-open clean=true", model, exc)
        # No reintentar con response_format por simplicidad; fail-open
        return VisionCheckResult(clean=True, issues=[], confidence=0.0, raw_response=None)
