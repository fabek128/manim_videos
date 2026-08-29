# Template: post de lista / ranking

## Cuándo usarlo

Rankings, "los más usados", comparativas de herramientas o modelos.
Es el template que acompaña a las escenas tipo `lostops`.

## Campos requeridos

| Campo | Descripción | Obligatorio |
|---|---|---|
| `criterio` | Qué mide el ranking, exactamente | Sí |
| `periodo` | Ventana temporal de los datos | Sí |
| `fuente_datos` | De dónde salen las métricas | Sí |
| `items` | Lista ordenada con nombre + métrica | Sí |
| `metodologia` | Cómo se ordenó y qué queda afuera | Sí |

Sin `criterio` y `fuente_datos` el ranking no se publica. Un top sin
método declarado es una opinión disfrazada de dato.

## Coherencia con el JSON del video

Cuando existe una escena de video con su JSON en
`tenants/<id>/videos/<slug>/json/`, el caption **debe** derivarse de ese
JSON, no de memoria. Leer el archivo real antes de escribir.

Campos típicos del JSON: `nombre`, `logo`, `etiqueta_metrica`,
`valor_metrica`, `comentario`, `specs`, `puesto`.

## Estructura del caption

```
[GANCHO — el criterio y el período, máx 125 caracteres]

[EL TOP — una línea por item:
N. Nombre — métrica — nota breve]

[LECTURA — 2 a 3 oraciones. El patrón que se ve en los datos.]

[METODOLOGÍA — una línea. Fuente y ventana temporal.]

[CIERRE — pregunta sobre el uso real del lector.]

[HANDLE]
[HASHTAGS]
```

## Longitud y tono

- Caption: 700–1400 caracteres.
- La métrica siempre con su unidad. "2M descargas", no "2M".
- Empates y datos faltantes se declaran: `N/D`, nunca se rellenan.
- No comparar métricas de distinta naturaleza como si fueran la misma.

## Mapeo al YAML

Para placa única con el podio:

```yaml
content:
  title: "<CRITERIO EN MAYÚSCULAS>"
  highlights: ["<el criterio>"]
  subtitle: "<periodo> · Fuente: <fuente_datos>"
  bullets:
    - "1. <nombre> — <valor_metrica>"
    - "2. <nombre> — <valor_metrica>"
    - "3. <nombre> — <valor_metrica>"
  footer_text: "<brand.name>"
```

Para carrusel, un slide por puesto:

| Slide | Tipo | Contenido |
|---|---|---|
| 1 | `cover` | Criterio + período |
| 2..N+1 | `text` | Un item por slide |
| N+2 | `bullets` | Lectura y metodología |

## Ejemplo

```
Los modelos más usados de la semana, por descargas en el hub.

1. Modelo A — 2.4M descargas — sigue liderando por integración por defecto
2. Modelo B — 1.1M descargas — crece por costo de inferencia
3. Modelo C — 890K descargas — fuerte en tareas de código
4. Modelo D — 410K descargas — nicho, contexto largo

El patrón se repite: el primer puesto no gana por calidad bruta, gana
por estar cableado como default en las librerías más instaladas. La
distancia entre el primero y el segundo es mayor que entre el segundo y
el cuarto.

Datos del 18 al 24 de agosto de 2026, descargas reportadas por el hub.

¿Cuál usás vos en producción?

@fabian128k
#IA #Modelos #OpenSource #InteligenciaArtificial #Desarrollo
```
