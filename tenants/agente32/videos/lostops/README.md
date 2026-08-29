# Videos "Los más usados"

Generador de tops 100% **data-driven**: un único `scene.py` (`ModelosSemana`)
renderiza cualquier top a partir de un JSON. Los datos viven en `json/`; el
código no cambia de un top a otro.

## Uso

```bash
# Renderiza el JSON más reciente (orden por nombre de archivo):
python build.py --video lostops

# ...o con un JSON explícito:
TOP_JSON=videos/lostops/json/2026-08-23_modelos_semana.json \
    python build.py --video lostops

# Otro formato de salida (el scene detecta proporción y usa pila o grilla 2x2):
PYTHONPATH=. manim -qh -r 1080,1920 --fps 30 videos/lostops/scene.py ModelosSemana
```

- `build.py --video lostops` mapea (fuzzy) a `videos/lostops/scene.py`.
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
  "titulo": ["LOS MODELOS QUE MÁS", "USÉ ESTA SEMANA"],
  "subtitulo": "Semana del 17 al 23 ago",
  "modelos": [
    {
      "nombre": "GPT-5.2",
      "logo": "openai",                 // nombre de asset o URL HTTP(S) a un SVG
      "logo_path": "...",               // (opcional) path local explícito, relativo al repo
      "provider": "OpenAI",             // (opcional) se inyecta como spec "Provider"
      "destacado": true,                // (opcional) acentúa tarjeta y texto; borde #1 siempre amarillo
      "metrica": { "etiqueta": "Tokens", "valor": "412M" },
      "comentario": ["línea 1", "línea 2"],
      "specs": [["Context", "400K"], ["Modalidad", "texto+visión"]]
    }
    // …
  ]
}
```

Notas:
- `metrica` puede ser `{etiqueta, valor}` o un valor simple (etiqueta asume `"Tokens"`).
- `comentario` admite 1…N líneas (se muestra izquierda del slot).
- `specs` son pares `[clave, valor]` (columna derecha del slot).
- No repetir `("Provider", ...)` dentro de `specs` si ya usás `provider`.
- `logo` acepta un nombre en `assets/logos/<logo>/` o una URL `http://`/`https://` a un SVG.
  Las URLs se descargan durante el render, se validan y se guardan en caché temporal
  (máximo 2 MiB); si fallan, se usa el monograma.
- `logo_path` mantiene el soporte para paths locales explícitos.

## Layout de la escena
1. La tarjeta grande aparece dentro del carril seguro entre encabezado y footer.
   El encabezado permanece nítido y el ranking previo se oculta para evitar
   ghosting y solapamientos de capas.
2. 5 s de lectura por modelo antes de pasar al siguiente.
   Entre cada modelo, `WAIT_TOP_NITIDO = 2.0` mantiene el ranking acumulado
   completamente nítido antes de iniciar la siguiente tarjeta.
3. La tarjeta vuela a su slot; las tarjetas anteriores permanecen ocultas
   durante el vuelo y reaparecen nítidas en la pausa siguiente.
4. Al terminar, el top entero se revela a plena opacidad.
5. Zonas muertas de 150 px arriba/abajo (UI de Instagram): nada de contenido.

En square y landscape la grilla usa margen lateral de `0.6u`, gutter de
`0.4u` y tipografía secundaria ampliada. Las tarjetas tienen una altura mínima
común para evitar que el puesto `#1` se perciba más pequeño por tener menos
contenido. El vuelo hacia el slot dura `1.0s`.

En formato vertical el hero se centra ligeramente hacia el footer para evitar
un vacío excesivo durante la entrada; square y landscape conservan centrado
geométrico.

Ajustes globales rápidos: `ZONA_SUP_PX`/`ZONA_INF_PX` (zonas muertas),
`slot_pad` (aire por item), `ORO` (color del borde del puesto #1).
