# Theme Carousel System — Agente E32

## Propósito
Prompt reutilizable para mantener una identidad visual consistente en todos los
slides de un carrusel de noticias de Agente E32.

## Estructura narrativa

1. **Portada:** imagen principal, titular y highlights.
2. **Desarrollo:** explicación breve de la noticia.
3. **Puntos clave:** lista de datos relevantes y fáciles de escanear.
4. **Cierre:** síntesis, fuente o llamada a la acción.

## Reglas compartidas

- Usar el mismo canvas, márgenes, safe areas, tipografías y colores en todos los
  slides.
- Mantener una jerarquía visual reconocible entre titular, cuerpo y datos.
- Reutilizar el mismo tratamiento de imagen y degradado.
- Mantener el divisor y el logo SVG de Agente E32 centrados de forma consistente.
- Ubicar `@fabian128k` abajo a la derecha en todos los slides.
- Ubicar el logo de la red social abajo a la derecha junto a @fabian128k.
- No deformar, estirar ni alterar la proporción de los logos.
- No pedir a la IA que genere el texto de la noticia; el contenido textual se
  entrega como variable externa.


## Degradado y contraste (comportamiento implementado)

El overlay oscuro (`colors.overlay_start` → `colors.overlay_end`) debe
llegar a **opacidad plena antes del final** de la zona de texto de cada
slide, no recién en el último píxel del lienzo. Un degradado que solo
empieza a notarse cerca del borde deja el título y el cuerpo sobre fondo
parcialmente visible y compromete la legibilidad.

**Regla única para todos los slides**: el degradado arranca ~60px antes
de la línea divisoria (donde vive el logo SVG de Agente E32), nunca
justo en el divisor ni después. Así la imagen ya está oscureciendo
cuando aparece el divisor y el logo, en portada e interiores por igual.

Implementado en `src/noticia_carrusel/render/templates.py::render()`
(`gradient_start_at` / `gradient_end_at` de `add_gradient`):

```
divider_line_y = split_y (cover, ~70% de alto) | divider_y (interiores, ~9-15%)
gradient_start_at = (divider_line_y - 30px) / alto_lienzo
gradient_end_at   = gradient_start_at + span   # span: 0.12 cover, 0.32 interiores
```

| Slide | Arranca a oscurecer | Opacidad plena |
|---|---|---|
| `cover` | ~64% de alto (60px antes del divisor a 70%) | ~76% |
| `text` / `bullets` / `code` | ~60px antes del divisor superior (~5-11%) | ~37-43% |

En los slides interiores el título y el cuerpo ocupan casi todo el resto
del slide, por eso el span hasta opacidad plena es mayor (0.32 vs 0.12):
el fondo queda sólido detrás de la mayor parte del contenido, no solo
con un leve oscurecimiento progresivo.

## Safe area configurable

Los márgenes seguros tienen un default por formato (`carousel_square`,
`carousel_vertical`, `post_square`, `post_vertical`, `story`),
calculado en `src/noticia_carrusel/render/canvas.py::CanvasSpec.from_format()`:

| Formato | Izq./Der. | Arriba | Abajo |
|---|---|---|---|
| `story` | 6% | 6% | 13% |
| `post_vertical` / `carousel_vertical` | 6% | 6% | 8% |
| `post_square` / `carousel_square` | 6% | 18% | 20% |

El default de `post_square`/`carousel_square` se subió de 6%/7% a
18%/20% (validado visualmente: badges + divisor + footer necesitan esa
reserva fija en 1:1). **No se generalizó a los demás formatos**: la
misma fracción aplicada a `post_vertical`/`carousel_vertical`/`story`
(lienzos más altos) recorta el título — confirmado con contenido real,
ver commit que introdujo `is_square` en `CanvasSpec.from_format()`.
Vertical/story mantienen su default original.

Se puede sobrescribir a nivel config (top-level, aplica a todos los
slides del carrusel para mantener consistencia visual) con
`safe_area:`. Cada lado es opcional; el que no se declara conserva el
default del formato:

