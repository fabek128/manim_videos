# Manim en formato vertical (9:16): el bug de `frame_y_radius`

Al renderizar con resolución vertical (`--resolution 1080,1920`), **`config.frame_height`
sigue reportando 8.0u** (valor derivado del ancho horizontal). El alto real de la cámara
es 25.28u y solo se obtiene con:

```python
fh = self.camera.frame_height   # 25.28u en vertical; config.frame_height miente (=8.0)
```

## Síntomas

- Mobjects posicionados con `config.frame_height` quedan amontonados al centro o fuera
  de pantalla.
- Peor aún: helpers que usan internamente `config.frame_y_radius` — como
  `.to_edge(UP)` o `.to_corner(...)` — posicionan respecto a un frame de 8u de alto.
  En un render de 25.28u eso deja elementos "flotando" a mitad de pantalla aunque el
  código parezca correcto.

Ejemplo real: `grupo.animate.to_edge(UP)` movió el título a +2.48u (≈4.0 − altura/2),
donde quedaría en un frame horizontal, no arriba del frame vertical real.

## Regla

En cualquier escena que pueda renderizarse en vertical:

1. Nunca usar `config.frame_width` / `config.frame_height` para layout.
2. Leer siempre `self.camera.frame_width` / `self.camera.frame_height`.
3. Desconfiar de helpers que asumen el frame completo (`to_edge`, `to_corner`,
   `next_to(frame, ...)`); posicionar manualmente si hace falta.

Referencia de implementación correcta:
`videos/losmas/scene.py` (`_titulo`, `_fila`, `_footer`).
