"""Generador de "Noticias de la semana" — 100% data-driven desde JSON.

Clon del generador de tops "Los más usados" (`videos/lostops/`) adaptado a
formato noticias: mismo motor de countdown, mismo layout y coreografía;
cambian los nombres de campo del JSON y las etiquetas por defecto para
encajar con "titular / fuente / resumen / datos" en vez de
"modelo / provider / comentario / specs". Se espera seguir ajustando
detalles particulares de este formato más adelante.

Los datos viven en `videos/noticias/json/YYYY-MM-DD_<slug>.json` (el nombre
ordena por fecha). Selección del JSON: variable de entorno TOP_JSON=<ruta>,
o si no está definida se usa el JSON más reciente de la carpeta (orden por
nombre). Esquema y ejemplos: videos/noticias/README.md.
"""

import json
import os
from pathlib import Path

from manim import *

from utils.theme import AGENTE32, ThemedScene

LOGOS_DIR = Path(__file__).parents[2] / "assets" / "logos"
SOUNDS_DIR = Path(__file__).parents[2] / "assets" / "sounds"
JSON_DIR = Path(__file__).parent / "json"
GRIS_TXT = "#B9B9B9"  # gris uniforme para textos secundarios
ORO = "#FFD700"  # color exclusivo del puesto #1


def _cargar_noticias() -> dict:
    """Devuelve el dict del top: TOP_JSON si está, o el JSON más reciente."""
    env = os.environ.get("TOP_JSON")
    if env:
        path = Path(env)
    else:
        candidatos = sorted(JSON_DIR.glob("*.json"))
        if not candidatos:
            raise FileNotFoundError(
                f"No hay JSONs en {JSON_DIR}. Creá uno (YYYY-MM-DD_slug.json) "
                "o apuntá TOP_JSON a un archivo."
            )
        path = candidatos[-1]  # YYYY-MM-DD_... → el último es el más nuevo
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _normalizar(top: dict) -> list[tuple]:
    """Convierte el JSON a las tuplas internas de la escena.

    (titular, logo, logo_path, etiqueta_dato, valor_dato, resumen, datos,
    destacado). El orden del array define el ranking: [0] es el #1.
    """
    noticias = []
    total = len(top["noticias"])
    for i, n in enumerate(top["noticias"]):
        datos = [tuple(d) for d in n.get("datos", [])]
        fuente = n.get("fuente")
        if fuente and not any(k.lower() == "fuente" for k, _ in datos):
            datos.insert(0, ("Fuente", fuente))
        dato = n.get("dato", {})
        if not isinstance(dato, dict):
            dato = {"valor": dato}
        noticias.append(
            (
                n["titular"],
                n.get("logo", n["titular"].lower().replace(" ", "_")),
                n.get("logo_path"),
                dato.get("etiqueta", "Fecha"),
                str(dato.get("valor", "")),
                tuple(n.get("resumen", ["", ""])),
                tuple(datos),
                bool(n.get("destacado", i == total - 1)),  # #1 por defecto
            )
        )
    return noticias


TOP = _cargar_noticias()
NOTICIAS = _normalizar(TOP)
PERIODO = TOP.get("subtitulo", "")
TITULO_LINEAS: tuple[str, ...] = tuple(
    TOP["titulo"] if isinstance(TOP.get("titulo"), list) else [TOP["titulo"]]
)


# Zonas muertas para la UI de Instagram (Reels/Stories), en píxeles del
# render final: franja superior e inferior donde la app superpone controles
# (nombre de cuenta, caption, audio). Ahí solo va fondo uniforme: nada de
# texto, logos ni gráfica. Ajustar estas dos variables para cambiar todo
# el layout de la escena de una vez.
ZONA_SUP_PX = 220
ZONA_INF_PX = 220


