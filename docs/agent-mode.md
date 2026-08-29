# Modo agente — protocolo de operación

Define cómo el agente detecta el tenant, clasifica lo que pide el
usuario, investiga, propone prototipos, itera y publica.

Este documento describe **comportamiento**, no implementación. Las
piezas de código pendientes están en
`docs/plan-agente-conversacional.md`.

---

## 1. Arranque de sesión

Antes de la primera acción de contenido, resolver el tenant. Orden de
precedencia:

1. `--tenant` explícito en el comando.
2. Variable de entorno `TENANT`.
3. `DEFAULT_TENANT` en `.env` de la raíz.
4. Si `tenants/` contiene exactamente un directorio, usar ese.
5. Si hay varios y ninguna de las anteriores resuelve → **preguntar**.

Resuelto el tenant, leer `tenants/<id>/tenant.yaml` y tomar:

| Campo | Uso |
|---|---|
| `name` | Nombre de marca en piezas y footers |
| `brand.logo` | Logo por defecto |
| `brand.default_theme` | Theme visual por defecto |
| `social.instagram.handle` | Handle en captions |
| `publish.namespace` | Carpeta aislada de publicación |

Anunciarlo en **una línea** y seguir:

```
Tenant: agente32 · Agente E32 · @fabian128k
```

No pedir confirmación del tenant si se resolvió por precedencia. No
mezclar assets ni outputs entre tenants nunca.

---

## 2. Router de intención

Clasificar el pedido en una de estas rutas antes de actuar:

| # | Ruta | Disparadores típicos | Salida |
|---|---|---|---|
| 1 | Placa individual | "hacé una placa de X" | 1 PNG + caption |
| 2 | Carrusel | "armá un carrusel de X" | N PNG + caption |
| 3 | Story | "story de X" | 1 PNG 9:16 |
| 4 | Video / Reel | "video de X", "renderizá X" | MP4 + caption |
| 5 | **Tema o noticia completo** | "escribí algo sobre X" | brief + caption + piezas |
| 6 | Solo texto | "escribime el copy de X" | caption |
| 7 | Solo imagen | "generá una imagen de X" | PNG |
| 8 | Publicar | "publicá esto", "dale, subilo" | copia a shared |

### Precedencia con la regla de render express

Si el usuario pide renderizar **una escena que ya existe**, manda la
regla ⚡ de `AGENTS.md`: cero preguntas, render directo. El router no
aplica. El modo conversacional es para contenido que todavía no existe.

### Ambigüedad

Pedido ambiguo → **una** ronda de preguntas, agrupadas, con default
recomendado. Nunca preguntar de a una por turno.

```
¿Qué generamos?
1. Placa vertical 1080x1350 (recomendado)
2. Carrusel de 4 slides
3. Story 9:16
4. Reel

¿Formato? ¿Y querés que investigue primero o ya tenés los datos?
```

---

## 3. Pipeline de tema o noticia (ruta 5)

Es la ruta más larga y la que define el comportamiento de agente.
Ejemplo de disparo:

> "Quiero que escribas algo sobre la compra de HuggingFace por Nvidia"

### Fase 0 — Encuadre

No preguntar nada todavía. Ir directo a investigar. El usuario dio tema
suficiente.

### Fase 1 — Investigación

Buscar en internet. Requisitos mínimos:

- **3 fuentes** como piso, priorizando primarias (blog oficial, release
  notes, comunicado, repositorio) sobre secundarias (medios).
- Fecha de cada fuente. Contenido sin fecha no se usa como confirmación.
- Detectar el **estado**: `confirmado`, `rumor`, `en curso`, `desmentido`.
- Detectar contradicciones entre fuentes y reportarlas.

Guardar los hallazgos en `brief.md` del proyecto de contenido (§5).

### Fase 2 — Devolver el brief al usuario

Antes de escribir nada de copy, mostrar qué se encontró:

```
Encontré esto sobre Nvidia / Hugging Face:

CONFIRMADO
- <hecho> — <medio>, <fecha> — <URL>

SIN CONFIRMAR
- <hecho> — reportado por <medio>, sin confirmación de las partes

CONTRADICCIONES
- <medio A> dice <X>, <medio B> dice <Y>

NO ENCONTRÉ
- Monto de la operación
- Comunicado oficial de cualquiera de las dos empresas

Con esto puedo escribir un post marcando el estado como rumor.
¿Avanzo así o esperás confirmación?
```

Esta fase es obligatoria. No se saltea aunque el tema parezca conocido.

### Fase 3 — Prototipo de texto

Elegir el template de `templates/posts/` según el tipo:

| Situación | Template |
|---|---|
| Hecho reciente | `post_noticia.md` |
| Lectura del hecho | `post_analisis.md` |
| Ranking | `post_lista_top.md` |
| Cómo hacer algo | `post_tutorial.md` |
| Producto o versión nueva | `post_lanzamiento.md` |

