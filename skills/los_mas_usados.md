# Skill: Los modelos que más usé esta semana

> **Carga automática**: se lee sola cuando la tarea es armar este video.
> Complementa (no reemplaza) `skills/global.md`, que también debe estar cargada.

Instrucción estándar para armar el video semanal de rankings de uso de modelos
de IA. Formato: countdown visual con logos, nombres y porcentajes de uso.

El usuario podra pedirte crear este tipo de videos de ranckings de distintas maneras como por ejemplo:
los tops
los mas
los mas usados
ranking de modelos

## 1. Parámetros a pedirle al usuario

Obligatorios — sin estos datos no se puede empezar:

| Parámetro | Qué es | Ejemplo |
|---|---|---|
| `modelos` | Lista de 5–10 modelos en orden de ranking (el #1 primero o último, confirmar) | GPT-5.2, Claude Opus 4.6, Gemini 3 Pro... |
| `uso` | Porcentaje o métrica por modelo (horas, % de prompts, $ gastado) | 42%, 18h, 310 prompts |
| `periodo` | Semana a mostrar en pantalla | "Semana del 17–23 ago" |
| `formato` | Reel/Story (9:16), post vertical (3:4) o cuadrado (1:1) | reel |

Opcionales (con defaults sensatos):

### Regla obligatoria al analizar un JSON

Cuando el usuario pida analizar un JSON de un top, leer el archivo real y
revisar tanto los datos como los textos visibles. Comprobar estructura, tipos,
campos obligatorios, valores faltantes o inválidos, orden del ranking, logos,
assets y URLs SVG.

Además, mejorar siempre la redacción de `titulo`, `subtitulo`, `comentario` y
etiquetas de `specs`: corregir ortografía, gramática, claridad, tono y
consistencia. No modificar ni inventar métricas, nombres, precios, fechas u
otros hechos; si falta un dato, señalarlo como pendiente de confirmación.

Si el usuario pide modificar el JSON, aplicar las mejoras directamente y
validar el JSON antes de renderizar.

| Parámetro | Default si no se pide |
|---|---|
| `metrica_label` | "% de uso" |
| `duracion_total` | 8–12s |
| `mostrar_barra` | true — barra proporcional junto a cada modelo |
| `estilo_entrada` | countdown desde el último puesto hasta el #1 |
| `musica` | ninguna (ver §4) |

## 2. Estructura del video (countdown)

```
[0.0s] Título: "LOS MODELOS QUE MÁS USÉ ESTA SEMANA" + periodo
[0.8s] Puesto N (último): logo + nombre + métrica + barra
[+0.7s] Puesto N-1 ... (cada entrada ~0.7s)
[...]  ...
[fin]  Puesto #1: entrada destacada (pulso 6% there_and_back, escala mayor)
```

- Duración total = título (0.8s) + N × 0.7s + cierre #1 (1.2s). Para 5 modelos ≈ 5.5s
- El #1 recibe tratamiento destacado: escala mayor, color `theme.accent`, pulso
- Barra proporcional: ancho ∝ métrica / métrica_max

## 3. Logos de los modelos

1. Chequear `assets/logos/<modelo>/` — si ya existe `_paths.svg`, usarlo
2. Si no existe:
   - Buscar el SVG oficial: press kit del vendor, Wikipedia (SVG de marca),
     worldvectorlogo/similar. Preferir SVG vectorial sobre PNG
   - Descargar → convertir texto a curvas con Inkscape (`--export-text-to-path`)
   - Sanitizar: `stroke:none`, remover `stroke-width`/`paint-order` residuales
   - Verificar import: `SVGMobject(...)` sin warnings, fills correctos
   - Guardar como `assets/logos/<nombre>/` con README de regeneración
3. Si un modelo no tiene logo disponible (muy nuevo/sin marca): usar monograma
   tipográfico con **Space Grotesk** (fuente de títulos del repo, ver
   `docs/fonts.md`) en `theme.primary` sobre chip `theme.dark`
4. Los logos van normalizados a altura común (~0.8u) alineados a la izquierda

## 4. Audio (opcional)

Manim soporta audio vía `self.add_sound("archivo.mp3", time_offset=..., gain=...)`.
Se llama en `construct()` y queda sincronizado al render final. Si el usuario pide
música:

- Pedir el archivo de audio y guardarlo en `assets/audio/`
- Un solo track de fondo: `self.add_sound(track, gain=-8)` al inicio
- SFX por puesto revelado: `self.add_sound("whoosh.mp3")` dentro del loop
- Alternativa post-render (más control): mezclar con ffmpeg
  `ffmpeg -i video.mp4 -i music.mp3 -map 0:v -map 1:a -c:v copy -shortest out.mp4`

## 5. Escena tipo (esqueleto)

```python
from pathlib import Path

from manim import *

from utils.theme import AGENTE32, ThemedScene

LOGOS_DIR = Path(__file__).parents[2] / "assets" / "logos"


class ModelosSemana(ThemedScene):
    theme = AGENTE32

    MODELOS = [  # (nombre, carpeta_logo, metrica) — completar con datos del usuario
        ("GPT-5.2", "openai", 42),
        ("Claude Opus 4.6", "anthropic", 31),
    ]
    PERIODO = "Semana del 17–23 ago"
    METRICA_LABEL = "% de uso"

    def construct(self):
        self._titulo()
        for i, (nombre, logo_dir, metrica) in enumerate(reversed(self.MODELOS)):
            self._fila(i + 1, nombre, logo_dir, metrica, destacado=(i == 0))

    def _fila(self, puesto, nombre, logo_dir, metrica, destacado):
        fila = VGroup()  # logo + nombre + barra + métrica
        # ... componer, posicionar, animar entrada ~0.7s
        ...
```

## 6. Checklist antes de entregar

- [ ] Datos del usuario confirmados (§1) — nunca inventar métricas
- [ ] Logos existentes reutilizados; nuevos sanitizados y documentados
- [ ] Render `-ql` verificado por frame (colores, orden del ranking legible)
- [ ] Duración total dentro de lo pedido
- [ ] Resolución correcta según formato elegido (`docs/instagram-formats.md`)
- [ ] Escena ya existente → render directo SIN preguntas (regla ⚡ AGENTS.md):
      `python build.py --video <nombre-que-dijo-el-usuario> --no-preview`
      (Reel default implícito; `-f post` para 3:4; `-o` abre al terminar)
- [ ] Escena nueva → confirmar datos §1 antes de escribir código, luego mismo comando
