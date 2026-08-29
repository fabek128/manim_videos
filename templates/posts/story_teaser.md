# Template: story teaser

## Cuándo usarlo

Pieza 9:16 que anticipa un post o carrusel ya publicado. Vida útil de
24 horas. No es contenido autónomo: empuja a otra pieza.

## Campos requeridos

| Campo | Descripción | Obligatorio |
|---|---|---|
| `gancho` | Una frase, máx 60 caracteres | Sí |
| `pieza_destino` | Qué post o carrusel promociona | Sí |
| `cta` | Acción concreta esperada | Sí |

## Zonas seguras 9:16

El formato es 1080x1920, pero Instagram superpone su UI:

| Zona | Píxeles | Regla |
|---|---|---|
| Superior | 0–250 | Sin texto ni logo |
| Inferior | 1670–1920 | Sin texto ni logo |
| Segura | 250–1670 | Todo el contenido acá |

Texto fuera de la zona segura queda tapado por el header y la barra de
respuesta. Referencia completa en `docs/instagram-formats.md`.

## Reglas de contenido

- Una sola idea. El story no explica, avisa.
- Máximo 2 bloques de texto.
- Tipografía grande: se lee a un brazo de distancia y en movimiento.
- Sin párrafos. Sin hashtags. Sin caption largo.
- El CTA es explícito: "Post completo en el perfil".

## Mapeo al YAML

```yaml
project_name: "<slug>_story"
output_dir: "<slug>_story"
format: "story"
template: "news_card"

brand:
  name: "<brand.name del tenant>"
  logo_path: "logos/<slug-marca>/<archivo>.svg"

fonts:
  title: "fonts/Montserrat-ExtraBold.ttf"
  body: "fonts/Inter-SemiBold.ttf"

content:
  title: "<GANCHO EN MAYÚSCULAS, máx 60 caracteres>"
  highlights: ["<la palabra que carga el gancho>"]
  subtitle: "<CTA>"
  footer_text: "<brand.name>"
```

## Ejemplo

```yaml
content:
  title: "NVIDIA VA POR HUGGING FACE"
  highlights: ["HUGGING FACE"]
  subtitle: "Análisis completo en el perfil"
  footer_text: "AGENTE E32"
```

## Checklist

- [ ] Todo el contenido entre los píxeles 250 y 1670
- [ ] Máximo 2 bloques de texto
- [ ] El gancho se lee en menos de 2 segundos
- [ ] El CTA nombra dónde está la pieza completa
- [ ] La pieza destino ya está publicada o se publica en el mismo momento
