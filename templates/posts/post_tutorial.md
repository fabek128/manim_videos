# Template: post tutorial

## Cuándo usarlo

Explicar cómo hacer algo concreto, con pasos reproducibles. Con o sin
código. Ideal para carrusel; en placa única solo si son ≤ 4 pasos.

## Campos requeridos

| Campo | Descripción | Obligatorio |
|---|---|---|
| `objetivo` | Qué logra el lector al terminar | Sí |
| `prerequisitos` | Qué necesita tener antes de empezar | Sí |
| `pasos` | Lista ordenada, cada uno accionable | Sí |
| `verificacion` | Cómo sabe que funcionó | Sí |
| `error_comun` | El fallo típico y su causa | No |
| `version` | Versión de la herramienta usada | Sí si hay código |

`verificacion` es obligatorio. Un tutorial sin forma de comprobar el
resultado no sirve.

## Estructura del caption

```
[OBJETIVO — qué vas a lograr, máx 125 caracteres]

[PREREQUISITOS — una línea.]

[PASOS — numerados, imperativo, uno por línea.]

[VERIFICACIÓN — cómo comprobar que salió bien.]

[ERROR COMÚN — el fallo típico y por qué pasa.]

[HANDLE]
[HASHTAGS]
```

## Reglas del código

- Todo snippet debe ser **ejecutable tal cual**. Nada de `...` ni
  pseudocódigo presentado como código real.
- Declarar la versión: `manim v0.21`, `Python 3.12`.
- Máximo 12 líneas por slide de código. Más que eso no se lee en móvil.
- Nunca incluir tokens, claves ni rutas privadas. Usar
  `os.environ["API_KEY"]` como placeholder.
- El código lo escribe el agente, no el generador de imágenes por IA.

## Longitud y tono

- Caption: 600–1400 caracteres.
- Imperativo: "Instalá", "Ejecutá", "Verificá".
- Un paso = una acción. Si un paso tiene dos verbos, son dos pasos.

## Mapeo al YAML

Carrusel con slide de código:

```yaml
format: "carousel_vertical"
template: "news_carousel"

slides:
  - type: "cover"
    title: "<OBJETIVO EN MAYÚSCULAS>"
    highlights: ["<el resultado>"]
    subtitle: "Tutorial · <herramienta> <version>"
    footer_text: "<brand.name>"
  - type: "bullets"
    title: "ANTES DE EMPEZAR"
    bullets: ["<prerequisito 1>", "<prerequisito 2>"]
    footer_text: "<brand.name>"
  - type: "code"
    title: "<PASO N>"
    code: |
      <code>
      # código ejecutable, máx 12 líneas
      </code>
    footer_text: "<brand.name>"
  - type: "text"
    title: "CÓMO VERIFICAR"
    body: "<verificacion>"
    footer_text: "<brand.name>"
```

Los tags `<code>` y `</code>` son obligatorios: el renderer los usa para
detectar el bloque y los elimina antes de dibujar.

## Ejemplo

```
Renderizá un Reel 1080x1920 desde una escena de Manim en un comando.

Necesitás Python 3.12, manim v0.21 y ffmpeg instalado.

1. Activá el entorno: source .venv/bin/activate
2. Listá las escenas disponibles: python build.py --list
3. Renderizá con el formato Reel: python build.py --video intro --no-preview
4. Confirmá la salida en media/videos/<slug>/1920p30/

Verificá con ffprobe que el archivo diga 1080x1920 y 30 fps. Si dice
otra cosa, el formato no se aplicó.

Error común: pasar -r 1080,1920,30. En manim v0.21 el fps va aparte,
con --fps 30. Con el formato junto, el comando falla.

@fabian128k
#Manim #Python #Animacion #Desarrollo #Tutorial
```
