# Template: post de noticia

## Cuándo usarlo

Hecho reciente, verificable y con fuente. Compras, fusiones, despidos,
regulaciones, resultados, incidentes. Si el hecho **no está confirmado**,
usar este template igual pero con el estado explícito (ver abajo).

## Campos requeridos

| Campo | Descripción | Obligatorio |
|---|---|---|
| `hecho` | Qué pasó, en una oración | Sí |
| `actores` | Quién / qué empresas u organismos | Sí |
| `fecha` | Cuándo ocurrió o se anunció | Sí |
| `fuente_principal` | URL y medio | Sí |
| `fuentes_secundarias` | 2+ URLs que corroboran | Sí |
| `estado` | `confirmado` \| `rumor` \| `en curso` | Sí |
| `cifra` | Monto, porcentaje o métrica central | No |
| `porque_importa` | Impacto concreto para el lector | Sí |

Falta un campo obligatorio → pedirlo o marcarlo `[SIN CONFIRMAR]`.
Nunca completarlo por inferencia.

## Estructura del caption

```
[GANCHO — máx 125 caracteres, el hecho puro, sin adjetivos]

[QUÉ PASÓ — 2 a 3 oraciones. Actores, fecha, cifra si existe.]

[POR QUÉ IMPORTA — 2 a 3 oraciones. Consecuencia concreta,
no especulación.]

[CONTEXTO — 1 a 2 oraciones. Antecedente que explica el hecho.]

[CIERRE — una línea. Pregunta al lector o dato abierto.]

[HANDLE]
[HASHTAGS]
```

## Estado de la información

El estado se refleja en el texto, no se omite:

- `confirmado` → afirmar en indicativo. "Nvidia compró…"
- `rumor` → "Según <medio>, Nvidia estaría negociando…" y en la placa
  agregar `subtitle: "Sin confirmación oficial"`.
- `en curso` → "La operación está en revisión regulatoria…"

Nunca convertir un rumor en un hecho para que el título rinda mejor.

## Longitud y tono

- Caption: 600–1200 caracteres. Nunca superar 2200.
- Oraciones cortas. Una idea por oración.
- Sin adjetivos de hype: *histórico*, *brutal*, *increíble*, *game changer*.
- Voz activa. Números en cifra, no en letra.

## Hashtags

8 a 15, en tres capas:

1. Tema: `#Nvidia #HuggingFace #IA`
2. Categoría: `#InteligenciaArtificial #Tecnologia #OpenSource`
3. Marca: el handle del tenant y su etiqueta propia.

Sin hashtags genéricos de alcance (`#follow`, `#viral`, `#fyp`).

## Mapeo al YAML

```yaml
format: "post_vertical"          # o post_square / story
template: "news_card"

content:
  title: "<HECHO EN MAYÚSCULAS, máx 90 caracteres>"
  highlights: ["<2 a 3 fragmentos exactos del title>"]
  subtitle: "<Lugar o rubro · Estado de la información>"
  footer_text: "<brand.name>"
```

Reglas del mapeo:

- `highlights` debe contener **subcadenas literales** de `title`. Si no
  coinciden, no se resaltan.
- `title` es el gancho, no el caption completo.
- `subtitle` lleva el estado cuando no está confirmado.

## Ejemplo

Datos verificados de entrada:

```
hecho: Nvidia acordó comprar Hugging Face
actores: Nvidia, Hugging Face
fecha: 2026-08-27
estado: rumor
fuente_principal: <URL del medio>
porque_importa: concentra el hub de modelos abiertos en un fabricante de GPU
```

Caption resultante:

```
Nvidia estaría negociando la compra de Hugging Face.

Según <medio>, las dos compañías avanzaron en un acuerdo por el hub de
modelos abiertos. Ninguna de las partes lo confirmó de forma oficial al
27 de agosto de 2026.

Si se cierra, el repositorio donde se distribuye buena parte del
ecosistema open source de IA quedaría bajo control del principal
fabricante de GPU del mercado. Eso toca licencias, hosting y costos de
inferencia para cualquiera que hoy dependa del hub.

Hugging Face nació como alternativa abierta frente a los modelos
cerrados. La operación invierte esa posición.

¿Migrarías tus modelos a otro hub?

@fabian128k
#Nvidia #HuggingFace #IA #OpenSource #InteligenciaArtificial #Tecnologia
```

YAML correspondiente:

```yaml
content:
  title: "NVIDIA NEGOCIA LA COMPRA DE HUGGING FACE"
  highlights: ["NVIDIA", "COMPRA DE HUGGING FACE"]
  subtitle: "Tecnología · Sin confirmación oficial"
  footer_text: "AGENTE E32"
```