Escribir el caption completo y mostrarlo. Marcar `[SIN CONFIRMAR]` lo
que corresponda.

### Fase 4 — Elegir piezas y formato

Recién acá preguntar, todo junto:

```
Texto listo. Para las piezas:

1. Placa vertical 1080x1350 (recomendado, mejor alcance)
2. Carrusel de 4 slides: hecho / qué pasó / puntos clave / por qué importa
3. Story teaser + placa
4. Reel

¿Cuál? ¿Imagen de fondo generada por IA o fondo sólido de marca?
```

### Fase 5 — Assets

Resolver antes de renderizar:

- **Logos** de las entidades mencionadas. Prioridad
  `tenants/<id>/assets/logos/` → `assets/logos/`. Si falta, descargar
  del press kit oficial y documentar el origen en un README junto al
  archivo. Nunca dibujar un logo a mano ni generarlo por IA.
- **Imagen base**. Con IA (`image_generation.enabled: true`) o fondo
  sólido. En prototipo usar el alias `draft`; el modelo de calidad se
  reserva para el final.

### Fase 6 — Prototipo visual

Antes de generar, chequear si ya hay imágenes base en `intermediate/`
(§10). Si hay, preguntar al usuario antes de llamar a la IA de nuevo.

Generar en borrador y **mostrar los paths absolutos**:

```bash
python scripts/generate_images.py carousel --config <slug>.yaml
```

Revisar visualmente cada PNG antes de mostrarlo. Verificar: texto sin
cortes, contraste suficiente, branding presente, zonas seguras
respetadas. Si usó IA, reportar el costo real que imprime el comando
(§9) — nunca estimarlo.

### Fase 7 — Iteración

Aplicar los cambios que pida el usuario y volver a generar. Sin límite
de vueltas. Cada iteración reporta los paths nuevos.

### Fase 8 — Versión final

Con el visto bueno, regenerar en calidad alta, confirmar la salida y
reportar el costo de esta corrida más el acumulado del proyecto (§9).

### Fase 9 — Publicación

**Solo** con aprobación explícita. Ver §7.

---

## 4. Reglas de interacción

- **Preguntar en lote.** Todas las preguntas de una fase en un solo
  turno, numeradas, con recomendación marcada.
- **Máximo 4 preguntas** por turno.
- **Siempre proponer un default.** El usuario debe poder contestar
  "dale" y que el agente avance.
- **Nunca preguntar lo que se puede resolver.** El tenant, la marca, el
  handle, las fuentes y los formatos disponibles salen de archivos.
- **Reportar paths absolutos** de cada artefacto generado.
- **Un artefacto por vez.** No generar carrusel, story y reel juntos sin
  que el usuario los haya pedido.

---

## 5. Proyecto de contenido

Cada tema vive en una carpeta con fecha y slug:

```
tenants/<id>/content/YYYY-MM-DD_<slug>/
  brief.md        # investigación, fuentes, estado de verificación
  caption.md      # copys por red y por pieza
  resumen.md       # costo real de cada llamada a un modelo de imagen IA
  renders/         # PNG generados (cuando la config usa content_slug)
  assets/          # imágenes base y logos descargados para este tema
```

La config **efectiva** que consume el generador vive en
`tenants/<id>/configs/images/<slug>.yaml`. Si declara `content_slug:
"<slug>"`, los renders van a `content/<slug>/renders/` (junto al brief
y el caption); si no, van a `tenants/<id>/output/<output_dir>/`. Lo
resuelve `AppConfig.resolved_output_dir()`.

### Slug

`YYYY-MM-DD_<tema-en-kebab-case>`, sin acentos.
Ejemplo: `2026-08-28_nvidia-huggingface`.

---

## 6. Veracidad

Reglas no negociables:

| Regla | Detalle |
|---|---|
| No inventar | Métricas, fechas, precios, nombres, capacidades |
| Marcar lo dudoso | `[SIN CONFIRMAR]` visible para el usuario |
| Separar niveles | Dato / inferencia / opinión, señalizados |
| Fuente con fecha | Sin fecha no cuenta como confirmación |
| Benchmark propio | Citar como "según <empresa>", nunca como medición neutral |
| Faltante explícito | `N/D`, jamás un valor estimado |

Si el usuario pide afirmar algo que la investigación no sostiene:
decirlo, ofrecer la redacción correcta y dejar la decisión en él.

---

## 7. Gate de publicación

`build.py` y los generadores escriben en `media/` y `output/` del
tenant. **Nunca** copian a la carpeta compartida.

La publicación es un acto explícito:

```bash
python scripts/publish_final.py --video <slug>
python scripts/publish_final.py --type images \
  --source <path> --date YYYY-MM-DD --slug <slug>
```

Destino, aislado por namespace del tenant:

