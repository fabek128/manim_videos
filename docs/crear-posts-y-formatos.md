# Cómo crear posts y formatos — guía para agentes

Guía operativa para CUALQUIER agente (E32, Pancho, otro) que opere este repo:
qué piezas se pueden generar, con qué comando, y **qué preguntarle al usuario**
antes de generar cada tipo. Complementa (no reemplaza) `AGENTS.md`, las skills
de `skills/` y los docs de `docs/`.

**Regla de oro**: nunca inventar datos, métricas, fechas ni nombres. Si falta
un dato, preguntarlo o marcar `N/D` / `[SIN CONFIRMAR]`.

---

## 1. Flujo estándar de cualquier pieza

1. **Clasificar el pedido** (tabla §2): placa, carrusel, story, video, noticia,
   caption, o "publicá esto".
2. **Render express si ya existe**: si la escena/pieza ya existe y el usuario
   pide renderizarla → CERO preguntas, render directo (regla del `AGENTS.md`).
3. **Investigar antes de redactar** (solo contenido nuevo): mínimo 3 fuentes,
   primarias primero; registrar fecha de cada una.
4. **Devolver brief** al usuario antes de escribir copy: qué está confirmado,
   qué no, contradicciones, qué no se encontró. Esperar validación.
5. **Preguntar parámetros en lote** (máx 4 preguntas por turno, numeradas,
   siempre con default propuesto para que el usuario pueda responder "dale").
   Qué preguntar según tipo: §3.
6. **Prototipo** en borrador (`--quality draft` para imágenes) → iterar.
7. **Gate visual** (§5) antes de entregar cualquier pieza visual.
8. **Final** en calidad alta con costo reportado (si usó IA: `usage.cost`).
9. **Publicar solo con aprobación explícita** (`scripts/publish_final.py`).

**No preguntar lo que se resuelve leyendo**: tenant (`agente32`), marca/handle
(`@fabian128k`), logos disponibles, configs existentes, formatos del repo.
Consultar `tenants/agente32/configs/images/` y `--list` antes de preguntar.

---

## 2. Clasificación del pedido

| Pedido del usuario | Pieza | Script |
|---|---|---|
| "hacé una placa de X" | Placa (post cuadrado/vertical) | `generate_images.py post` |
| "armá un carrusel de X" | Carrusel (3/5 slides) | `generate_images.py carousel` |
| "story de X" | Story 9:16 | `generate_images.py story` |
| "video de X" / "reel de X" | Video (Manim o web) | `build.py` |
| "escribí algo sobre X" | Tema/noticia completo | `generate_news.py` (niveles 1–3) |
| "escribime el copy de X" | Solo caption | `generate_caption.py` |
| "generá una imagen de X" | Solo imagen base | `generate_images.py` |
| "publicá esto" | Publicación | `publish_final.py` |

---

## 3. Qué preguntar por tipo de pieza

### 3.1 Placa (post cuadrado `1:1` o vertical `4:5`)

```bash
python scripts/generate_images.py --tenant agente32 post --config <nombre>.yaml [--quality draft|medium|high] [--reuse-intermediate]
```

| Parámetro | Obligatorio | Default sugerido |
|---|---|---|
| Tema / dato principal del post | sí | — |
| Título/headline (o se redacta del brief) | no | del brief |
| Fondo: `solid` \| screenshot de URL \| IA | no | screenshot si hay URL real; si no, IA |
| Formato: cuadrado vs vertical | no | vertical (`post_vertical`) |
| Fuente de la noticia/URL | no | — |

El resto (paleta, fuentes, logos, safe_area) lo define el config/template;
NO preguntar. Salida: `tenants/agente32/output/<output_dir>/`.

### 3.2 Story (`9:16`)

```bash
python scripts/generate_images.py --tenant agente32 story --config story.yaml [--quality ...]
```

| Parámetro | Obligatorio | Default |
|---|---|---|
| Tema | sí | — |
| Título corto (1 línea, se lee en 2 s) | no | del brief |
| CTA final ("Seguí @fabian128k", "Link en bio") | no | "Seguí @fabian128k" |
| Fondo | no | ídem placa |

### 3.3 Carrusel (cuadrado `1:1` o vertical `4:5`, 3 o 5 slides)

```bash
python scripts/generate_images.py --tenant agente32 carousel --config carousel_noticia_3.yaml --quality draft
```

| Parámetro | Obligatorio | Default |
|---|---|---|
| Tema | sí | — |
| Cantidad de slides | sí (3 o 5) | 3 |
| Formato: cuadrado vs vertical | no | vertical |
| Estructura (portada + desarrollo + cierre) | no | cover + text/bullets + cierre con CTA |
| Slides de código (tipo `code`) | no | no |

Tipos de slide disponibles: `cover` (portada), `text`, `bullets`, `code`.
Salida: `tenants/agente32/output/<output_dir>/slide_*.png` (o `renders/`).

### 3.4 Noticia completa (niveles 1–3)

```bash
python scripts/generate_news.py --level 1 --url <URL> [--format short]
python scripts/generate_news.py --level 2 --topic "<tema>" [--select N --format carousel3]
python scripts/generate_news.py --level 3 --topic "<tema>" [--select 1 --format carousel5]
```

