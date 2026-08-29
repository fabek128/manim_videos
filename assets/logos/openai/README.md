# Logo OpenAI (símbolo "knot")

- Fuente: Wikipedia / Wikimedia Commons, archivo `OpenAI_logo_2025_(symbol).svg`
  (descargado vía `https://en.wikipedia.org/wiki/Special:FilePath/OpenAI_logo_2025_(symbol).svg`).
- `openai_paths.svg`: SVG monocromático (path único), recoloreado a `fill="#FFFFFF"`
  en cada `<path>` y sin `stroke` (Manim pinta strokes residuales como halos).
- Regenerar: re-descargar la URL de arriba, aplicar el mismo sanitizado
  (`sed -i '' -e 's|<path |<path fill="#FFFFFF" |g' -e 's|stroke[^ ]*="[^"]*"||g'`).
