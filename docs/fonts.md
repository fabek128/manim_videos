# Fuentes del proyecto

Política de fuentes para que el proyecto funcione igual en cualquier máquina
(macOS o Linux) sin depender de rutas personales de instalación.

## Dos niveles de fuentes

El proyecto usa fuentes en **dos lugares distintos**, con políticas distintas:

### 1. Imágenes (Pillow) — fuentes incluidas en el repo

El render de placas, carruseles y stories carga las fuentes desde
`assets/fonts/` mediante rutas relativas (`TenantContext.resolve_asset`).
No hay dependencia de fuentes instaladas en el sistema operativo.

| Archivo | Uso |
|---|---|
| `assets/fonts/FiraCode-Regular.ttf` | Código en slides `type: "code"` |
| `assets/fonts/Inter-SemiBold.ttf` | Títulos/cuerpo de placas y carruseles |
| `assets/fonts/Montserrat-ExtraBold.ttf` | Titulares display |

Para agregar una fuente nueva al proyecto:

1. Copiar el TTF/OTF (con su licencia) a `assets/fonts/`.
2. Referenciarla por ruta relativa en el YAML de la config (`fonts:`).
3. Documentar el origen en el README de la fuente si aplica.

Los logos SVG se convierten a curvas (`fetch_logo.py --for-manim`) y no
dependen de la fuente original para renderizarse.

### 2. Videos (Manim + Pango) — fuentes del sistema

Las escenas de Manim referencian fuentes **por nombre** en `Text`/`MarkupText`
(`font="Inter"`, `font="Space Grotesk"`, etc.). Pango las resuelve contra las
fuentes instaladas en el sistema (fontconfig). **El repo no bundlea ni inyecta
estas fuentes en Manim.**

Fuentes por nombre que usan las escenas actuales:

| Nombre | Uso | Alternativa en repo |
|---|---|---|
| `Inter` | Textos, subtítulos, UI | `assets/fonts/Inter-SemiBold.ttf` (solo Pillow; Manim requiere la instalada) |
| `Space Grotesk` | Títulos principales | no incluida en el repo |
| `Noto Sans` | Escenas demo/intro | no incluida en el repo |

## Instalación portable de fuentes de Manim

Instalar las fuentes de video en el sistema **sin depender de una ruta de
macOS**:

- **Linux**: copiar a `~/.local/share/fonts/` (per-user, sin sudo):

  ```bash
  mkdir -p ~/.local/share/fonts
  cp assets/fonts/*.ttf ~/.local/share/fonts/
  fc-cache -f
  ```

  Para fuentes que no están en el repo (Space Grotesk, Noto Sans), descargarlas
  de su fuente oficial y copiarlas al mismo directorio.

- **macOS**: copiar a `~/Library/Fonts/`:

  ```bash
  mkdir -p ~/Library/Fonts
  cp assets/fonts/*.ttf ~/Library/Fonts/
  ```

- **Verificación**: Pango hace fallback silencioso si la fuente no existe.
  Verificar siempre antes de renderizar:

  ```bash
  fc-list | grep -i <fuente>
  ```

## Reglas

1. Una escena usa Fira Code + a lo sumo una fuente de display (títulos/cuerpo).
   No mezclar Space Grotesk + Inter + Manrope en la misma escena.
2. **Fira Code es el default automático** en todo `Text`/`MarkupText` vía el
   patch de `utils/theme.py`. No pasar `font=` salvo excepción consciente.
3. Para títulos y textos no-código pasar la fuente explícitamente:
   ```python
   titulo = Text("Título", font="Space Grotesk")
   subtitulo = Text("Subtítulo", font="Inter")
   ```
4. Los logos SVG van convertidos a curvas: sus fuentes originales NO se tocan.
5. Pesos disponibles: elegir el peso vía archivo/peso instalado; no confiar en
   sintaxis de peso CSS. En Manim, negrita = `weight=Bold` o `weight=BOLD`.