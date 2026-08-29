from __future__ import annotations

import base64
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


class ImageProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImageGenerationResult:
    """Resultado de una llamada real a la API de imágenes."""

    path: Path
    model: str
    cost_usd: float | None
    """Costo reportado por `usage.cost` en la respuesta de OpenRouter.

    `None` cuando el proveedor no lo informó (nunca se inventa un valor).
    """


class OpenRouterImageProvider:
    """Cliente desacoplado para el endpoint de generación de imágenes."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 180.0):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = (base_url or os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")).rstrip("/")
        self.timeout = timeout
        if not self.api_key:
            raise ImageProviderError("Falta OPENROUTER_API_KEY")
        if not self.base_url.startswith(("http://", "https://")):
            raise ImageProviderError("OPENROUTER_API_BASE debe usar http:// o https://")

    def generate(
        self,
        prompt: str,
        output_path: Path,
        model: str,
        width: int,
        height: int,
        negative_prompt: str | None = None,
        seed: int | None = None,
        variations: int = 1,
    ) -> ImageGenerationResult:
        if not prompt.strip():
            raise ImageProviderError("El prompt de imagen no puede estar vacío")
        divisor = math.gcd(width, height)
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": variations,
            "aspect_ratio": f"{width // divisor}:{height // divisor}",
            "size": f"{width}x{height}",
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed
        try:
            response = requests.post(
                f"{self.base_url}/images",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://agentee32.local",
                    "X-Title": "Agente E32 Image Generator",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            suffix = f" HTTP {status}" if status else ""
            raise ImageProviderError(f"OpenRouter no pudo generar la imagen{suffix}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise ImageProviderError("OpenRouter no devolvió JSON") from exc
        data = body.get("data", [])
        if not data:
            raise ImageProviderError("OpenRouter no devolvió imágenes")
        item = data[0]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if item.get("b64_json"):
                output_path.write_bytes(base64.b64decode(item["b64_json"], validate=True))
            elif item.get("url"):
                image_response = requests.get(item["url"], timeout=self.timeout)
                image_response.raise_for_status()
                output_path.write_bytes(image_response.content)
            else:
                raise ImageProviderError("Respuesta de OpenRouter sin b64_json ni url")
        except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
            raise ImageProviderError("No se pudo guardar la imagen de OpenRouter") from exc

        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        cost = usage.get("cost")
        cost_usd = float(cost) if isinstance(cost, (int, float)) else None
        return ImageGenerationResult(path=output_path, model=model, cost_usd=cost_usd)