| Parámetro | Obligatorio | Default |
|---|---|---|
| Nivel (1 fuente única / 2 búsqueda / 3 profunda) | sí | 2 |
| `--url` (nivel 1) o `--topic` (niveles 2–3) | sí | — |
| Ángulo (si el informe ofrece opciones) | después del informe | opción recomendada |
| Formato de la pieza (post/story/carrusel 3 o 5) | no | carousel3 |

Sin terminal interactiva el script imprime opciones y espera: el agente
devuelve el informe al usuario y espera su elección. Salida: brief,
screenshot validado, pieza(s) y `post.txt`.

### 3.5 Caption / copy (solo texto)

```bash
python scripts/generate_caption.py --slug <contenido> --template post_noticia
```

| Parámetro | Obligatorio | Default |
|---|---|---|
| Tema/brief | sí | — |
| Template (`post_noticia`, `post_analisis`, `post_lista_top`, `post_tutorial`, `post_lanzamiento`, `carousel_noticia`, `story_teaser`) | no | según pieza |
| Tono, hashtags, CTA | no | tono editorial del repo |

### 3.6 Video de noticia / data-driven (Manim)

```bash
python build.py --tenant agente32 --video <nombre-noticia> --no-preview [--serve]
```

Las noticias se animan desde `tenants/agente32/videos/noticias/` (`scene.py`
+ `json/`): el JSON es la entrada.

| Parámetro | Obligatorio | Default |
|---|---|---|
| Tema / datos de la noticia | sí | — |
| Formato: reel (9:16) vs post (3:4) | no | reel |
| Calidad | no | low para iterar, high para final |
| Background/audio | no | del JSON |

### 3.7 Video top / "los más usados" (ranking semanal)

```bash
python build.py --tenant agente32 --video lomas --serve
# o con JSON propio: configs/videos/top/<nombre>.json
```

| Parámetro | Obligatorio | Ejemplo |
|---|---|---|
| Modelos (lista 5–10 en orden de ranking) | sí | GPT-5.2, Claude Opus 4.6… |
| Uso (métrica por modelo: %, horas, prompts) | sí | 42%, 18 h, 310 prompts |
| Periodo a mostrar | sí | "Semana del 17–23 ago" |
| Formato: reel / post vertical / cuadrado | no | reel |

Opcionales con defaults: `metrica_label` ("% de uso"), `duracion_total`
(8–12 s), `mostrar_barra` (true), `estilo_entrada` (countdown),
`musica` (ninguna).

**Regla del JSON**: antes de opinar o modificar, leer el archivo real;
mejorar redacción de textos visibles pero NUNCA inventar métricas/orden.
Detalle completo: `skills/los_mas_usados.md`.

### 3.8 Video web_capture (screenshot de URL con zoom/pan)

```bash
python build.py --tenant agente32 --video <nombre-web> --no-preview [--serve]
```

Se define con `web.yaml` (engine web, Playwright + cámara zoom/pan, sin Manim).

| Parámetro | Obligatorio | Default |
|---|---|---|
| URL a capturar | sí | — |
| Selector/elemento (si aplica) | no | página completa |
| Zoom/pan (directión y duración) | no | zoom lento centrado |
| Formato | no | vertical 9:16 |

Gate obligatorio: revisar con visión el screenshot crudo (publicidad,
popups, paywalls, texto cortado). Detalle: `docs/web-capture.md`.

### 3.9 Intros / logos (escenas existentes)

Render express: CERO preguntas. Solo preguntar si la escena NO existe.

---

## 4. Parámetros de diseño que NO se preguntan

Decididos por el config/template del repo (a menos que el usuario pida
cambios explícitos):

- Marca, paleta, fuentes, footer `@fabian128k`, logos SVG.
- `safe_area` por formato (square 18/20%, vertical 6/8%, story 6/13%) + margin 20 px.
- Template de diseño (`templates/prompts/`) referenciado en el YAML.

## 5. Checklist previo a entregar

- [ ] Datos verificados (fuentes con fecha); sin inventar métricas/nombres.
- [ ] `--check-intermediate` antes de regenerar (reuso con `--reuse-intermediate`
      si el usuario lo elige; eso evita costo de IA).
- [ ] Gate visual con rol de visión: publicidad, popups, texto cortado,
      contraste, logos verdaderos, zonas seguras — máx 3 reintentos, la 4.ª
      evaluación decide; estado en `vision_review.json`; nunca entregar en
      silencio una pieza fallida.
- [ ] Costo IA reportado (si aplica), tomado de la salida del comando.
- [ ] Paths absolutos de cada artefacto generado (regla del AGENTS.md).
- [ ] Video: verificación `ffprobe` (resolución/fps) del mp4 final.
- [ ] Publicar solo con aprobación explícita: `publish_final.py --type
      images|videos --source <path> --date YYYY-MM-DD --slug <slug>`.

## 6. Referencias

- `AGENTS.md` — protocolo completo (modo agente, veracidad, costos, publicación).
- `skills/generador_imagenes.md` — schema YAML, slides, calidad, solución de problemas.
- `skills/los_mas_usados.md` — video top en detalle.
- `skills/contenido.md` — pipeline de contenido y captions.
- `skills/global.md` — convenciones del repo.
- `docs/instagram-formats.md` — zonas seguras por formato.
- `docs/agent-mode.md` — protocolo del modo agente conversacional.
- `docs/web-capture.md` — captura web + cámara zoom/pan.
- `docs/news-generator.md` — generador de noticias por niveles.