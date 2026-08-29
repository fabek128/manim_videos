# Templates de posts para redes sociales

Estos templates definen **el texto** que acompaña a cada pieza (caption,
copy, estructura de slides). Son distintos de `templates/prompts/`, que
definen **el diseño visual**.

| Template | Uso |
|---|---|
| `post_noticia.md` | Noticia o hecho reciente verificable |
| `post_analisis.md` | Análisis técnico, opinión fundada, contexto |
| `post_lista_top.md` | Ranking / "los más usados" / comparativas |
| `post_tutorial.md` | Cómo hacer algo, con o sin código |
| `post_lanzamiento.md` | Lanzamiento de producto, modelo o feature |
| `carousel_noticia.md` | Estructura slide por slide de un carrusel |
| `story_teaser.md` | Story 9:16 que empuja al post principal |

## Cómo se usan

1. El agente elige el template según la intención detectada.
2. Completa los **campos requeridos** con datos verificados.
3. Genera el caption con PromptGate (`PROMPTGATE_MODEL`).
4. Mapea los campos al YAML de `tenants/<id>/configs/images/`.

## Reglas transversales (aplican a todos)

- **Nunca inventar** métricas, fechas, precios, nombres ni capacidades.
  Dato no confirmado → marcarlo `[SIN CONFIRMAR]` y avisar al usuario.
- Toda afirmación factual necesita fuente. Las fuentes van en el brief,
  no necesariamente en el caption.
- Español neutro. Sin emojis salvo pedido explícito del usuario.
- Sin promesas comerciales ni clickbait que el contenido no cumpla.
- El handle de la marca sale de `tenant.yaml` → `social.instagram.handle`.

## Límites de Instagram

| Elemento | Límite |
|---|---|
| Caption | 2200 caracteres |
| Visible antes de "… más" | ~125 caracteres |
| Hashtags | 30 máximo (recomendado 8–15) |
| Título en placa | 90 caracteres para que no se corte |

El **gancho** debe entrar en los primeros 125 caracteres. Todo lo que
importa va antes del corte.
