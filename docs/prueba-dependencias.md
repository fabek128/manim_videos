# Estado de dependencias — preparado para prueba

Fecha: 2026-10-08

## Estado: LISTO (alineado al requisito Python 3.12)

- Python 3.12.13 instalado mediante `uv python install 3.12`.
- `.venv` recreado con Python 3.12.13.
- Dependencias de proyecto y desarrollo instaladas con `uv sync --group dev`.
- Manim 0.21.0, OpenCV headless, Pillow, Pydantic, pytest, Playwright y Chromium instalados.

Verificación:
- `python -m pytest tests/ -q` → **142 passed, 1 warning**.
- Warning no bloqueante: `audioop` está deprecado en Python 3.12, emitido por `pydub`.

## Comandos para repetir

```bash
cd /home/fabian/code/redes2
source .venv/bin/activate
python -m pytest tests/ -q
```
