# Template: post de lanzamiento

## Cuándo usarlo

Sale un modelo, producto, versión o feature. El foco es **qué cambia
respecto de lo anterior**, no el comunicado de prensa.

## Campos requeridos

| Campo | Descripción | Obligatorio |
|---|---|---|
| `producto` | Nombre y versión exactos | Sí |
| `quien` | Empresa u organización | Sí |
| `fecha` | Fecha del anuncio | Sí |
| `que_cambia` | Diferencia concreta con la versión previa | Sí |
| `disponibilidad` | Abierto, beta, waitlist, pago, región | Sí |
| `precio` | Costo o `N/D` | Sí |
| `fuente_oficial` | URL del anuncio de la fuente primaria | Sí |
| `limitacion` | Qué no hace o dónde falla | Sí |

`limitacion` es obligatorio. Un lanzamiento sin límites declarados es
publicidad, y este proyecto no publica publicidad de terceros.

## Regla de fuente

La fuente **primaria** manda: blog oficial, release notes, repositorio.
Un medio que cubre el anuncio es fuente secundaria y se usa solo para
corroborar. Benchmarks del propio fabricante se citan como tales:
"según <empresa>", nunca como medición independiente.

## Estructura del caption

```
[QUÉ SALIÓ — producto, versión y el cambio, máx 125 caracteres]

[QUÉ CAMBIA — 2 a 3 oraciones. Comparación con lo anterior.]

[DISPONIBILIDAD Y PRECIO — una a dos líneas, sin ambigüedad.]

[LIMITACIÓN — 1 a 2 oraciones. Qué no resuelve.]

[CIERRE — para quién sirve concretamente.]

[HANDLE]
[HASHTAGS]
```

## Longitud y tono

- Caption: 600–1200 caracteres.
- Cero superlativos sin número. "Más rápido" solo con la cifra al lado.
- Si el precio no está publicado: `N/D`. Nunca estimarlo.
- Si la disponibilidad es por región, decir cuál.

## Mapeo al YAML

```yaml
format: "post_vertical"
template: "news_card"

content:
  title: "<PRODUCTO + EL CAMBIO, MAYÚSCULAS, máx 90 caracteres>"
  highlights: ["<nombre del producto>"]
  subtitle: "<quien> · <disponibilidad>"
  bullets:
    - "Cambio: <que_cambia>"
    - "Precio: <precio>"
    - "Límite: <limitacion>"
  footer_text: "<brand.name>"
```

## Logos

Si el post menciona una empresa con logo disponible, resolverlo con la
prioridad tenant → compartido:

1. `tenants/<id>/assets/logos/<slug>/`
2. `assets/logos/<slug>/`

Si no existe, descargarlo del press kit oficial y guardarlo con su
README de origen. Nunca reconstruir un logo a mano ni generarlo por IA.

## Ejemplo

```
Sale la versión 2.0 del runtime con soporte de contexto extendido.

La ventana pasa de 32K a 200K tokens y el tiempo de primera respuesta
baja de 1.8s a 0.6s en la configuración por defecto, según los números
publicados por la empresa. La API mantiene compatibilidad con la
versión anterior.

Disponible desde hoy en beta abierta, sin waitlist. Precio: N/D, la
empresa no publicó tarifas para el tier extendido.

No resuelve el costo de inferencia en contextos largos: el precio por
token sigue siendo el mismo, así que 200K tokens cuestan 200K tokens.

Sirve si ya estabas partiendo documentos a mano para entrar en 32K.

@fabian128k
#IA #Lanzamiento #Desarrollo #InteligenciaArtificial #API
```
