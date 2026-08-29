# Logo AGENTE32

## Archivos

| Archivo | Qué es |
|---|---|
| `agente32.svg` | Fuente original (Inkscape, A4). Contiene `<text>` con fuentes Ethnocentric e Hiragino Maru Gothic ProN |
| `agente32_paths.svg` | Versión lista para Manim: texto convertido a curvas y strokes residuales removidos |

## Por qué existen dos versiones

`SVGMobject` de Manim **no soporta elementos `<text>`** (los descarta con un warning). Además, Inkscape deja `stroke-width` residuales grandes al exportar (ej. `stroke-width:217`) que Manim interpreta como strokes visibles gigantes.

## Regenerar `agente32_paths.svg` desde el original

```bash
# 1. Texto a curvas
/Applications/Inkscape.app/Contents/MacOS/inkscape \
  --export-type="svg" --export-text-to-path \
  --export-filename=/tmp/agente32_paths.svg agente32.svg

# 2. Remover stroke-width / paint-order residuales y forzar stroke:none
python3 -c "
import re
src = open('/tmp/agente32_paths.svg').read()
def clean(m):
    style = re.sub(r'(stroke-width|paint-order):[^;\"]*;?', '', m.group(1))
    return f'style=\"stroke:none;{style}\"'
open('agente32_paths.svg', 'w').write(re.sub(r'style=\"([^\"]*)\"', clean, src))
"
```

## Uso en escenas

```python
logo = SVGMobject(Path(__file__).parents[2] / "assets" / "logos" / "agente32" / "agente32_paths.svg")
```

Ejemplo de referencia: `videos/2026-08-24_logo_agente32/scene.py`.

## Estructura del logo

- Barra principal `#00112B` + chip `#F9F9F9`
- Texto "AGENT" `#CCFF00` (Ethnocentric) sobre la barra
- Texto "E32" `#374837` (Hiragino Maru Gothic ProN) sobre el chip
