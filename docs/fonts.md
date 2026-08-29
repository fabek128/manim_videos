# Fuentes del proyecto

Especificación de tipografías para los videos. Estado de instalación verificado
con `fc-list` el 2026-08-25.

| Fuente | Estilo | Uso | Instalada |
|---|---|---|---|
| **Inter** | Limpia / profesional | Textos, subtítulos, UI | ✅ (`~/Library/Fonts/Inter-Variable.ttf`) |
| **Manrope** | Moderna / geométrica | Títulos + cuerpo (alternativa) | ✅ (`~/Library/Fonts/Manrope-Variable.ttf`) |

## Cómo se aplican

- **Fira Code es el default**: el patch en `utils/theme.py` inyecta
  `font="Fira Code"` en todo `Text`/`MarkupText`. No pasar `font=` salvo
  excepción consciente.
- Para títulos y textos no-código pasar la fuente explícitamente:
  ```python
  titulo = Text("Título", font="Space Grotesk")
  subtitulo = Text("Subtítulo", font="Inter")
  ```
- Los logos SVG van convertidos a curvas: sus fuentes originales NO se tocan.

## Reglas

1. Una escena usa Fira Code + a lo sumo una fuente de display (títulos/cuerpo).
   No mezclar Space Grotesk + Inter + Manrope en la misma escena.
2. Pango hace fallback silencioso si la fuente no existe: verificar siempre con
   `fc-list | grep -i <fuente>` antes de renderizar con una nueva.
3. Pesos disponibles: elegir el peso vía archivo/peso instalado; no confiar en
   sintaxis de peso CSS. En Manim, negrita = `weight=Bold` o `weight=BOLD`.
4. Si falta una fuente requerida por un video: instalarla en `~/Library/Fonts`
   y actualizar la tabla de este documento.

