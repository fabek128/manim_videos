# Theme News Cover — Agente E32

## Descripción
Prompt reutilizable para el diseño del primer slide de un carrusel de noticias destinado a Agente E32. Define la composición visual, jerarquía y restricciones técnicas del slide.

## Composición del Slide

### Zona Superior (70%)
- Imagen principal clara y de alta resolución.
- La imagen ocupa exactamente el 70% superior del lienzo sin deformación.

### Zona Inferior (30%)
- Transición gradual de difuminado y oscurecimiento progresivo desde el 70% hacia el 100% del lienzo.
- Contenido gráfico y textual alineado en esta zona inferior.

### Distribución de Elementos en la Zona Inferior
1. **Línea divisoria** horizontal que cruza la zona inferior.
2. **Logo SVG de Agente E32** centrado sobre la línea divisoria o integrado en su centro.
3. **Titular** posicionado debajo del logo con jerarquía visual primaria.
4. **Descripción** posicionada debajo del titular con jerarquía visual secundaria.
5. **Logo de la red social** alineado en el extremo inferior derecho.
6. **@fabian128k** alineado a la derecha, junto al logo de la red social.

## Reglas de Uso

### Safe Area
- Todos los elementos críticos deben permanecer dentro del área segura.
- Margen mínimo de seguridad del 5% en todos los bordes del lienzo para evitar recortes.
- Default por formato: izquierda/derecha 6%, arriba 6%, abajo 7-13%
  según formato (calculado en `CanvasSpec.from_format()`). Se puede
  sobrescribir por config con `safe_area:` (spec en
  `theme_carousel_system.md` → "Safe area configurable").

### Jerarquía Visual
- Orden de peso: Imagen (70%) > Logo E32 > Titular > Descripción > Logo red social / @fabian128k.
- El titular debe poseer el mayor peso tipográfico dentro de la zona inferior.

### Legibilidad
- Contraste mínimo de 4.5:1 entre texto y fondo en la zona inferior.
- Utilizar sombras, fondos semitransparentes o difuminados si la imagen de fondo compromete la lectura.
- Tamaño de fuente mínimo garantizado para legibilidad en dispositivos móviles.
- El degradado debe llegar a opacidad plena bien entrada la franja de
  texto, no recién en el borde inferior. Spec exacta en
  `theme_carousel_system.md` → "Degradado y contraste".

### Integridad de Logos
- Prohibir la deformación, estiramiento o distorsión de los logos SVG.
- Mantener la proporción original y la resolución vectorial de todos los logos.
- El logo de Agente E32 debe conservar sus proporciones exactas.

### Restricciones de Texto
- No solicitar a la IA que genere o escriba contenido textual original.
- Los campos de titular y descripción deben ser proporcionados como variables estáticas previamente.
- El prompt define exclusivamente la estructura visual y la disposición de los elementos, no el contenido textual.

## Variables del Prompt
- `{{titular}}`: Texto del titular (proporcionado externamente).
- `{{descripcion}}`: Texto de la descripción (proporcionado externamente).
- `{{imagen_principal}}`: Referencia de la imagen para el 70% superior.
- `{{logo_red_social}}`: Referencia del logo de la red social para la esquina inferior derecha.
