# Video "Demo zoom web" (engine=web)

Ejemplo mínimo del engine `web` (`web.yaml`, sin `scene.py`/Manim): captura
una URL con Playwright y anima un pan+zoom sobre esa captura con OpenCV,
codificado a MP4 con ffmpeg. Arquitectura completa: `docs/web-capture.md`,
`docs/web-capture-plan.md` (Fase E).

## Uso

```bash
python build.py --tenant agente32 --video demo-zoom-web --no-preview
```

`build.py` detecta `web.yaml` en la carpeta (no `scene.py`) y lo renderiza
con el motor de captura web en vez de invocar `manim`. El viewport y el fps
de captura siguen al formato/calidad pedidos por el comando — igual que una
escena Manim recibe `-r`/`--fps` — no lo que declara `web.yaml` (eso es solo
el default para invocar el módulo directamente, fuera de `build.py`).

Convive con escenas Manim: `python build.py --combine` puede concatenar este
clip con cualquier `ModelosSemana`/`NoticiasSemana` del tenant sin cambios en
`combine_videos()` (mismo `ffmpeg -f concat` que ya usa el repo).
