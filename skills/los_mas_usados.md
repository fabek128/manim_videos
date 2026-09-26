# Skill: Los modelos que más usé esta semana

> **Carga automática**: se lee sola cuando la tarea es armar este video.
> Complementa (no reemplaza) `skills/global.md`, que también debe estar cargada.
> **Nota 2026-09-06**: el generador `top` es ahora global y reutilizable. No crear
> `tenants/<id>/videos/lostops/scene.py` manualmente. El tenant aporta solo
> `tenants/<id>/configs/videos/top/*.json` (esquema `title`/`items`/`audio`)
> y `tenant.yaml` (`brand.footer_logos`, `default_theme`). Ver
> `docs/shared-top-generator-refactor-plan.md`. Para personalización visual,
> usar `tenants/<id>/overrides/videos/top/scene.py` que herede de `BaseTopScene`.

Instrucción estándar para armar el video semanal de rankings (ahora vía
generador global `top`). Formato: countdown visual con logos, nombres y métricas.

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

```text
[0.0s] Título: entrada, hold de lectura y traslado a cabecera
[siguiente] Puesto N: tarjeta central detallada
[por puesto] Entrada → hold → movimiento estable → crossfade al slot
[...] Puestos N-1 hasta #1
[fin] Revelado conjunto → ola → hold final
```

Con los defaults de `TopStyle`, el título dura 5.4s y cada puesto 6.2s;
un destacado suma 0.4s de pulso. Un top de cinco elementos con hold final
de 5s dura aproximadamente 44s. Cambiar duración exclusivamente mediante
los campos `title_*`, `card_*`, `wave_*` y `final_hold_seconds`; no insertar
literales en el composer.

La posición `#1` es siempre el único destacado: usa
`highlighted_rank_color` y `card_highlight_pulse_factor`. El config no
declara flags de destacado. Todas las tarjetas centrales comparten
`central_card_height` (default `3.8`) y todos los slots del ranking comparten
`ranking_card_height` (default `1.2`). Si el contenido excede su caja, se
escala dentro de ella sin cambiar la altura exterior. La tarjeta central muestra todo el
detalle; por defecto el ranking final conserva logo, puesto, nombre y métrica.
`ranking_show_comments` y `ranking_show_specs` permiten incluir el detalle
también en el cierre.

## 3. Logos de los modelos

1. Chequear `assets/logos/<modelo>/` — preferir `_paths.svg`.
2. Si no existe, buscar primero el press kit o sitio oficial del vendor.
   Descargar SVG y convertir su texto a curvas con Inkscape
   (`--export-text-to-path`) cuando sea posible. Si el vendor solo publica
   PNG/WebP/JPEG, conservar el raster oficial: el renderer admite esos
   formatos.
3. Sanitizar SVG: `stroke:none`, remover `stroke-width`/`paint-order`
   residuales y verificar `SVGMobject(...)` sin warnings.
4. Guardar el asset en `assets/logos/<nombre>/` con un README que documente
   URL oficial, variante y fecha de recuperación.
5. Usar monograma únicamente si se confirmó que no existe logo oficial
   disponible. El gate visual debe rechazar placeholders cuando la marca sí
   publica un logo.
6. Los logos se normalizan a una altura común y se alinean a la izquierda.

## 4. Audio (opcional)

Manim soporta audio vía `self.add_sound("archivo.mp3", time_offset=..., gain=...)`.
Se llama en `construct()` y queda sincronizado al render final. Si el usuario pide
música:

- Pedir el archivo de audio y guardarlo en `assets/audio/`
- Un solo track de fondo: `self.add_sound(track, gain=-8)` al inicio
- SFX por puesto revelado: `self.add_sound("whoosh.mp3")` dentro del loop
- Alternativa post-render (más control): mezclar con ffmpeg
  `ffmpeg -i video.mp4 -i music.mp3 -map 0:v -map 1:a -c:v copy -shortest out.mp4`

## 5. Uso del generador global (no crear escena manual)

