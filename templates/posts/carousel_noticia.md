# Template: carrusel de noticia

## Cuándo usarlo

El tema no entra en una placa. Necesita contexto, varios datos o una
secuencia. Entre 3 y 6 slides; más de 6 pierde retención.

## Formatos

| Formato | Medida | Uso |
|---|---|---|
| `carousel_vertical` | 1080x1350 | Default. Ocupa más pantalla |
| `carousel_square` | 1080x1080 | Cuando hay imágenes horizontales |

## Estructura canónica

| Slide | Tipo | Función | Regla |
|---|---|---|---|
| 1 | `cover` | Gancho | El hecho puro. Debe funcionar solo |
| 2 | `text` | Qué pasó | Actores, fecha, cifra |
| 3 | `bullets` | Puntos clave | 3 a 4 bullets, uno por idea |
| 4 | `text` | Por qué importa | Consecuencia concreta |
| 5 | `text` | Contexto o cierre | Antecedente o pregunta |

Slides 4 y 5 son opcionales. El slide 1 nunca lo es.

## Reglas por slide

- **Cover**: `title` ≤ 90 caracteres. `highlights` con subcadenas
  literales del `title`. Si el usuario solo ve este slide, tiene que
  entender la noticia.
- **Text**: `body` de 180 a 320 caracteres. Más que eso se achica la
  tipografía y deja de leerse en móvil.
- **Bullets**: 3 a 4 items, ≤ 60 caracteres cada uno. Sin sub-bullets.
- **Code**: solo si el tema lo justifica. Máx 12 líneas, con tags
  `<code>...</code>`.

## Consistencia visual

Todos los slides comparten `brand`, `fonts`, `colors` y `footer_text`.
El branding no cambia entre slides del mismo carrusel. La guía de
diseño está en `templates/prompts/theme_carousel_system.md`.

## Caption del carrusel

El caption no repite los slides: los complementa.

```
[GANCHO — el mismo hecho del slide 1, redactado distinto]

[LO QUE NO ENTRÓ EN LAS PLACAS — 2 a 4 oraciones con el detalle,
las cifras finas o la fuente.]

[CIERRE — pregunta o llamado a deslizar.]

[HANDLE]
[HASHTAGS]
```

## Mapeo al YAML

```yaml
project_name: "<slug>"
output_dir: "<slug>"
format: "carousel_vertical"
template: "news_carousel"

brand:
  name: "<brand.name del tenant>"
  logo_path: "logos/<slug-marca>/<archivo>.svg"

fonts:
  title: "fonts/Montserrat-ExtraBold.ttf"
  body: "fonts/Inter-SemiBold.ttf"
  code: "fonts/FiraCode-Regular.ttf"

colors:
  text_primary: "#FFFFFF"
  text_secondary: "#D9D9D9"
  highlight_bg: "#0057D9"
  footer_text: "#FFFFFF"
  divider: "#6F86A8"

slides:
  - type: "cover"
    title: "<HECHO EN MAYÚSCULAS>"
    highlights: ["<subcadena 1>", "<subcadena 2>"]
    subtitle: "<categoría> · <estado>"
    footer_text: "<brand.name>"
  - type: "text"
    title: "QUÉ PASÓ"
    body: "<2 a 3 oraciones>"
    footer_text: "<brand.name>"
  - type: "bullets"
    title: "PUNTOS CLAVE"
    bullets:
      - "<punto 1>"
      - "<punto 2>"
      - "<punto 3>"
    footer_text: "<brand.name>"
  - type: "text"
    title: "POR QUÉ IMPORTA"
    body: "<consecuencia concreta>"
    footer_text: "<brand.name>"
```

## Generación

```bash
python scripts/generate_images.py carousel --config <archivo>.yaml
```

El archivo vive en `tenants/<id>/configs/images/` y la ruta se pasa
relativa a esa carpeta. La salida son `slide_01.png`, `slide_02.png`, …
en `tenants/<id>/output/<output_dir>/`.

## Checklist antes de mostrar al usuario

- [ ] El slide 1 se entiende sin los demás
- [ ] Los `highlights` son subcadenas literales del `title`
- [ ] Ningún `body` supera 320 caracteres
- [ ] El footer es idéntico en todos los slides
- [ ] Los datos coinciden con el brief verificado
- [ ] Las imágenes existen y no están recortando texto