```
/Users/fabian/Documents/shared/<namespace>/videos/<YYYY-MM-DD>_<slug>/
/Users/fabian/Documents/shared/<namespace>/images/<YYYY-MM-DD>_<slug>/
```

### Qué cuenta como aprobación

Cuenta: "publicá", "aprobado", "dale, subilo", "OK publicalo".

**No** cuenta: un comentario positivo sobre el diseño, el fin de un
render, una revisión sin veredicto, o el silencio.

---

## 8. Seguridad

- Secretos solo en `.env` (raíz) y `tenants/<id>/.env`, ambos
  gitignored, permisos `600`.
- Nunca imprimir el valor de una clave. Si aparece en un output,
  señalar el riesgo sin reproducirla.
- Las rutas de assets y configs pasan por `TenantContext`, que rechaza
  rutas absolutas y `..`. No resolver paths a mano salteando esa capa.
- Antes de operaciones destructivas o contra la carpeta compartida,
  confirmar alcance.

---

## 9. Costos de generación de imágenes por IA

Cada llamada a un modelo de imagen (`image_generation.enabled: true`)
devuelve `usage.cost` en la respuesta de OpenRouter. Se registra
**automáticamente**, sin acción del agente, en `resumen.md` del
proyecto (§5) o junto al output si la config no tiene `content_slug`.
El costo nunca se inventa: si el proveedor no lo informa, no se
registra nada.

`scripts/generate_images.py` imprime al terminar el costo de esa
corrida y el acumulado del proyecto:

```
Costo de esta generación: $0.0400 USD (4 imagen(es) por IA)
Costo acumulado del proyecto: $0.0800 USD
Resumen: tenants/<id>/content/<slug>/resumen.md
```

**Obligación del agente**: después de generar cualquier pieza con
imagen por IA (prototipo o final), reportar al usuario ese costo real,
tomado literalmente de la salida del comando:

> Este prototipo (4 slides) costó \$0.04 USD. Acumulado del proyecto:
> \$0.08 USD.

Si la pieza usó fondo sólido o una imagen provista (sin IA), no hay
costo que reportar — decirlo si el usuario pregunta.

---

## 10. Reuso de imágenes intermedias antes de generar

**Siempre chequear antes de generar un borrador o prototipo** si ya
hay imágenes base en `intermediate/` para esa config:

```bash
python scripts/generate_images.py post --config <archivo>.yaml --check-intermediate
```

Si el comando devuelve imágenes existentes, **preguntar al usuario**,
nunca decidir solo:

> Ya hay 4 imágenes base generadas para este prototipo en
> `intermediate/`. ¿Querés volver a generarlas, o verlas antes de
> decidir?

Si el usuario quiere verlas primero, mostrarlas antes de preguntar de
nuevo. El usuario decide:

| Respuesta | Acción |
|---|---|
| "Sí, regenerar" | Correr normal, sin flags extra. Llama a la IA de nuevo, genera costo nuevo (§9) |
| "No, usá esas" | Correr con `--reuse-intermediate`: reusa las imágenes existentes, vuelve a componer texto/theme sobre ellas, sin llamar a la IA ni sumar costo |

```bash
python scripts/generate_images.py post --config <archivo>.yaml --reuse-intermediate
```

Implementado en `generator.py::intermediate_images()` (chequeo, sin
costo ni llamadas) y `_base_image(..., reuse_intermediate=True)`
(reuso real, salta la API si el archivo ya existe).

---

## 11. Comandos de referencia

```bash
source .venv/bin/activate

# Tenants y escenas
python build.py --list-tenants
python build.py --list

# Proyecto de contenido
python scripts/new_content.py --slug <tema-kebab> --tema "<descripción>"
python scripts/generate_caption.py --slug <fecha>_<tema-kebab> --template post_noticia
python scripts/content_status.py

# Assets
python scripts/fetch_logo.py --slug <marca> --url <url> --license "<licencia>"
python scripts/fetch_logo.py --slug <marca> --url <url> --for-manim

# Imágenes (prototipo en borrador, final en alta)
python scripts/generate_images.py post --config <archivo>.yaml --quality draft
python scripts/generate_images.py post --config <archivo>.yaml --quality high
python scripts/generate_images.py carousel --config <archivo>.yaml --quality draft
python scripts/generate_images.py --tenant <id> post --config <archivo>.yaml

# Chequear/reusar imágenes base ya generadas (§10)
python scripts/generate_images.py post --config <archivo>.yaml --check-intermediate
python scripts/generate_images.py post --config <archivo>.yaml --reuse-intermediate

# Videos
python build.py --video <slug> --no-preview
python scripts/generate_videos.py --tenant <id> --video <slug> --no-preview

# Publicación (solo con aprobación explícita)
python scripts/publish_final.py --video <slug>
python scripts/publish_final.py --type images --source <path> --date <YYYY-MM-DD> --slug <slug>
```
