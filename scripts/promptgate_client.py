#!/usr/bin/env python3
"""Cliente mínimo OpenAI-compatible para PromptGate.

Uso:
    python scripts/promptgate_client.py --list-models
    python scripts/promptgate_client.py --model <id> --prompt "Hola"

La autenticación de PromptGate es explícitamente none: este cliente nunca
envía API keys ni cabecera Authorization.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL: str | None = None  # Sin default privado: exigir PROMPTGATE_BASE_URL
DEFAULT_TIMEOUT = 120.0
MAX_RESPONSE_BYTES = 16 * 1024 * 1024


def _load_dotenv(path: Path) -> None:
    """Carga pares simples KEY=VALUE sin sobrescribir el entorno existente."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _base_url() -> str | None:
    value = os.environ.get("PROMPTGATE_BASE_URL", "").strip().rstrip("/")
    if not value:
        raise ValueError(
            "Falta PROMPTGATE_BASE_URL en el entorno: definilo en .env o "
            "exportalo (ej: https://endpoint.example/v1) para usar PromptGate"
        )
    if not value.startswith(("http://", "https://")):
        raise ValueError("PROMPTGATE_BASE_URL debe usar http:// o https://")
    if "@" in value.split("://", 1)[1].split("/", 1)[0]:
        raise ValueError("PROMPTGATE_BASE_URL no debe contener credenciales")
    return value


def _timeout() -> float:
    try:
        value = float(os.environ.get("PROMPTGATE_TIMEOUT", DEFAULT_TIMEOUT))
    except ValueError as exc:
        raise ValueError("PROMPTGATE_TIMEOUT debe ser numérico") from exc
    if not 1 <= value <= 600:
        raise ValueError("PROMPTGATE_TIMEOUT debe estar entre 1 y 600 segundos")
    return value


def _request_json(path: str, payload: dict | None = None) -> dict:
    auth = os.environ.get("PROMPTGATE_AUTH", "none").strip().lower()
    if auth != "none":
        raise ValueError("PromptGate requiere PROMPTGATE_AUTH=none; no se envía auth")

    url = f"{_base_url()}/{path.lstrip('/')}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urlopen(request, timeout=_timeout()) as response:  # noqa: S310
            data = response.read(MAX_RESPONSE_BYTES + 1)
    except TimeoutError as exc:
        raise RuntimeError(
            f"PromptGate agotó el timeout de {_timeout():g} segundos en {path}"
        ) from exc
    except HTTPError as exc:
        raise RuntimeError(f"PromptGate respondió HTTP {exc.code} en {path}") from exc
    except URLError as exc:
        raise RuntimeError(f"No se pudo conectar con PromptGate en {url}: {exc.reason}") from exc
    if len(data) > MAX_RESPONSE_BYTES:
        raise RuntimeError("La respuesta de PromptGate supera el límite permitido")
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise RuntimeError("PromptGate devolvió una respuesta que no es JSON") from exc


def list_models() -> list[str]:
    response = _request_json("models")
    models = response.get("data")
    if not isinstance(models, list):
        raise RuntimeError("La respuesta /models no contiene data[]")
    ids = [item.get("id") for item in models if isinstance(item, dict)]
    return sorted(model_id for model_id in ids if isinstance(model_id, str) and model_id)

def chat(
    model: str,
    prompt: str,
    system: str | None = None,
    max_tokens: int | None = None,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    response = _request_json("chat/completions", payload)
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("La respuesta no contiene choices[]")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise RuntimeError("La respuesta no contiene choices[0].message")
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        return "".join(part for part in parts if isinstance(part, str))
    raise RuntimeError("La respuesta no contiene texto en message.content")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cliente OpenAI-compatible para PromptGate")
    parser.add_argument("--list-models", action="store_true", help="Descubre e imprime los modelos")
    parser.add_argument(
        "--model",
        help="ID exacto; por defecto usa PROMPTGATE_MODEL del .env",
    )
    parser.add_argument("--prompt", help="Prompt del usuario; si falta, se lee stdin")
    parser.add_argument("--system", help="Mensaje system opcional")
    return parser.parse_args()


def main() -> int:
    _load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    args = parse_args()
    try:
        if args.list_models:
            print("\n".join(list_models()))
            return 0
        model = args.model or os.environ.get("PROMPTGATE_MODEL")
        if not model:
            raise ValueError(
                "Debes indicar --model o definir PROMPTGATE_MODEL; "
                "usa --list-models para descubrir IDs"
            )
        prompt = args.prompt if args.prompt is not None else sys.stdin.read().strip()
        if not prompt:
            raise ValueError("Debes indicar --prompt o proporcionar un prompt por stdin")
        print(chat(model, prompt, args.system))
        return 0
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
