#!/usr/bin/env python3
"""Genera fondos limpios reutilizables para posts.

Los fondos se guardan en `tenants/<id>/assets/backgrounds/`, sin texto,
logos ni marcas. Cada imagen pasa por Vision QA; si falla, se regenera hasta
3 veces y la cuarta evaluación detiene el proceso.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from noticia_carrusel.providers import ImageProviderError, OpenRouterImageProvider  # noqa: E402
from noticia_carrusel.tenant import load_tenant  # noqa: E402
from noticia_carrusel.web_capture.vision import check_screenshot  # noqa: E402

DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1350
MAX_RETRIES = 3

PROMPTS = (
    (
        "bg_01_neural-network",
        "Abstract editorial background about artificial intelligence: luminous neural network graph, deep navy and electric blue palette with small lime accents, layered depth, clean negative space in the lower third for a news headline, premium technology magazine style, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_02_data-center",
        "Editorial technology background: futuristic AI data center aisle with server racks and soft cyan light, dark navy shadows, subtle lime highlights, strong perspective, clean negative space in the lower third for text, realistic high-end photography, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_03_robotic-arm",
        "Editorial robotics background: precision robotic arm working in a modern research laboratory, cobalt blue and graphite environment, controlled lime rim light, subject placed away from the lower third, clean composition for a news post, realistic cinematic photography, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_04_humanoid-robot",
        "Editorial robotics background: elegant humanoid robot silhouette in a dark research facility, blue volumetric light and restrained lime accents, face and central subject above the lower text area, atmospheric but uncluttered, realistic technology photography, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_05_biotech-lab",
        "Editorial science background: close-up of a microscope and glass laboratory instruments in a clean biotech lab, deep blue shadows, cyan reflections, small lime accent light, clear negative space in the lower third, realistic scientific photography, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_06_quantum-computing",
        "Abstract editorial science background: futuristic quantum computing laboratory with glowing cryogenic equipment and subtle particle-like light, deep navy, cyan and lime palette, layered depth, no central clutter in the lower third, premium magazine visual, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_07_space-satellite",
        "Editorial space science background: communications satellite orbiting above a blue atmospheric horizon with stars, dark navy space, cyan light and restrained lime highlight, strong subject in upper half, clean lower third for text, realistic cinematic photography, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_08_cybersecurity",
        "Editorial cybersecurity background: abstract secure digital infrastructure with glowing blue pathways and a protected central data core, dark navy and graphite, lime warning accents used sparingly, no readable interface text, clean lower third for a headline, premium technology visual, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_09_autonomous-vehicle",
        "Editorial autonomous mobility background: sleek sensor-equipped vehicle moving through a modern city at blue hour, cyan reflections, dark graphite road, subtle lime light trail, vehicle and important details kept above lower text area, realistic technology photography, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_10_materials-science",
        "Editorial materials science background: macro view of layered advanced material fibers and metallic surfaces, deep blue and graphite tones with electric cyan and lime highlights, tactile depth, uncluttered lower third for text, abstract realistic scientific photography, no text, no letters, no logos, no watermark",
    ),
    (
        "bg_11_astra-cybersecurity",
        "Editorial background for a frontier AI cybersecurity model: abstract autonomous cyber-defense intelligence core surrounded by controlled blue data arcs, deep navy and graphite field with restrained electric cyan and lime accents, subtle warm orange glow, important central object kept above the lower third for a headline, premium technology magazine visual, no text, no letters, no logos, no watermark",
    ),
)

NEGATIVE_PROMPT = "text, typography, letters, numbers, logo, brand mark, watermark, UI, labels, captions, distorted objects, duplicated objects, malformed geometry, blurry, low resolution, oversaturated, visual noise"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera fondos IA reutilizables para posts")
    parser.add_argument("--tenant", help="Tenant activo; default desde TENANT/DEFAULT_TENANT")
    parser.add_argument("--model", help="Modelo OpenRouter; default OPENROUTER_IMAGE_QUALITY_HIGH_MODEL")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--force", action="store_true", help="Regenerar aunque el PNG ya exista")
    parser.add_argument("--only", type=int, nargs="+", metavar="N", help="Generar solo los índices indicados (1-11)")
    return parser.parse_args()

def _model_from_env() -> str:
    model = os.environ.get("OPENROUTER_IMAGE_QUALITY_HIGH_MODEL", "").strip()
    if not model:
        raise ImageProviderError(
            "Falta --model o OPENROUTER_IMAGE_QUALITY_HIGH_MODEL para generar fondos"
        )
    return model


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.width < 320 or args.height < 320:
        print("Error: width y height deben ser >= 320", file=sys.stderr)
        return 1
    selected = set(args.only or range(1, len(PROMPTS) + 1))
    invalid = sorted(index for index in selected if index < 1 or index > len(PROMPTS))
    if invalid:
        print(f"Error: índices inválidos: {invalid}; disponibles 1-{len(PROMPTS)}", file=sys.stderr)
        return 1

    try:
        tenant = load_tenant(args.tenant)
        model = args.model or _model_from_env()
        output_dir = tenant.resolve_inside(tenant.assets_dir, "backgrounds")
        output_dir.mkdir(parents=True, exist_ok=True)
        provider = OpenRouterImageProvider(timeout=float(os.environ.get("OPENROUTER_IMAGE_TIMEOUT", "180")))
    except (FileNotFoundError, ValueError, OSError, ImageProviderError) as exc:
        print(f"Error inicializando generador: {exc}", file=sys.stderr)
        return 1

    run_entries: list[dict] = []
    review_entries: list[dict] = []
    for index, (slug, prompt) in enumerate(PROMPTS, start=1):
        if index not in selected:
            continue
        output_path = tenant.resolve_inside(output_dir, f"{slug}.png")
        if output_path.is_file() and not args.force:
            print(f"Reusado: {output_path}")
            with Image.open(output_path) as cached_image:
                actual_size = list(cached_image.size)
            run_entries.append({"index": index, "path": str(output_path), "reused": True, "cost_usd": None, "actual_size": actual_size})
            continue

        attempts: list[dict] = []
        total_cost = 0.0
        clean = False
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                result = provider.generate(
                    prompt=prompt,
                    negative_prompt=NEGATIVE_PROMPT,
                    model=model,
                    width=args.width,
                    height=args.height,
                    output_path=output_path,
                )
                cost = result.cost_usd
                if cost is not None:
                    total_cost += cost
                vision = check_screenshot(result.path)
                entry = {
                    "attempt": attempt,
                    "clean": vision.clean,
                    "issues": vision.issues,
                    "confidence": vision.confidence,
                    "cost_usd": cost,
                }
                attempts.append(entry)
                if vision.clean:
                    clean = True
                    break
                if attempt <= MAX_RETRIES:
                    print(f"Vision QA rechazó {slug} (intento {attempt}/4): {vision.issues}; regenerando")
                else:
                    print(f"Vision QA rechazó {slug} en la cuarta evaluación: {vision.issues}", file=sys.stderr)
            except (ImageProviderError, OSError, ValueError) as exc:
                print(f"Error generando {slug} en intento {attempt}: {exc}", file=sys.stderr)
                return 1

        status = "passed" if clean else "stopped_after_3_retries"
        with Image.open(output_path) as generated_image:
            actual_size = list(generated_image.size)
        review_entries.append({"index": index, "path": str(output_path), "attempts": attempts, "status": status, "actual_size": actual_size})
        run_entries.append({"index": index, "path": str(output_path), "reused": False, "cost_usd": total_cost, "actual_size": actual_size})
        if not clean:
            print("Se detiene la generación: un fondo no pasó Vision QA tras 3 reintentos.", file=sys.stderr)
            _write_json(output_dir / "vision_review.json", {"generated_at": dt.datetime.now().isoformat(), "items": review_entries})
            return 1
        print(f"Generado: {output_path}")

    total = sum(entry["cost_usd"] or 0.0 for entry in run_entries)
    manifest_path = output_dir / "manifest.json"
    previous_items: dict[int, dict] = {}
    if manifest_path.is_file():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous_items = {
                int(item["index"]): item
                for item in previous.get("items", [])
                if isinstance(item, dict) and "index" in item
            }
        except (OSError, ValueError, TypeError):
            previous_items = {}
    previous_items.update({int(item["index"]): item for item in run_entries})
    all_items = [previous_items[index] for index in sorted(previous_items)]
    collection_cost = sum(item.get("cost_usd") or 0.0 for item in all_items)
    _write_json(
        manifest_path,
        {
            "generated_at": dt.datetime.now().isoformat(),
            "tenant": tenant.id,
            "model": model,
            "requested_size": {"width": args.width, "height": args.height},
            "negative_prompt": NEGATIVE_PROMPT,
            "items": all_items,
            "run_cost_usd": total,
            "collection_cost_usd": collection_cost,
        },
    )
    print(f"Fondos listos: {len(run_entries)}")
    print(f"Costo real de esta corrida: ${total:.4f} USD")
    print(f"Manifest: {output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