```bash
# Crear/editar JSON genérico
# tenants/<id>/configs/videos/top/2026-09-06_mi-top.json
{
  "schema_version": 1,
  "title": ["TOP HERRAMIENTAS", "DE LA SEMANA"],
  "subtitle": "Semana del 1 al 7 de septiembre",
  "audio": {"asset": "sounds/intros/SunsetDrift.mp3", "gain_db": -4},
  "final_hold_seconds": 5.0,
  "items": [
    {"name": "Herramienta", "visual_asset": "logos/openai/openai_paths.svg", "secondary_text": "OpenAI", "metric": {"label": "Uso", "value": "42%"}, "comment": ["Línea 1", "Línea 2"], "specs": [{"label": "Estado", "value": "Confirmado"}]}
  ]
}

# Renderizar (elige el JSON más reciente si no se pasa --config)
python build.py --tenant agente32 --video top --no-preview
python build.py --tenant agente32 --video top --config 2026-09-06_mi-top.json --seed 42 --no-preview
# Alias siguen funcionando:
python build.py --tenant agente32 --video lostops --no-preview
```

La lógica visual y de animación vive en
`src/noticia_carrusel/video_generators/top/`. `BaseTopScene.construct()` carga
el contexto y llama al único orquestador principal:
`TopComposer.animar_top_completo(scene)`. El entrypoint
`generators/videos/top/scene.py` es mínimo. Los assets se resuelven vía
`TenantContext.resolve_asset` (tenant → global) y el pool de fondos vía
`available_backgrounds` combinado.

Formatos: vertical 9:16 (`-f reel`, default) y 3:4 (`-f post`) son el camino
principal. `--no-format` (16:9 landscape) también funciona: activa el modo
grid de 2 columnas del composer; las zonas seguras (`safe_*_px`, calibradas
para el lienzo 1080x1920) se clampean a un máximo de 16% del alto del render
(`ZONA_SEGURA_MAX_FRACCION` en `composer.py`), de modo que 9:16 y 3:4 quedan
intactos. El fondo se aplica en modo cover: escala para cubrir todo el frame
y recorta centrado, así que el pool vertical también sirve en landscape.

## 5b. Arquitectura y orquestación de la animación

`TopComposer.animar_top_completo()` es el equivalente al `main` del top. No
existe un segundo camino `render` que pueda divergir. Ejecuta, en este orden:

1. `configurar_layout(scene)`;
2. `agregar_audio(scene)`;
3. `agregar_fondo(scene)`;
4. `agregar_footer(scene)`;
5. `animar_titulo(scene)`;
6. `animar_tarjeta_puesto(scene, puesto, item)` para cada puesto, de último a
   primero;
7. `animar_cierre(scene)`.

El composer calcula geometría, arma objetos y verifica zonas seguras. Las
primitivas reusables que ejecutan movimiento viven en `BaseTopScene`:

|Función|Responsabilidad|
|---|---|
|`ingreso_titulo_top`|`FadeIn`, permanencia central y traslado del título a la cabecera|
|`ingreso_tarjeta_puesto`|entrada, espera, vuelo al slot, atenuados, restauraciones y pulso opcional|
|`revelar_top`|restauración conjunta de opacidad antes del cierre|
|`play_scale_wave`|ola secuencial de escala|
|`play_zoom_pulse`|zoom deliberado reusable; no forma parte del flujo default|
|`espera_final_top`|hold final con mínimo de frames|

Todos los tiempos, shifts, opacidades, factores de escala, repeticiones y
mínimos de frames del flujo default tienen una sola fuente:
`TopStyle` (`style.py`). Un tenant puede construir un contexto inmutable con
`context.with_style(context.style.with_overrides(...))`, sin copiar la escena
ni el composer.
Las rate functions se reciben como parámetros de las primitivas para permitir
curvas alternativas sin duplicar implementación. Toda pausa positiva se
redondea hacia arriba a frames completos para no desaparecer en Manim.


## 5c. Efecto ola configurable

`TopComposer` ejecuta una ola al cerrar el ranking, después de devolver todas
las filas a opacidad completa. La implementación reusable está en
`BaseTopScene.play_scale_wave(objects, ...)`.

```python
self.play_scale_wave(
    filas,
    scale_factor=1.05,
    transition_time=0.12,
    hold_time=0.04,
    between_items_time=0.02,
    repetitions=1,
    reverse=False,
)
```

