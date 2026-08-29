# Template: post de análisis

## Cuándo usarlo

Explicar por qué algo pasa, comparar alternativas o dar una opinión
técnica fundada. No hay hecho nuevo: hay lectura de un hecho.

## Campos requeridos

| Campo | Descripción | Obligatorio |
|---|---|---|
| `tesis` | La afirmación central, en una oración | Sí |
| `evidencia` | 2 a 4 datos verificables que la sostienen | Sí |
| `contraargumento` | La objeción más fuerte a la tesis | Sí |
| `conclusion` | Qué hacer o qué mirar a partir de esto | Sí |
| `alcance` | Qué NO afirma este análisis | Sí |

`contraargumento` y `alcance` son obligatorios: un análisis sin objeción
declarada es propaganda.

## Estructura del caption

```
[TESIS — máx 125 caracteres, afirmativa y discutible]

[EVIDENCIA — 3 a 4 oraciones. Un dato por oración, con su magnitud.]

[CONTRAARGUMENTO — 1 a 2 oraciones. "Esto puede fallar si…"]

[CONCLUSIÓN — 2 oraciones. Qué implica en la práctica.]

[ALCANCE — una línea. "No estoy diciendo que…"]

[HANDLE]
[HASHTAGS]
```

## Longitud y tono

- Caption: 800–1600 caracteres.
- Primera persona permitida: es una opinión, se firma.
- Separar hecho de interpretación de forma explícita.
- Prohibido presentar la tesis como consenso si no lo es.

## Marcado de certeza

| Nivel | Redacción |
|---|---|
| Dato duro | "X creció 40% en 2026 según <fuente>" |
| Inferencia | "Eso sugiere que…" |
| Opinión | "Para mí, …" / "Mi lectura es que…" |

Mezclar los tres niveles sin marcarlos es el error más común. No hacerlo.

## Mapeo al YAML

```yaml
format: "post_vertical"
template: "news_card"

content:
  title: "<TESIS EN MAYÚSCULAS, máx 90 caracteres>"
  highlights: ["<el núcleo discutible de la tesis>"]
  subtitle: "Análisis · <categoría>"
  footer_text: "<brand.name>"
```

Para carrusel, usar `carousel_noticia.md` con esta distribución:

| Slide | Tipo | Contenido |
|---|---|---|
| 1 | `cover` | Tesis |
| 2 | `bullets` | Evidencia |
| 3 | `text` | Contraargumento |
| 4 | `text` | Conclusión + alcance |

## Ejemplo

```
Comprar el hub de modelos abiertos es comprar el canal de distribución,
no los modelos.

Los pesos de la mayoría de los modelos abiertos tienen licencias
permisivas y espejos fuera del hub. Lo que no se replica fácil es el
tráfico: la ruta por defecto de descarga, la integración en librerías y
la reputación del índice.

Esto puede fallar si la comunidad migra rápido a alternativas
autoalojadas, algo que ya pasó con otros registries.

En la práctica, cualquier equipo que dependa de un solo hub debería
tener hoy un plan de mirror y fijar versiones por hash.

No estoy diciendo que los modelos abiertos dejen de serlo.

@fabian128k
#IA #OpenSource #MLOps #InteligenciaArtificial #Infraestructura
```