```yaml
safe_area:
  top: 0.18      # fracción del alto del lienzo (0.0-0.45)
  bottom: 0.20
  # left / right también aceptados; fracción del ancho
```

Validado en `models.py::SafeAreaConfig` (rango 0.0-0.45 por lado, para
evitar valores que dejen sin espacio utilizable). Aplicado en
`NewsCardRenderer.__init__` al construir el `CanvasSpec`.

**La zona segura aplica a TODO el contenido, no solo al footer.** Título,
descripción, cuerpo, bullets y código nunca dibujan más allá del límite
real disponible — si el texto no entra, se recorta línea por línea
(`TextEngine._clip_to_height`), nunca se corta a mitad de palabra ni se
deja overflow. El footer (`_draw_brand`, handle + ícono social) tiene
70px reservados pegados al borde inferior de la zona segura
(`NewsCardRenderer.FOOTER_RESERVED_HEIGHT`); el resto del contenido debe
terminar antes de esa franja, no en el borde crudo de `safe_area.bottom`.

En la portada, si `safe_area.bottom` es grande, el divisor sube lo
necesario para reservar al menos 200px de texto
(`NewsCardRenderer.MIN_COVER_TEXT_HEIGHT`) antes del footer; con valores
muy agresivos la descripción puede quedar sin espacio y no se dibuja
(mejor omitirla que invadir la zona segura).

Nota: en la portada (`cover`), la línea divisoria vive a un 70% fijo
del alto por default (no depende de `safe_area.top`), pero SÍ se
ajusta hacia arriba cuando `safe_area.bottom` no deja lugar para el
texto. En slides interiores, `top` sí mueve directamente el divisor
desde siempre.

## Margen extra en píxeles (`margin:`)

Además de `safe_area` (fracción del lienzo), se suma un margen
absoluto en píxeles con `margin:` — para ajustes finos sin recalcular
porcentajes. Se suma al `safe_area` ya resuelto, no lo reemplaza.

**Default: 20px en los 4 lados, para todo formato** (`post_square`,
`post_vertical`, `story`, `carousel_square`, `carousel_vertical`).
A diferencia del default de `safe_area`, este sí es universal — 20px
es lo bastante chico como para no recortar contenido en ningún
formato (confirmado: solo resta 40px de alto útil en `post_vertical`,
sin causar recorte). No hace falta declarar `margin:` para tener este
default; solo para ajustarlo:

```yaml
margin:
  left: 30     # px, sumados al safe_area ya resuelto (default 20 c/u)
  top: 30
  right: 30
  bottom: 30
```

Cada lado es independiente; el que no se declara usa el default de
20px (no 0). Validado en `models.py::MarginConfig` (0-200px por
lado). Aplicado en `NewsCardRenderer.__init__` vía
`SafeArea.expand()` (`canvas.py`), después de resolver `safe_area`: el
resultado es un `SafeArea` más grande que empuja todo el contenido
(título, cuerpo, footer) hacia adentro por igual, sin tocar el fondo.

## Flujo de composición

- Preparar el fondo y el reencuadre antes de dibujar el texto.
- Aplicar el degradado necesario para asegurar contraste.
- Componer el contenido dentro de las safe areas.
- Revisar que cada slide pueda entenderse por separado y que el conjunto tenga
  continuidad narrativa.
- Mantener el mismo footer y sistema de branding durante todo el carrusel.

## Variables

- `{{slides}}`: lista ordenada de slides.
- `{{tipo_slide}}`: `cover`, `text`, `bullets` o cierre.
- `{{titulo}}`: titular del slide.
- `{{cuerpo}}`: desarrollo textual.
- `{{bullets}}`: puntos clave.
- `{{imagen}}`: fondo opcional.
- `{{logo_agente_e32}}`: ruta del logo SVG.
- `{{logo_red_social}}`: ruta del logo social.
- `{{handle}}`: por defecto `@fabian128k`.
