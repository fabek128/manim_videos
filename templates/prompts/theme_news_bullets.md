# Theme News Bullets — Agente E32

## Propósito
Prompt reutilizable para un slide de noticia con una lista de puntos clave.
El texto se proporciona externamente y la composición final debe priorizar una
lectura rápida y ordenada.

## Composición

- Usar un titular principal con la mayor jerarquía visual.
- Presentar los puntos clave como una lista de viñetas con espaciado uniforme.
- Usar un fondo fotográfico opcional con degradado que arranque antes de
  la línea divisoria y llegue a opacidad plena a ~37-43% de alto (spec
  exacta en `theme_carousel_system.md` → "Degradado y contraste").
- Colocar una línea divisoria arriba del título como separación visual.
- Centrar el logo SVG de Agente E32 sobre la línea divisoria.
- Ubicar `@fabian128k` abajo a la derecha, junto al logo de la red social.
- Ubicar el logo de la red social abajo a la derecha, junto a `@fabian128k`.

## Reglas de diseño

- Mantener todos los elementos dentro de las safe areas del formato
  (configurable por config con `safe_area:`; spec en
  `theme_carousel_system.md` → "Safe area configurable").
- Reservar márgenes equivalentes a izquierda y derecha.
- Mantener una separación constante entre título, viñetas y divisor.
- Usar tipografía legible y claramente diferenciada entre título y viñetas.
- No deformar ni estirar los logos.
- Mantener la misma identidad visual en los demás slides del carrusel.

## Variables

- `{{titulo}}`: titular principal.
- `{{bullets}}`: lista de puntos clave, uno por línea.
- `{{fondo}}`: imagen o color de fondo opcional.
- `{{degradado}}`: overlay opcional para mejorar legibilidad.
- `{{logo_agente_e32}}`: ruta del logo SVG.
- `{{logo_red_social}}`: ruta del logo social.
- `{{handle}}`: por defecto `@fabian128k`.
