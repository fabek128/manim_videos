# Skill: Generación de contenido para redes (placas, carruseles, captions)

> **Carga automática**: esta skill se lee SIEMPRE que la tarea sea de
> contenido para redes — placa, carrusel, story, caption, o un pedido tipo
> "escribí/armá/generá algo sobre X". Se lee junto con `skills/global.md`
> (que sigue siendo obligatoria), no en su lugar. Protocolo completo:
> `docs/agent-mode.md`.

## 1. Setup obligatorio

```bash
source .venv/bin/activate
```

## 2. Resolver el tenant primero

```bash
python build.py --list-tenants
```

Precedencia: `--tenant` > `TENANT` > `DEFAULT_TENANT` en `.env` > único
tenant en `tenants/`. Todo lo que sigue opera dentro de
`tenants/<id>/`: assets, configs, content, media, output.

## 3. Herramientas disponibles

| Script | Para qué |
|---|---|
| `scripts/new_content.py` | Crear el andamiaje de un tema: `brief.md`, `caption.md`, `assets/` |
| `scripts/generate_caption.py` | Redactar el caption desde `brief.md` con un template de `templates/posts/` |
| `scripts/generate_images.py` | Renderizar placa o carrusel desde un YAML |
| `scripts/fetch_logo.py` | Descargar y registrar un logo con origen documentado |
| `scripts/content_status.py` | Ver el estado de todos los proyectos de contenido del tenant |
| `scripts/publish_final.py` | Publicar a la carpeta compartida (solo con aprobación explícita) |

## 4. Flujo para un tema nuevo

```bash
# 1. Crear el proyecto de contenido
python scripts/new_content.py --slug <tema-kebab> --tema "<descripción>"

# 2. Investigar y completar tenants/<id>/content/<slug>/brief.md a mano
#    (el agente edita el archivo con los hallazgos verificados)

# 3. Generar el caption desde el brief
python scripts/generate_caption.py --slug <fecha>_<tema-kebab> \
  --template post_noticia   # o el que corresponda

# 4. Escribir el YAML de la pieza en tenants/<id>/configs/images/
#    con content_slug: "<fecha>_<tema-kebab>" para que el render
#    quede junto al proyecto

# 5. Chequear si ya hay imagen base generada (intermediate/) antes de
#    llamar a la IA; si hay, preguntar al usuario (ver §9)
python scripts/generate_images.py post --config <archivo>.yaml --check-intermediate

# 5b. Generar prototipo en borrador (o --reuse-intermediate si el
#     usuario prefirió no regenerar)
python scripts/generate_images.py post --config <archivo>.yaml --quality draft

# 6. Iterar con el usuario

# 7. Final en calidad alta
python scripts/generate_images.py post --config <archivo>.yaml --quality high
```

## 5. Elegir el template de texto

| Tipo de contenido | Template en `templates/posts/` |
|---|---|
| Hecho reciente verificable | `post_noticia.md` |
| Lectura u opinión fundada | `post_analisis.md` |
| Ranking / comparativa | `post_lista_top.md` |
| Cómo hacer algo | `post_tutorial.md` |
| Producto o versión nueva | `post_lanzamiento.md` |
| Carrusel de noticia | `carousel_noticia.md` |
| Story que empuja a otra pieza | `story_teaser.md` |

Cada template define campos requeridos, límites de longitud y el mapeo
exacto a los campos del YAML. Leerlo antes de redactar.

## 6. Logos y assets

Prioridad de resolución: `tenants/<id>/assets/logos/` →
`assets/logos/` (compartido). Si falta un logo:

```bash
python scripts/fetch_logo.py --slug <marca> --url <press-kit-oficial> \
  --license "<licencia declarada>"
```

Con `--for-manim` si el logo se va a usar en una escena de video (Manim
no soporta `<text>`, necesita curvas). Nunca dibujar un logo a mano ni
generarlo por IA.

## 7. Calidad de imagen

`--quality draft` (default) usa `OPENROUTER_IMAGE_DRAFT_MODELS`. Usar
`draft` para todo prototipo e iteración. Recién en la entrega final:
`--quality high`. No tocar `image_generation.model` en el YAML para
esto: el flag lo sobrescribe en tiempo de ejecución.

## 8. Costos de generación por IA

Cada llamada a un modelo de imagen que devuelva `usage.cost` se
registra sola en `resumen.md` (junto al proyecto en `content/<slug>/`,
o junto al output si la config no tiene `content_slug`). No hay que
hacer nada para que esto pase — `generator.py` lo hace automático.

Lo que **sí** es obligación del agente: `scripts/generate_images.py`
imprime el costo de la corrida y el acumulado del proyecto al
terminar. Después de generar cualquier pieza con IA, reportar ese
costo real al usuario, tomado de la salida del comando:

> Este prototipo (4 slides) costó \$0.04 USD. Acumulado del proyecto:
> \$0.08 USD.

Nunca estimar el costo ni omitir el reporte. Fondo sólido o imagen
provista (sin IA) → no hay costo, decirlo si preguntan.

## 9. Reuso de imágenes intermedias antes de generar

**Siempre chequear antes de generar un borrador o prototipo** si ya
hay imágenes base en `intermediate/`:

```bash
python scripts/generate_images.py post --config <archivo>.yaml --check-intermediate
```

Si devuelve imágenes existentes, preguntar al usuario — nunca decidir
solo — si quiere regenerarlas o verlas antes. Si el usuario dice que
no regenere, usar `--reuse-intermediate`: reusa las imágenes
existentes como fondo y recompone el texto/theme sobre ellas, sin
llamar a la IA ni sumar costo:

```bash
python scripts/generate_images.py post --config <archivo>.yaml --reuse-intermediate
```

## 10. Veracidad — no negociable

- Nunca inventar métricas, fechas, precios, nombres ni capacidades.
- Todo hecho en el brief necesita fuente con fecha.
- `estado: confirmado` en el brief exige 2+ fuentes primarias
  (`src/noticia_carrusel/brief.py` lo valida).
- Dato faltante: `N/D`. Nunca un valor estimado.
- Marcar `[SIN CONFIRMAR]` lo que no tenga sustento y avisarlo.

## 11. Verificación visual

Antes de mostrar un PNG al usuario: revisar que el texto no se corte,
que el contraste sea suficiente, que el branding esté presente y que
las zonas seguras de Instagram se respeten (`docs/instagram-formats.md`).

## 12. Publicación

Nunca automática. Solo con "publicá", "aprobado", "dale, subilo" o
equivalente explícito:

```bash
python scripts/publish_final.py --type images \
  --source <path> --date <YYYY-MM-DD> --slug <tema-kebab>
```

Un comentario positivo sobre el diseño o el fin de un render **no** es
aprobación.
