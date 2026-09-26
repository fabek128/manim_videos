# Videos "Noticias de la semana"

Clon de `videos/lostops/` (generador de tops "Los más usados") adaptado a
formato **noticias**. Mismo motor 100% data-driven: un único `scene.py`
(`NoticiasSemana`) renderiza cualquier top de noticias a partir de un JSON.
Los datos viven en `json/`; el código no cambia de una tanda a otra.

> Este formato es intencionalmente muy similar a `lostops` (mismo layout,
> misma coreografía de countdown, mismas zonas muertas y footer). Se espera
> ir ajustando detalles particulares (etiquetas, datos por noticia, música,
> duración) más adelante sin tocar el motor.

## Uso

```bash
# Renderiza el JSON más reciente (orden por nombre de archivo):
python build.py --video noticias

# ...o con un JSON explícito:
TOP_JSON=videos/noticias/json/2026-08-30_top_noticias_semana.json \
    python build.py --video noticias

# Otro formato de salida (el scene detecta proporción y usa pila o grilla 2x2):
PYTHONPATH=. manim -qh -r 1080,1920 --fps 30 videos/noticias/scene.py NoticiasSemana
```

- `build.py --video noticias` mapea (fuzzy) a `videos/noticias/scene.py`.
- Manim nombra la carpeta de salida por la altura (`media/videos/scene/<hh>p<fps>/`);
  square y apaisado comparten `1080p30`, así que si renderizás ambos en una misma
  corrida conviene copiar el mp4 de inmediato.

## Formatos soportados (auto)

| Aspecto | Layout |
|---|---|
| Vertical (`fh > fw`, Reel 9:16) | pila de 4 slots |
| Cuadrado / apaisado (`fh ≤ fw`) | grilla 2×2 |

Los tamaños se anclan a **píxeles** (`ZONA_*_PX`, `slot_pad`, fonts escalarizados)
para que sean consistentes entre formatos.

Todos los slots tienen borde blanco de 2.5 px. El slot del puesto `#1`
usa borde amarillo (`ORO`); el color del borde depende del puesto, no del
campo opcional `destacado`.

## Esquema del JSON (`json/YYYY-MM-DD_<slug>.json`)

El nombre de archivo **debe** empezar con `YYYY-MM-DD` para que el orden
alfabético coincida con el orden cronológico (el último alfabéticamente = el
más nuevo = el que se renderiza por defecto).

```jsonc
{
  // 1..N líneas (se centran, bold, Space Grotesk)
  "titulo": ["LAS NOTICIAS QUE MÁS", "IMPORTARON ESTA SEMANA"],
  "subtitulo": "Semana del 24 al 30 de agosto",
  "noticias": [
    {
      "titular": "Nuevo modelo open-weight compite con los frontier",
      "logo": "deepseek",               // nombre de asset en assets/logos/ (fuente/medio)
      "logo_path": "...",               // (opcional) path local explícito, relativo al repo
      "fuente": "DeepSeek",             // (opcional) se inyecta como dato "Fuente"
      "destacado": true,                // (opcional) acentúa tarjeta y texto; borde #1 siempre amarillo
      "dato": { "etiqueta": "Fecha", "valor": "26 ago" },
      "resumen": ["línea 1", "línea 2"],
      "datos": [["Categoría", "Modelos"], ["Alcance", "1.2M lectores"]]
    }
    // …
  ]
}
```

Notas (mapeo respecto a `lostops`, para quien conoce ese schema):

| `lostops` | `noticias` | Significado |
|---|---|---|
| `modelos` | `noticias` | array de items del ranking |
| `nombre` | `titular` | título de la fila/tarjeta |
| `provider` | `fuente` | se inyecta como dato `("Fuente", …)` si no está ya en `datos` |
| `metrica` | `dato` | par `{etiqueta, valor}`; etiqueta por defecto `"Fecha"` (antes `"Tokens"`) |
| `comentario` | `resumen` | 1…N líneas, se muestra izquierda del slot |
| `specs` | `datos` | pares `[clave, valor]`, columna derecha del slot |

- `dato` puede ser `{etiqueta, valor}` o un valor simple (etiqueta asume `"Fecha"`).
- `resumen` admite 1…N líneas (se muestra izquierda del slot).
- `datos` son pares `[clave, valor]` (columna derecha del slot).
- No repetir `("Fuente", ...)` dentro de `datos` si ya usás el campo `fuente`.
- `logo` acepta un nombre en `assets/logos/<logo>/`; si no existe, se usa un
  monograma automático (inicial de `logo`) — no hace falta tener el logo del
  medio para probar el pipeline.
- `logo_path` mantiene el soporte para paths locales explícitos.

## Datos de ejemplo

`json/2026-08-30_top_noticias_semana.json` es un **fixture de prueba**, no
noticias reales: titulares plausibles pero genéricos, fechas ficticias
dentro del período declarado, y campos sin dato verificado marcados
`[SIN CONFIRMAR]`. Reemplazar por datos reales y confirmados antes de
publicar (ver regla de veracidad en `AGENTS.md` §5).

## Layout de la escena

Igual a `lostops` (el motor no cambió, solo los nombres de campo):

1. La tarjeta grande aparece dentro del carril seguro entre encabezado y footer.
   El encabezado permanece nítido y el ranking previo se oculta para evitar
   ghosting y solapamientos de capas.
2. 5 s de lectura por noticia antes de pasar a la siguiente.
   Entre cada noticia, `WAIT_TOP_NITIDO` (implícito en la coreografía) mantiene
   el ranking acumulado completamente nítido antes de iniciar la siguiente
   tarjeta.
3. La tarjeta vuela a su slot; las tarjetas anteriores permanecen ocultas
   durante el vuelo y reaparecen nítidas en la pausa siguiente.
4. Al terminar, el top entero se revela a plena opacidad.
5. Zonas muertas de 220 px arriba/abajo (UI de Instagram): nada de contenido.

En square y landscape la grilla usa margen lateral de `0.6u`, gutter de
`0.4u` y tipografía secundaria ampliada. Las tarjetas tienen una altura mínima
común para evitar que el puesto `#1` se perciba más pequeño por tener menos
contenido. El vuelo hacia el slot dura `1.0s`.

En formato vertical el hero se centra ligeramente hacia el footer para evitar
un vacío excesivo durante la entrada; square y landscape conservan centrado
geométrico.

Ajustes globales rápidos: `ZONA_SUP_PX`/`ZONA_INF_PX` (zonas muertas),
`slot_pad` (aire por item), `ORO` (color del borde del puesto #1).

## Pendiente de particularizar (a futuro)

Heredado tal cual de `lostops` por ahora, candidato a cambiar cuando el
formato noticias tenga su propia identidad:

- Música de fondo (`FM Attack - Footprints 2.mp3`, mismo track que `lostops`).
- Duración de lectura por noticia (5 s, igual que por modelo).
- Etiqueta por defecto del dato destacado (`"Fecha"`) — podría variar según
  el tipo de nota (fecha, alcance, categoría, etc.).
