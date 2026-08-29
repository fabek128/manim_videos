# Theme News Text — Agente E32

## Propósito
Prompt reutilizable para un slide interior de noticia destinado a Agente E32.
El texto se proporciona externamente y la composición final debe mantener una
jerarquía editorial clara.

## Composición

- Usar una imagen fotográfica opcional como fondo.
- Aplicar un degradado oscuro cuando el fondo pueda reducir la legibilidad.
- Mantener un encabezado separado del contenido principal.
- Presentar el título con la mayor jerarquía tipográfica del slide.
- Organizar el cuerpo breve en bloques fáciles de escanear.
- Colocar una línea divisoria arriba del título como separación visual.
- Centrar el logo SVG de Agente E32 sobre la línea divisoria.
- Ubicar el título y el cuerpo descriptivo debajo de la línea y del logo.
- Ubicar `@fabian128k` abajo a la derecha, junto al logo de la red social.
- Ubicar el logo de la red social abajo a la derecha, junto a `@fabian128k`.

## Reglas de diseño

- Respetar las safe areas del formato de salida (configurable por
  config con `safe_area:`; spec en `theme_carousel_system.md` → "Safe
  area configurable").
- Mantener márgenes consistentes y evitar texto pegado a los bordes.
- Asegurar contraste suficiente entre fondo y texto: el degradado arranca
  antes de la línea divisoria y llega a opacidad plena bien temprano
  (~37-43% de alto), no recién al final. Spec exacta en
  `theme_carousel_system.md` → "Degradado y contraste".
- Evitar que la imagen compita con el título o el cuerpo.
- No deformar, estirar ni rasterizar innecesariamente los logos SVG.
- Mantener la misma identidad visual en todos los slides del carrusel.

## Variables

- `{{encabezado}}`: texto breve de contexto.
- `{{titulo}}`: titular principal.
- `{{cuerpo}}`: desarrollo breve de la noticia.
- `{{imagen_fondo}}`: imagen opcional.
- `{{logo_agente_e32}}`: ruta del logo SVG.
- `{{logo_red_social}}`: ruta del logo social.
- `{{handle}}`: por defecto `@fabian128k`.