def _texto_par(clave: str, valor: str, fs_clave: int, fs_valor: int) -> VGroup:
    """Par clave (gris) + valor (blanco) alineados por línea de base."""
    k = Text(clave, font="Inter", font_size=fs_clave, color=GRIS_TXT)
    v = Text(valor, font="Inter", font_size=fs_valor, color="#FFFFFF")
    grupo = VGroup(k, v).arrange(RIGHT, buff=0.14)
    v.align_to(k, DOWN).shift(DOWN * 0.04)
    return grupo


class NoticiasSemana(ThemedScene):
    """Countdown desde la noticia menos relevante hasta la #1 destacada."""

    theme = AGENTE32

    def construct(self):
        # Música de fondo desde t=0. gain=15 porque los tracks del repo
        # tienen master muy bajo (ver skills/global.md §7 "Ganancia").
        # Placeholder heredado de lostops: cambiar el track cuando este
        # formato tenga su propia identidad sonora.
        self.add_sound(
            str(SOUNDS_DIR / "intros" / "fm_attack" / "FM Attack - Footprints 2.mp3"),
            gain=15,
        )

        # Límites de las zonas muertas, en unidades manim: NADA de contenido
        # por encima de _lim_sup ni por debajo de _lim_inf (solo fondo).
        fh = self.camera.frame_height
        u_px = fh / config.pixel_height  # unidades manim por píxel
        self.u_px = u_px  # conversión px→unidades para todo el diseño
        self._lim_sup = fh / 2 - ZONA_SUP_PX * u_px
        self._lim_inf = -fh / 2 + ZONA_INF_PX * u_px

        self._slots_colocados: list[Mobject] = []
        self._titulo_ref: Mobject | None = None

        # Orden del video: footer fijo → título → filas en countdown
        # (última noticia primero, #1 al final) → cierre con top nítido.
        self._footer()
        self._titulo()
        n = len(NOTICIAS)
        for i, m in enumerate(reversed(NOTICIAS)):
            (
                titular,
                logo_dir,
                logo_path,
                dato_lbl,
                dato_val,
                resumen,
                datos,
                destacado,
            ) = m
            self._fila(
                n - i,
                titular,
                logo_dir,
                logo_path,
                dato_lbl,
                dato_val,
                resumen,
                datos,
                destacado,
            )
        # Cierre: top completo nítido, sin difuminación.
        self._revelar_top()
        self.wait(4.5)  # hold de cierre antes del corte

    # ---------- secciones ----------

    def _titulo(self) -> None:
        fh = self.camera.frame_height
        # --- TÍTULO PRINCIPAL ---
        # 2 líneas en Space Grotesk bold (font_size=125); el tamaño final lo
        # fija set_width al 88% del frame, así que font_size es relativo.
        titulo = VGroup(
            *[
                MarkupText(
                    f"<b>{ln}</b>",
                    font="Space Grotesk",
                    font_size=125,
                    color=self.theme.primary,
                )
                for ln in TITULO_LINEAS
            ]
        ).arrange(DOWN, buff=0.3)
        titulo.width = config.frame_width * 0.88
        # --- SUBTÍTULO: SOLO el período ---
        periodo = Text(PERIODO, font="Inter", font_size=44, color=GRIS_TXT)
        # Bloque arranca en el CENTRO del video; tras 4s de lectura migra a
        # cabecera.
        grupo = VGroup(titulo, periodo).arrange(DOWN, buff=0.5)
        # Cap de alto: en formatos bajos (cuadrado/apaisado) el título no
        # puede comerse el espacio de la banda/grilla de slots.
        cap_alto = 0.32 * (fh - (ZONA_SUP_PX + ZONA_INF_PX) * self.u_px)
        if grupo.height > cap_alto:
            grupo.scale(cap_alto / grupo.height)
        grupo.move_to(ORIGIN)
        # TIEMPOS del título: aparece en el CENTRO, espera 4s de lectura y
        # recién entonces sube a cabecera (0.8s).
        self.play(FadeIn(grupo, shift=UP * 0.3), run_time=0.6)
        self._chequear_zonas("título centrado", grupo)
        self.wait(4)  # lectura en el centro
        # to_edge usa config.frame_y_radius (incorrecto en formato vertical);
        # posicionar manualmente respecto al alto real de la cámara.
        # Cabecera final: encoge a 80% y apoya su borde superior exactamente
        # en el límite de la zona muerta superior (ZONA_SUP_PX).
        objetivo = grupo.copy().scale(0.8)
        objetivo.shift(UP * (self._lim_sup - objetivo.get_top()[1]))
        self.play(Transform(grupo, objetivo), run_time=0.8)
        self._chequear_zonas("título cabecera", objetivo)
        self._titulo_ref = grupo  # el fondo desenfocable durante las filas

    def _chequear_zonas(self, nombre: str, *mobs: Mobject) -> None:
        """Falla ruidosamente si algo invade las zonas muertas de Instagram.

        Las franjas ZONA_SUP_PX / ZONA_INF_PX deben llevar solo fondo
        uniforme; cualquier texto, logo o chip ahí queda tapado por la UI.
        """
        for mo in mobs:
            if mo.get_top()[1] > self._lim_sup + 1e-6:
                raise ValueError(
                    f"{nombre}: invade la zona muerta superior "
                    f"(top {mo.get_top()[1]:.2f} > límite {self._lim_sup:.2f})"
                )
            if mo.get_bottom()[1] < self._lim_inf - 1e-6:
                raise ValueError(
                    f"{nombre}: invade la zona muerta inferior "
                    f"(bottom {mo.get_bottom()[1]:.2f} < límite {self._lim_inf:.2f})"
                )

    def _revelar_top(self) -> None:
        """Cierre: todo el ranking a plena opacidad, sin difuminación."""
        if not self._slots_colocados:
            return
        self.play(
            *[s.animate.set_opacity(1.0) for s in self._slots_colocados],
            run_time=0.6,
        )
        self._chequear_zonas("ranking final", *self._slots_colocados)

    def _fila(
        self,
        puesto: int,
        titular: str,
        logo_dir: str,
        logo_path: str | None,
        dato_lbl: str,
        dato: str,
        resumen: tuple[str, str],
        datos: tuple[tuple[str, str], ...],
        destacado: bool,
    ) -> None:
        """Fila con doble presentación: tarjeta centrada → slot ranking.

        `dato` = valor del dato destacado ya formateado (ej. "28 ago");
        Durante la lectura centrada, el fondo (ranking previo + título)
        queda fuera de foco (opacidad baja, pero siempre visible). Cuando
        la tarjeta vuela a su slot, el fondo vuelve a foco. Al terminar
        todas las filas, el top completo se revela nítido (_revelar_top).
        """
        accent = ORO if destacado else self.theme.accent
        color_borde = ORO if puesto == 1 else WHITE
        # ======================================================
        # TARJETA CENTRADA (presentación grande, ancho máximo)
        # ======================================================
        pad_h, pad_v = 0.55, 0.55
        chip_c_w = config.frame_width - 0.7  # margen 0.35u por lado

        logo_c = self._logo(logo_dir, logo_path)
        logo_c.height = min(1.05, logo_c.height)

        etiq_c = MarkupText(
            f'<span color="{accent}"><b>#{puesto}</b></span>'
            f'<span color="{self.theme.accent}">  {titular}</span>',
            font="Inter",
            font_size=64 if destacado else 52,
        )
        res_c = VGroup(
            *[
                MarkupText(f"<i>{ln}</i>", font="Inter", font_size=30, color=GRIS_TXT)
                for ln in resumen
            ]
        ).arrange(DOWN, buff=0.08)

        # Dato destacado: etiqueta gris + valor grande en acento.
        dato_lbl_c = Text(dato_lbl, font="Space Grotesk", font_size=34, color=GRIS_TXT)
        dato_val_c = Text(
            dato,
            font="Space Grotesk",
            font_size=64 if destacado else 54,
            color=accent,
        )
        dato_c = VGroup(dato_lbl_c, dato_val_c).arrange(RIGHT, buff=0.3)
        dato_lbl_c.align_to(dato_val_c, DOWN).shift(DOWN * 0.08)

        # Datos adicionales: columna de pares clave·valor, cada par centrado.
        datos_c = VGroup(*[_texto_par(k, v, 26, 30) for k, v in datos]).arrange(
            DOWN, buff=0.1
        )

        contenido_c = VGroup(logo_c, etiq_c, res_c, dato_c, datos_c).arrange(
            DOWN, buff=0.34
        )
        max_w = chip_c_w - 2 * pad_h
        if contenido_c.width > max_w:
            contenido_c.scale(max_w / contenido_c.width)
        chip_c_h = contenido_c.height + 2 * pad_v
        banda_util = (
            self.camera.frame_height
            - (ZONA_SUP_PX + ZONA_INF_PX) * self.u_px
            - self._footer_alto
            - 0.3
        )
        escala = min(1.0, banda_util / chip_c_h, max_w / contenido_c.width)
        chip_c = RoundedRectangle(
            corner_radius=0.18, width=chip_c_w, height=chip_c_h, stroke_width=2.5
        )
        chip_c.fill_color = self.theme.dark
        chip_c.set_fill(opacity=1.0 if destacado else 0.92)
        chip_c.set_stroke(color_borde, width=2.5)
        contenido_c.move_to(chip_c)
        tarjeta = VGroup(chip_c, contenido_c)
        if escala < 1.0:
            tarjeta.scale(escala)
        tarjeta.move_to(ORIGIN)
        # Clamp a las zonas muertas: si la tarjeta crece, se desplaza.
        exceso_sup = tarjeta.get_top()[1] - self._lim_sup
        if exceso_sup > 0:
            tarjeta.shift(DOWN * exceso_sup)
        exceso_inf = self._lim_inf - tarjeta.get_bottom()[1]
        if exceso_inf > 0:
            tarjeta.shift(UP * exceso_inf)

        # ======================================================
        # SLOT DEL RANKING (toda la info, alineación perfecta)
        # ======================================================
        n = len(NOTICIAS)
        fh = self.camera.frame_height
        fw = config.frame_width
        # Layout adaptativo: vertical → pila de slots; cuadrado/apaisado →
        # grilla de 2 columnas (una pila de 4 no entra en frames bajos).
        grid = fw >= fh
        cols = 2 if grid else 1
        filas = (n + cols - 1) // cols
        col_gap = 0.5
        chip_w = (fw - 2 * 0.35 - (cols - 1) * col_gap) / cols if grid else 11.5

        # Padding vertical por item, en px (constante entre formatos).
        slot_pad = 38 * self.u_px
        piso = self._lim_inf + self._footer_alto + 0.15  # techo del footer
        techo = (
            self._titulo_ref.get_bottom()[1]
            if self._titulo_ref is not None
            else self._lim_sup
        )

        pad_x, pad_v_s = 0.55, 0.26
        gap_ab = 0.2  # separación entre línea superior e inferior del chip

        # Dato destacado (se construye primero: su ancho acota al titular).
        dato_lbl_s = Text(dato_lbl, font="Space Grotesk", font_size=24, color=GRIS_TXT)
        dato_val_s = Text(
            dato,
            font="Space Grotesk",
            font_size=42 if destacado else 34,
            color=accent,
        )
        dato_s = VGroup(dato_lbl_s, dato_val_s).arrange(RIGHT, buff=0.2)
        dato_lbl_s.align_to(dato_val_s, DOWN).shift(DOWN * 0.05)

        # Titular: tamaño ajustado a su cantidad de caracteres (se re-escala
        # para caber entre el logo y el bloque de dato).
        etiqueta = MarkupText(
            f'<span color="{accent}"><b>#{puesto}</b></span>'
            f'<span color="{self.theme.accent}">  {titular}</span>',
            font="Inter",
            font_size=48 if destacado else 38,
        )
        logo = self._logo(logo_dir, logo_path)
        logo.width = min(1.5, logo.width)
        logo.height = min(0.8, logo.height)

        # Línea inferior: resumen (2 líneas, izq.) + datos (der.).
        res_s = VGroup(
            *[
                MarkupText(f"<i>{ln}</i>", font="Inter", font_size=23, color=GRIS_TXT)
                for ln in resumen
            ]
        ).arrange(DOWN, buff=0.05)
        datos_s = VGroup(
            *[
                MarkupText(
                    f'<span color="{GRIS_TXT}">{k}</span> '
                    f'<span color="#FFFFFF">{v}</span>',
                    font="Inter",
                    font_size=23,
                )
                for k, v in datos
            ]
        ).arrange(DOWN, buff=0.05, aligned_edge=RIGHT)
        # Presupuesto de ancho: el contenido de cada renglón se escala con
        # f_w; los gaps del layout (0.45 logo→titular, 0.5 titular→dato,
        # 0.4 resumen→datos) y el padding del chip son FIJOS (el
        # posicionamiento no los escala), así que van fuera de `contenido`.
        fijos = 0.45 + 0.5 + 0.4 + 2 * pad_x
        contenido = max(
            logo.width + etiqueta.width + dato_s.width,
            res_s.width + datos_s.width,
        )
        f_w = min(1.0, (chip_w - fijos) / contenido)
        if f_w < 1.0:
            for mo in (logo, etiqueta, dato_s, res_s, datos_s):
                mo.scale(f_w)

        # Alturas y fit de alto: filas*chip + padding entre título y footer
        # debe entrar en el alto disponible; si no, se escala el contenido.
        alto_a = max(logo.height, etiqueta.height, dato_s.height)
        alto_b = max(res_s.height, datos_s.height)
        chip_h = alto_a + gap_ab + alto_b + 2 * pad_v_s
        disp_h = techo - piso - (filas + 1) * slot_pad
        f_h = min(1.0, disp_h / (filas * chip_h))
        if f_h < 1.0:
            for mo in (logo, etiqueta, dato_s, res_s, datos_s):
                mo.scale(f_h)
            chip_h *= f_h
            alto_a *= f_h
            alto_b *= f_h

        # Posición: pila (1 columna) o grilla 2 columnas, con padding por
        # item anclado a título (techo) y footer (piso).
        top_y = techo - slot_pad - chip_h / 2
        bot_y = piso + slot_pad + chip_h / 2
        step_y = (top_y - bot_y) / (filas - 1) if filas > 1 else 0.0
        fila_i = (puesto - 1) // cols
        col_i = (puesto - 1) % cols
        y = top_y - fila_i * step_y
        x = (col_i - (cols - 1) / 2) * (chip_w + col_gap)
        chip = RoundedRectangle(
            corner_radius=0.14, width=chip_w, height=chip_h, stroke_width=2.5
        )
        chip.fill_color = self.theme.dark
        chip.set_fill(opacity=1.0 if destacado else 0.92)
        chip.set_stroke(color_borde, width=2.5)
        chip.move_to([x, y, 0])
        # Posiciones EXACTAS: una sola Y por línea → todo perfectamente
        y_a = y + chip_h / 2 - pad_v_s - alto_a / 2  # centro línea superior
        y_b = y_a - alto_a / 2 - gap_ab - alto_b / 2  # centro línea inferior
        logo.move_to([chip.get_left()[0] + pad_x + logo.width / 2, y_a, 0])
        etiqueta.next_to(logo, RIGHT, buff=0.45)
        etiqueta.set_y(y_a)
        dato_s.move_to([chip.get_right()[0] - pad_x - dato_s.width / 2, y_a, 0])

        res_s.move_to([chip.get_left()[0] + pad_x + res_s.width / 2, y_b, 0])
        datos_s.move_to([chip.get_right()[0] - pad_x - datos_s.width / 2, y_b, 0])

        slot = VGroup(chip, logo, etiqueta, dato_s, res_s, datos_s)
        # --- COREOGRAFÍA POR FILA ---
        # 1) El fondo (ranking ya colocado + título) pasa a fuera de foco:
        #    opacidad baja pero NUNCA desaparece (sigue visible, borroso).
        # 2) La tarjeta aparece CENTRADA, nítida, por encima de todo.
        # 3) 5s de lectura.
        # 4) Vuela (0.7s) a su slot; el fondo vuelve a foco (op. de reposo).
        fondo = list(self._slots_colocados)
        if self._titulo_ref is not None:
            fondo.append(self._titulo_ref)
        entrada: list[Animation] = [FadeIn(tarjeta, shift=UP * 0.4)]
        entrada += [s.animate.set_opacity(0.15) for s in fondo]
        self.play(*entrada, run_time=0.5)
        self.wait(5)  # lectura centrada
        self._chequear_zonas(f"tarjeta #{puesto}", tarjeta)
        vuelo: list[Animation] = [Transform(tarjeta, slot)]
        for s in self._slots_colocados:
            vuelo += [s[0].animate.set_opacity(0.55), s[1:].animate.set_opacity(0.5)]
        if self._titulo_ref is not None:
            vuelo.append(self._titulo_ref.animate.set_opacity(1.0))
        self.play(*vuelo, run_time=0.7)
        self._chequear_zonas(f"fila #{puesto}", tarjeta, slot)
        if destacado:
            # Pulso sutil del chip del #1: escala 1.05 ida y vuelta.
            self.play(
                tarjeta.animate(rate_func=there_and_back).scale(1.05),
                run_time=0.4,
            )
        self._slots_colocados.append(tarjeta)

    def _footer(self) -> None:
        """Logos agente32 + fabian128k en el pie (≤4% del alto)."""
        fh = self.camera.frame_height
        h_max = fh * 0.04  # techo del footer: ≤4% del alto total
        logos = []
        for d in ("agente32", "fabian128k"):
            svg = LOGOS_DIR / d / f"{d}_paths.svg"
            lo = SVGMobject(str(svg))
            lo.height = h_max * 0.7  # cada logo, un poco bajo el techo
            logos.append(lo)
        grupo = VGroup(*logos).arrange(RIGHT, buff=0.8)
        # Apoya el borde inferior de los logos en el límite de la zona
        # muerta inferior (ZONA_INF_PX): nada del footer entra ahí.
        grupo.move_to([0, self._lim_inf + grupo.height / 2, 0])
        self._footer_alto = grupo.height  # la banda de filas lo descuenta
        self._chequear_zonas("footer", grupo)
        self.add(grupo)

    def _logo(self, logo_dir: str, logo_path: str | None) -> Mobject:
        """Logo SVG por asset (logo_dir) o path explícito (logo_path JSON)."""
        if logo_path:
            svg_path = Path(logo_path)
            if not svg_path.is_absolute():
                svg_path = Path(__file__).parents[2] / logo_path
        else:
            svg_path = LOGOS_DIR / logo_dir / f"{logo_dir}_paths.svg"
        if svg_path.exists():
            try:
                return SVGMobject(str(svg_path))
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] SVG {svg_path} falló ({exc}); uso monograma")
        # Sin SVG disponible: monograma = inicial de la FUENTE (logo_dir) en
        # Inter sobre chip 0.85u.
        mono = Text(
            logo_dir[0].upper(), font="Inter", font_size=40, color=self.theme.primary
        )
        bg = Square(side_length=0.85)
        bg.set_fill(self.theme.dark, 1).set_stroke(self.theme.primary, 2)
        return VGroup(bg, mono.move_to(bg))
