# Brief: Astra, el próximo modelo de OpenAI con capacidades críticas de ciberseguridad

- **Fecha de creación:** 2026-09-02
- **Tenant:** agente32
- **Estado:** en_curso para el lanzamiento; confirmado para el anuncio de capacidades

## Confirmado

- OpenAI afirma que Astra es el primer modelo de la compañía que alcanza el nivel **Critical** de capacidades de ciberseguridad bajo su Preparedness Framework.
- OpenAI afirma que Astra puede encontrar vulnerabilidades desconocidas y desarrollar cadenas de explotación en sistemas protegidos sin instrucciones paso a paso de una persona, con las herramientas y el acceso adecuados.
- En ExploitBench, Astra obtuvo 100% en la evaluación sobre desarrollo de exploits a partir de vulnerabilidades conocidas.
- En un benchmark interno con 20 vulnerabilidades de alta severidad, OpenAI afirma que Astra obtuvo mayores tasas de ejecución arbitraria de código que GPT-5.6 Sol usando menos tokens.
- OpenAI afirma que Astra descubrió y utilizó dos vulnerabilidades zero-day durante una evaluación; la empresa dice que está notificándolas a los responsables.
- El modelo no participó en el incidente de Hugging Face. OpenAI dice que incorporó las lecciones de ese incidente en sus salvaguardas.
- OpenAI implementó controles adicionales: rechazo de solicitudes cibernéticas dañinas, clasificadores de seguridad, monitoreo del razonamiento y las acciones, controles para usuarios de mayor riesgo y capacidad de detener actividad potencialmente no autorizada.
- La disponibilidad será **próxima**, pero las capacidades avanzadas de ciberseguridad tendrán acceso limitado inicialmente a testers y luego se ampliarán mediante Daybreak Blue.

## Sin confirmar

- Fecha exacta de lanzamiento: OpenAI solo dice "soon" / "pronto".
- Precio, límites de uso y disponibilidad general.
- System Card de Astra: se publicará al lanzamiento.
- Validación independiente de los resultados de benchmarks y de los dos zero-days.

## Contradicciones

- No hay contradicción directa entre los dos anuncios oficiales. El 7 de agosto OpenAI dijo que no podía descartar el nivel Critical; el 1 de septiembre afirmó que Astra alcanzaba formalmente ese umbral. Es una actualización de evaluación.

## Por qué importa

Astra marca un cambio de categoría en la evaluación pública de modelos de OpenAI: el problema ya no es solo qué puede hacer el sistema, sino quién puede usar esas capacidades y qué controles deben acompañarlas. El acceso limitado busca reducir abuso, pero también puede frenar tareas defensivas legítimas por falsos positivos o interrupciones automáticas.

## Fuentes

| URL | Medio | Fecha | Tipo |
|---|---|---|---|
| https://openai.com/index/path-to-astra/ | OpenAI — Path to Astra: critical capabilities and frontier safeguards | 2026-09-01 | primaria |
| https://openai.com/index/responding-next-frontier-critical-cyber-capabilities/ | OpenAI — Responding to the next frontier of critical cyber capabilities | 2026-08-07 | primaria |
| https://www.cnbc.com/2026/09/01/open-ai-astra-cyber-model.html | CNBC — OpenAI says Astra crosses Critical cybersecurity capability | 2026-09-01 | secundaria |
| https://www.bloomberg.com/news/articles/2026-09-01/openai-will-limit-access-to-new-astra-model-s-cybersecurity-features | Bloomberg — OpenAI will limit access to Astra cybersecurity features | 2026-09-01 | secundaria |

## Incidente del workflow

PromptGate devolvió respuestas truncadas, con campos no válidos o sin contenido
al intentar generar el informe estructurado y el caption. El texto de esta
pieza se completó manualmente a partir de las fuentes listadas, sin agregar
hechos no presentes en ellas. Reintentar la generación de caption cuando
PromptGate esté disponible.
