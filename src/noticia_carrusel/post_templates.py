"""Carga de templates editoriales de `templates/posts/`.

Separado de `templates/prompts/` (diseño visual). Ver
`templates/posts/README.md` para el contrato de cada template.
"""

from __future__ import annotations

from pathlib import Path

from .tenant import POST_TEMPLATES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POSTS_TEMPLATES_DIR = PROJECT_ROOT / "templates" / "posts"


def load_post_template(name: str) -> str:
    """Devuelve el contenido de `templates/posts/<name>.md`.

    `name` debe ser uno de los nombres conocidos en `POST_TEMPLATES`
    (sin extensión, sin rutas). Cualquier otro valor —incluido `..` o
    una ruta absoluta— se rechaza antes de tocar el filesystem.
    """
    if name not in POST_TEMPLATES:
        known = ", ".join(sorted(POST_TEMPLATES))
        raise ValueError(f"Template de post desconocido: {name!r}; disponibles: {known}")
    path = POSTS_TEMPLATES_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Falta el archivo de template: {path}")
    return path.read_text(encoding="utf-8")


def list_post_templates() -> list[str]:
    return sorted(POST_TEMPLATES)
