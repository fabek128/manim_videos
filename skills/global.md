# Skill: Generación de animaciones (global)

> **Carga automática**: esta skill se lee SIEMPRE al iniciar cualquier tarea en
> este repo, sin que el usuario lo pida. Las skills específicas
> (`los_mas_usados.md`, etc.) se cargan además cuando la tarea coincide con su
> tipo de video.

## 1. Setup obligatorio

```bash
source .venv/bin/activate   # Python 3.12 + manim v0.21.0 + ffmpeg
```

## 2. Estructura

- Un video = una carpeta: `videos/YYYY-MM-DD_tema/scene.py`
- Clases PascalCase heredando de `Scene` (o `MovingCameraScene` si hay cámara)
- Assets vectoriales en `assets/logos/<nombre>/` — nunca inline en la escena
- Output a `media/` (gitignored, no editar)

footer: en el footer siempre deberan estar los logos de agente32 y fabian128k.
El footer debe tener una altura maxima de 4% del alto total. Ajustar los logos siempre.

## 3. Assets SVG (logos, gráficos)

1. Fuente editable (`_src.svg`) y versión para Manim (`_paths.svg`) juntas
2. Manim NO soporta `<text>`: convertir a curvas con Inkscape:

```bash
/Applications/Inkscape.app/Contents/MacOS/inkscape \
  --export-type="svg" --export-text-to-path \
  --export-filename=/tmp/xxx_paths_raw.svg fuente.svg
```

3. Forzar `stroke:none` y remover `stroke-width`/`paint-order` residuales
   (Inkscape deja valores gigantes que Manim pinta como halos enormes)
4. Documentar regeneración en el README del asset
5. Importar con ruta absoluta al asset: `Path(__file__).parents[2] / "assets" / ...`

Si el logo del modelo no existe aún como asset: buscarlo en internet
(Wikipedia / press kit oficial / worldvectorlogo), descargar SVG, sanitizarlo con
el mismo procedimiento y guardarlo en `assets/logos/<nombre>/`.

## 4. Temas visuales

- Usar `ThemedScene` de `utils/theme.py`; colores desde `self.theme.*`
- Nunca hardcodear colores de marca dentro de `construct()`
- Fondo por defecto negro; cambiar solo vía tema

## 4b. Fuente por defecto

- Todo `Text`/`MarkupText` usa **Fira Code** automáticamente (patch en
  `utils/theme.py`, se activa al importarlo). No pasar `font=` salvo excepción
  consciente.
- Los logos SVG van como curvas: sus fuentes originales NO se tocan nunca.

### Especificación de fuentes (detalle en `docs/fonts.md`)

- **Fira Code**: código (snippets, identificadores, números). Default automático
  en todo `Text`/`MarkupText`; no pasar `font=` salvo excepción consciente.
- **Space Grotesk**: ⭐ títulos principales (pasar `font=` explícito).
- **Inter**: textos, subtítulos, UI (pasar `font=` explícito).
- **Manrope**: alternativa títulos + cuerpo (pasar `font=` explícito).
- Reglas: una escena = Fira Code + a lo sumo una fuente de display; los logos
  SVG van como curvas y nunca se les cambia la fuente.

## 5. Animación — convenciones probadas

- Ritmo rápido: `FadeIn` ~0.3s; pulsos únicos ~0.4s con `rate_func=there_and_back`
- Zoom sutil = escala 1.05–1.06 y volver exacto al tamaño original (`there_and_back`)
- Sin pausas muertas: nada de `self.wait()` largos entre animaciones
- Verificación visual: render `-ql`, extraer frame con ffmpeg y validar colores/geometría

## 6. Formatos de salida

- Referencia completa: `docs/instagram-formats.md`
- **Regla ⚡ (ver "Render express" en AGENTS.md, prioridad máxima)**: escena
  existente → CERO preguntas, render directo:
  `python build.py --video <nombre-que-dijo-el-usuario> --no-preview`
  Reel 1080x1920@30 es el default implícito; `-f post` para 3:4;
  `--no-format -q high` para 1080p60. Reportar path + ffprobe + comando alterno.
- Preguntar destino SOLO al crear una escena nueva (§8)
- Composición centrada; bordes superior/inferior reservados para UI en 9:16

## 7. Audio

- Música y SFX viven en `assets/sounds/<categoría>/` (actualmente solo
  `intros/`). Ver tracks disponibles con `ls assets/sounds/*/`
- En la escena: `self.add_sound(ruta, time_offset=0, gain=15)` — el audio
  queda embebido y sincronizado en el render final de Manim. Ver regla de
  **Ganancia** abajo.
- Ruta absoluta al asset: `Path(__file__).parents[2] / "assets" / "sounds" / ...`
- Alternativa post-render (control fino de mezcla): ffmpeg
  `ffmpeg -i video.mp4 -i music.mp3 -map 0:v -map 1:a -c:v copy -shortest out.mp4`
- **Ganancia**: los tracks de `sounds/intros/` tienen master bajo (mean ≈
  −32 dB, pico ≈ −18 dB). Con `gain=-14` el audio queda inaudible. Usar
  `gain=15` (verificado: mean ≈ −17 dB, pico ≈ −2 dB, sin clipping). Si un
  track nuevo suena bajo: medir con
  `ffmpeg -i video.mp4 -af volumedetect -f null - 2>&1 | grep volume` y ajustar.

## 7b. Análisis de JSON

Cuando el usuario pida analizar un JSON, leer siempre el archivo real antes de
responder. Revisar estructura, tipos, campos obligatorios, valores faltantes o
inválidos, orden y consistencia de los datos, y referencias a assets o URLs.
Revisar también todos los textos visibles y mejorar siempre su ortografía,
gramática, claridad, tono y consistencia (`titulo`, `subtitulo`, descripciones,
comentarios y etiquetas). No inventar métricas ni otros hechos: conservar los
datos factuales y señalar lo que requiera confirmación. Si el usuario pide
modificar el JSON, aplicar las mejoras y validarlo antes de renderizar.

## 8. Flujo de trabajo

1. Clarificar con el usuario: contenido, duración objetivo, formato de salida
   (solo al crear escena nueva; si ya existe, saltar directo a render)
2. Crear carpeta + `scene.py`; reusar assets existentes antes de crear nuevos
3. Desarrollo en `-ql --no-preview`; iterar rápido
4. Verificar frame final por píxeles (colores presentes, posiciones correctas)
5. Render/entrega: un solo comando, sin preguntas intermedias:
   `python build.py --video <nombre> --no-preview` (Reel default implícito).
   Salida en `media/videos/<módulo>/<H>p<fps>/`. Abrir con `-o`. Reportar path.
6. Actualizar READMEs de assets si se crearon nuevos
