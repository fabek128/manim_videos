# Logo @fabian128k

## Archivos

| Archivo | Qué es |
|---|---|
| `fabian128k_src.svg` | Fuente editable: texto "Hiragino Maru Gothic ProN" 13px, fill `#ffffff` |
| `fabian128k_paths.svg` | Versión lista para Manim: texto convertido a curvas, stroke:none forzado |

## Por qué

`SVGMobject` de Manim no soporta `<text>`; hay que convertir a curvas con Inkscape
(`--export-text-to-path`) y forzar `stroke:none` para evitar strokes residuales.
Mismo procedimiento que `../agente32/README.md`.

## Regenerar desde la fuente

```bash
/Applications/Inkscape.app/Contents/MacOS/inkscape \
  --export-type="svg" --export-text-to-path \
  --export-filename=/tmp/fabian128k_paths_raw.svg fabian128k_src.svg
python3 -c "
import re
src = open('/tmp/fabian128k_paths_raw.svg').read()
def clean(m):
    style = re.sub(r'(stroke-width|paint-order):[^;\\\"]*;?', '', m.group(1))
    return f'style=\"stroke:none;{style}\"'
open('fabian128k_paths.svg', 'w').write(re.sub(r'style=\"([^\"]*)\"', clean, src))
"
```

## Uso en escenas

```python
logo = SVGMobject(Path(__file__).parents[2] / "assets" / "logos" / "fabian128k" / "fabian128k_paths.svg")
```

Un solo VMobject (todo el texto es un path), fill `#CCFF00`, proporción ~7.8:1.