- `scale_factor`: tamaño máximo relativo; debe ser mayor que `1`.
- `transition_time`: segundos de cada tramo (crecer y achicar). Menor valor =
  movimiento más rápido.
- `hold_time`: permanencia de cada objeto en tamaño máximo.
- `between_items_time`: pausa entre saltos consecutivos.
- `repetitions`: cantidad de recorridos completos.
- `reverse`: invierte el orden recibido.
- `rate_func`: curva de interpolación Manim; por defecto usa `smooth`.

Los defaults del cierre viven en `TopStyle.wave_*` y son también los defaults
de la firma de `play_scale_wave` (fuente única). Un override tenant puede
usar `context.with_style(context.style.with_overrides(...))`, sin copiar el
compositor global. La función valida números no finitos, tiempos negativos,
factores que no agrandan y elementos que no sean `Mobject`. Las pausas se
cuantizan a frames: un valor mayor que 0 pero menor a `1/fps` dura 1 frame
(sin esto, `between_items_time=0.02` a 30 fps era un no-op).

Para un zoom deliberado de cada tarjeta (crecer, mantenerse ampliado, volver),
usar la variante hermana `BaseTopScene.play_zoom_pulse(objects, ...)`:
defaults `scale_factor=1.3`, `transition_time=0.3`, `hold_time=0.6` (dwell
largo), sin pausa entre objetos y un solo recorrido. Comparte validación,
cuantización y restauración de escala con la ola. No se ejecuta
automáticamente: invocarla desde un override tenant o el compositor cuando se
la necesite.

## 5d. Ingreso de tarjeta al ranking

La entrada de cada tarjeta (`FadeIn` con shift → espera → movimiento del
bloque sin deformar → crossfade al slot con atenuados y restauraciones →
pulso de aterrizaje si está destacada) vive en
`BaseTopScene.ingreso_tarjeta_puesto(puesto, objeto, destino, ...)`; el
composer la invoca una vez por fila y conserva el `Mobject` retornado. El
título permanece a opacidad completa y el panel central es opaco para que
ningún slot previo contamine el texto.

```python
style = composer.style
scene.ingreso_tarjeta_puesto(
    puesto=3,
    objeto=tarjeta,
    destino=slot,
    atenuar_entrada=anteriores,
    atenuar_vuelo=(
        (previo_chip, style.card_landed_chip_opacity),
        (previo_contenido, style.card_landed_content_opacity),
    ),
    restaurar_vuelo=(),
    pulso=style.card_highlight_pulse_factor,
    pulso_time=style.card_highlight_pulse_time,
    shift=(0.0, style.card_entry_shift_y, 0.0),
    entrada_time=style.card_entry_time,
    espera_time=style.card_hold_time,
    vuelo_time=style.card_flight_time,
    vuelo_move_ratio=style.card_flight_move_ratio,
)
```

Los defaults de tiempos, shift, opacidades, fracción de movimiento y pulso
provienen de `TopStyle`; los tamaños del comentario y de las especificaciones
centrales se controlan con `central_comment_font_size`,
`central_spec_label_font_size` y `central_spec_value_font_size`. Con
`destino=None` se saltea el vuelo y con `pulso=0` se deshabilita el pulso de
aterrizaje. Las verificaciones de zonas muertas siguen en el composer
(`_chequear_zonas`), no en la función de movimiento.

## 6. Checklist antes de entregar

- [ ] Datos del usuario confirmados (§1) — nunca inventar métricas
- [ ] Logos existentes reutilizados; nuevos sanitizados y documentados
- [ ] Render `-ql` verificado por frame (colores, orden del ranking legible)
- [ ] Duración total dentro de lo pedido
- [ ] Escena ya existente → render directo SIN preguntas (regla ⚡ AGENTS.md):
      `python build.py --tenant <id> --video top --no-preview`
      (alias `lostops`/`losmas` también resuelven al mismo generador; `--config` para elegir JSON, `--seed` para fondo reproducible; Reel default implícito)
- [ ] Si el JSON no existe, crearlo en `tenants/<id>/configs/videos/top/YYYY-MM-DD_slug.json` con esquema genérico (`title`/`subtitle`/`audio.asset`/`items[]`) y validar con `TopSpec`
- [ ] Escena nueva → confirmar datos §1 antes de crear JSON, luego mismo comando
