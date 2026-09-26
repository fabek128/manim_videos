from __future__ import annotations

from pathlib import Path

from manim import (
    BLACK,
    DOWN,
    ORIGIN,
    RIGHT,
    UP,
    WHITE,
    VGroup,
    Group,
    ImageMobject,
    MarkupText,
    Rectangle,
    RoundedRectangle,
    Square,
    SVGMobject,
    Text,
    config,
)

from noticia_carrusel.backgrounds import select_random_background

from .context import TopRenderContext
from .models import TopItem

# Las zonas seguras Instagram (safe_*_px) están calibradas para el lienzo
# vertical 1080x1920. En renders más bajos (landscape 16:9, previews -ql) los
# px absolutos consumen casi todo el alto y el layout colapsa: se clampean a
# una fracción máxima del alto del render. El tope queda justo por encima de
# la mayor fracción de los formatos soportados (3:4 = 15.3%), de modo que
# 9:16 y 3:4 quedan intactos y solo se ajustan los casos que hoy fallan.
ZONA_SEGURA_MAX_FRACCION = 0.16


def _zona_segura_px(safe_px: float, pixel_height: int) -> float:
    """Zona muerta en px, clampeada a ZONA_SEGURA_MAX_FRACCION del alto."""
    return min(float(safe_px), ZONA_SEGURA_MAX_FRACCION * pixel_height)


class TopComposer:
    """Compone el ranking desde TopSpec y lo anima con tokens de TopStyle."""

    def __init__(self, context: TopRenderContext) -> None:
        self.context = context
        self.spec = context.spec
        self.style = context.style
        self.tenant = context.tenant
        self.rng = context.rng
        # Estado de render (se inicializa en render)
        self.u_px: float = 0.0
        self._lim_sup: float = 0.0
        self._lim_inf: float = 0.0
        self._alto_zonas_u: float = 0.0
        self._footer_alto: float = 0.0
        self._slots_colocados: list = []
        self._titulo_ref = None
        self._fondo_path: Path | None = None

    # ---------- helpers ----------

    def _resolve_background(self) -> Path | None:
        ref = self.spec.background_image_path
        if ref:
            # Intentar tal cual, luego con prefijo backgrounds/
            candidates = [Path(ref)]
            if not Path(ref).parts or Path(ref).parts[0] != "backgrounds":
                candidates.append(Path("backgrounds") / Path(ref))
            last_exc: Exception | None = None
            for cand in candidates:
                try:
                    return self.tenant.resolve_asset(str(cand))
                except (ValueError, FileNotFoundError) as exc:
                    last_exc = exc
                    continue
            raise FileNotFoundError(f"No existe el fondo configurado: {ref} ({last_exc})")
        # Pool combinado tenant+global, elección reproducible vía seed
        return select_random_background(self.tenant, self.rng)

    def _resolve_audio(self) -> tuple[Path, float]:
        asset = self.spec.audio.asset
        gain = float(self.spec.audio.gain_db)
        # audio.asset es relativo a assets/, ej: sounds/intros/SunsetDrift.mp3
        path = self.tenant.resolve_asset(asset)
        return path, gain

    def _logo(self, item: TopItem) -> object:
        visual = item.visual_asset
        # Monograma fallback
        def _monogram(label: str) -> VGroup:
            # label: primera letra del name o visual_asset
            ch = (label.strip() or "?")[0].upper()
            mono = Text(ch, font="Inter", font_size=40, color=self._primary())
            bg = Square(side_length=0.85)
            bg.set_fill(self._dark(), 1).set_stroke(self._primary(), 2)
            return VGroup(bg, mono.move_to(bg))

        if not visual:
            return _monogram(item.name)

        # URL remota → monograma (no descargar en render Manim)
        if visual.startswith("http://") or visual.startswith("https://"):
            return _monogram(item.name)

        # Intentar resolver como asset
        # shorthand: "openai" → "logos/openai/openai_paths.svg"
        candidates: list[str] = []
        if "/" in visual:
            candidates.append(visual)
            # Si ya es logos/..._paths.svg probar tal cual
        else:
            candidates.append(f"logos/{visual}/{visual}_paths.svg")
            candidates.append(f"logos/{visual}.svg")
            candidates.append(f"logos/{visual}/{visual}.png")
            candidates.append(f"logos/{visual}/{visual}.webp")
            candidates.append(f"logos/{visual}/{visual}.jpg")

        for cand in candidates:
            try:
                p = self.tenant.resolve_asset(cand)
            except (ValueError, FileNotFoundError):
                continue
            if not p.is_file():
                continue
            try:
                if p.suffix.lower() == ".svg":
                    return SVGMobject(str(p))
                if p.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}:
                    return ImageMobject(str(p))
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] Logo {p} falló ({exc}); pruebo otro asset")
        return _monogram(visual if "/" not in visual else item.name)

    def _item_specs(self, item: TopItem) -> tuple[tuple[str, str], ...]:
        """Convierte specs + secondary_text a tuplas (label, value) para el layout."""
        specs: list[tuple[str, str]] = [(r.label, r.value) for r in item.specs]
        if item.secondary_text:
            # Evitar duplicar si ya hay un spec con ese valor
            if not any(v == item.secondary_text for _, v in specs):
                # Compatibilidad con datos migrados de provider → etiqueta Provider
                # Para datos nuevos, el label genérico "Info" es neutro
                # Si specs ya tiene Provider, no duplicar
                has_provider = any(k.lower() == "provider" for k, _ in specs)
                label = "Provider" if has_provider is False and specs else "Info"
                # Si hay specs, insertar al inicio para mantener proveedor primero
                # Si no hay specs, crear uno
                specs.insert(0, (label, item.secondary_text))
        return tuple(specs)

    def _primary(self) -> str:
        # Theme primary se resuelve dinámicamente desde utils.theme según style.theme_name
        from utils.theme import AGENTE32, DEFAULT

        name = self.style.theme_name
        if name == "theme_agente32":
            return AGENTE32.primary
        if name == "theme_default":
            return DEFAULT.primary
        # fallback
        return DEFAULT.primary

    def _accent(self) -> str:
        from utils.theme import AGENTE32, DEFAULT

        name = self.style.theme_name
        if name == "theme_agente32":
            return AGENTE32.accent
        return DEFAULT.accent

    def _dark(self) -> str:
        from utils.theme import AGENTE32, DEFAULT

        name = self.style.theme_name
        if name == "theme_agente32":
            return AGENTE32.dark
        return DEFAULT.dark

    def _texto_par(self, clave: str, valor: str, fs_clave: int, fs_valor: int) -> VGroup:
        k = Text(clave, font="Inter", font_size=fs_clave, color=self.style.secondary_text_color)
        v = Text(valor, font="Inter", font_size=fs_valor, color="#FFFFFF")
        grupo = VGroup(k, v).arrange(RIGHT, buff=0.14)
        v.align_to(k, DOWN).shift(DOWN * 0.04)
        return grupo

    def _chequear_zonas(self, nombre: str, *mobs) -> None:  # type: ignore[no-untyped-def]
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

    # ---------- secciones manim ----------

    def _fondo(self, scene, path: Path) -> None:  # type: ignore[no-untyped-def]
        imagen = ImageMobject(str(path))
        imagen.height = scene.camera.frame_height
        # Cover: si escalando por alto no cubre el ancho (fondo vertical en
        # landscape), escalar por ancho; el overflow se recorta centrado.
        if imagen.width < scene.camera.frame_width:
            imagen.width = scene.camera.frame_width
        imagen.move_to(ORIGIN)
        imagen.set_opacity(self.style.background_image_opacity)
        velo = Rectangle(
            width=scene.camera.frame_width,
            height=scene.camera.frame_height,
            stroke_width=0,
        )
        velo.set_fill(BLACK, opacity=self.style.background_overlay_opacity)
        velo.move_to(ORIGIN)
        scene.add(imagen, velo)

    def animar_titulo(self, scene) -> None:  # type: ignore[no-untyped-def]
        fh = scene.camera.frame_height
        titulo = VGroup(
            *[
                MarkupText(
                    f"<b>{ln}</b>",
                    font="Space Grotesk",
                    font_size=125,
                    color=self._primary(),
                )
                for ln in self.spec.title
            ]
        ).arrange(DOWN, buff=0.3)
        titulo.width = config.frame_width * self.style.horizontal_usable_ratio
        periodo = Text(self.spec.subtitle, font="Inter", font_size=44, color=self.style.secondary_text_color)
        grupo = VGroup(titulo, periodo).arrange(DOWN, buff=0.5)
        ancho_max = config.frame_width * self.style.horizontal_usable_ratio
        if grupo.width > ancho_max:
            grupo.scale(ancho_max / grupo.width)
        cap_alto = 0.32 * (fh - self._alto_zonas_u)
        if grupo.height > cap_alto:
            grupo.scale(cap_alto / grupo.height)
        grupo.move_to(ORIGIN)
        objetivo = grupo.copy().scale(self.style.title_header_scale)
        objetivo.shift(UP * (self._lim_sup - objetivo.get_top()[1]))
        self._chequear_zonas("título centrado", grupo)
        self._chequear_zonas("título cabecera", objetivo)
        scene.ingreso_titulo_top(
            grupo,
            objetivo,
            shift=(0.0, self.style.title_entry_shift_y, 0.0),
            entrada_time=self.style.title_entry_time,
            hold_time=self.style.title_hold_time,
            traslado_time=self.style.title_header_time,
        )
        self._titulo_ref = grupo

    def agregar_footer(self, scene) -> None:  # type: ignore[no-untyped-def]
        fh = scene.camera.frame_height
        h_max = fh * 0.04
        # Footer logos desde manifest.brand.footer_logos o brand.logo
        manifest = self.tenant.manifest
        # Intentar obtener footer_logos si existe (manifest genérico)
        footer_assets: list[str] = []
        # BrandManifest puede tener footer_logos opcional (añadido en migración)
        brand_data = manifest.brand.model_dump() if hasattr(manifest.brand, "model_dump") else {}
        raw_footer = brand_data.get("footer_logos")
        if isinstance(raw_footer, (list, tuple)) and raw_footer:
            footer_assets = [str(x) for x in raw_footer]
        else:
            footer_assets = [manifest.brand.logo]
        # Fallback extra: si brand.logo es el único y tenant es agente32, incluir fabian
        # Para no hardcodear, solo usar lo declarado

        logos = []
        for asset in footer_assets:
            try:
                p = self.tenant.resolve_asset(asset)
            except (ValueError, FileNotFoundError):
                continue
            try:
                lo = SVGMobject(str(p))
            except Exception:
                continue
            lo.height = h_max * 0.7
            logos.append(lo)
        if not logos:
            # Sin logos no se dibuja footer
            self._footer_alto = 0.0
            return
        grupo = VGroup(*logos).arrange(RIGHT, buff=0.8)
        ancho_max = config.frame_width * self.style.horizontal_usable_ratio
        if grupo.width > ancho_max:
            grupo.scale(ancho_max / grupo.width)
        grupo.move_to([0, self._lim_inf + grupo.height / 2, 0])
        self._footer_alto = grupo.height
        self._chequear_zonas("footer", grupo)
        scene.add(grupo)


    def animar_tarjeta_puesto(self, scene, puesto: int, item: TopItem) -> None:  # type: ignore[no-untyped-def]
        destacado = puesto == 1
        accent = self.style.highlighted_rank_color if destacado else self._accent()
        color_borde = self.style.highlighted_rank_color if destacado else WHITE

        # Métrica
        met_lbl = item.metric.label if item.metric else "Valor"
        met_val = item.metric.value if item.metric else ""
        comentario = tuple(item.comment) if item.comment else ("", "")
        specs = self._item_specs(item)

        # Tarjeta centrada
        pad_h, pad_v = 0.55, 0.55
        chip_c_w = config.frame_width * self.style.horizontal_usable_ratio

        logo_c = self._logo(item)  # type: ignore[arg-type]
        try:
            logo_c.height = min(1.05, logo_c.height)  # type: ignore[union-attr]
        except Exception:
            pass

        etiq_c = MarkupText(
            f'<span color="{accent}"><b>#{puesto}</b></span>'
            f'<span color="{self._accent()}">  {item.name}</span>',
            font="Inter",
            font_size=64 if destacado else 52,
        )
        com_c = VGroup(
            *[
                MarkupText(
                    f"<i>{ln}</i>",
                    font="Inter",
                    font_size=self.style.central_comment_font_size,
                    color=self.style.secondary_text_color,
                )
                for ln in comentario
            ]
        ).arrange(DOWN, buff=0.08)

        tok_lbl_c = Text(met_lbl, font="Space Grotesk", font_size=34, color=self.style.secondary_text_color)
        tok_num_c = Text(
            met_val,
            font="Space Grotesk",
            font_size=64 if destacado else 54,
            color=accent,
        )
        tokens_c = VGroup(tok_lbl_c, tok_num_c).arrange(RIGHT, buff=0.3)
        tok_lbl_c.align_to(tok_num_c, DOWN).shift(DOWN * 0.08)

        specs_c = (
            VGroup(
                *[
                    self._texto_par(
                        k,
                        v,
                        self.style.central_spec_label_font_size,
                        self.style.central_spec_value_font_size,
                    )
                    for k, v in specs
                ]
            ).arrange(DOWN, buff=0.1)
            if specs
            else VGroup()
        )

        contenido_c = Group(logo_c, etiq_c, com_c, tokens_c, specs_c).arrange(
            DOWN, buff=0.34
        )
        max_w = chip_c_w - 2 * pad_h
        max_h = max(0.01, self.style.central_card_height - 2 * pad_v)
        if contenido_c.width > max_w:
            contenido_c.scale(max_w / contenido_c.width)
        if contenido_c.height > max_h:
            contenido_c.scale(max_h / contenido_c.height)
        chip_c_h = self.style.central_card_height
        banda_util = (
            scene.camera.frame_height
            - self._alto_zonas_u
            - self._footer_alto
            - 0.3
        )
        escala = min(1.0, banda_util / chip_c_h)
        chip_c = RoundedRectangle(
            corner_radius=0.18, width=chip_c_w, height=chip_c_h, stroke_width=2.5
        )
        chip_c.fill_color = self._dark()
        chip_c.set_fill(opacity=self.style.central_card_fill_opacity)
        chip_c.set_stroke(color_borde, width=2.5)
        contenido_c.move_to(chip_c)
        tarjeta = Group(chip_c, contenido_c)
        if escala < 1.0:
            tarjeta.scale(escala)
        tarjeta.move_to(ORIGIN)
        exceso_sup = tarjeta.get_top()[1] - self._lim_sup
        if exceso_sup > 0:
            tarjeta.shift(DOWN * exceso_sup)
        exceso_inf = self._lim_inf - tarjeta.get_bottom()[1]
        if exceso_inf > 0:
            tarjeta.shift(UP * exceso_inf)

        # Slot ranking
        n = len(self.spec.items)
        fh = scene.camera.frame_height
        fw = config.frame_width
        grid = fw >= fh
        cols = 2 if grid else 1
        filas = (n + cols - 1) // cols
        col_gap = 0.5
        ancho_util = fw * self.style.horizontal_usable_ratio
        chip_w = (
            (ancho_util - (cols - 1) * col_gap) / cols
            if grid
            else ancho_util
        )

        slot_pad = 38 * self.u_px
        piso = self._lim_inf + self._footer_alto + 0.15
        techo = (
            self._titulo_ref.get_bottom()[1]
            if self._titulo_ref is not None
            else self._lim_sup
        )

        pad_x, pad_v_s = 0.55, 0.26
        gap_ab = 0.2

        tok_lbl = Text(met_lbl, font="Space Grotesk", font_size=24, color=self.style.secondary_text_color)
        tok_num = Text(
            met_val,
            font="Space Grotesk",
            font_size=42 if destacado else 34,
            color=accent,
        )
        tokens_s = VGroup(tok_lbl, tok_num).arrange(RIGHT, buff=0.2)
        tok_lbl.align_to(tok_num, DOWN).shift(DOWN * 0.05)

        etiqueta = MarkupText(
            f'<span color="{accent}"><b>#{puesto}</b></span>'
            f'<span color="{self._accent()}">  {item.name}</span>',
            font="Inter",
            font_size=48 if destacado else 38,
        )
        logo = self._logo(item)  # type: ignore[arg-type]
        try:
            logo.width = min(1.5, logo.width)  # type: ignore[union-attr]
            logo.height = min(0.8, logo.height)  # type: ignore[union-attr]
        except Exception:
            pass

        comentario_slot = comentario if self.style.ranking_show_comments else ()
        specs_slot = specs if self.style.ranking_show_specs else ()
        com_s = VGroup(
            *[
                MarkupText(f"<i>{ln}</i>", font="Inter", font_size=23, color=self.style.secondary_text_color)
                for ln in comentario_slot
            ]
        ).arrange(DOWN, buff=0.05)
        specs_s = VGroup(
            *[
                MarkupText(
                    f'<span color="{self.style.secondary_text_color}">{k}</span> '
                    f'<span color="#FFFFFF">{v}</span>',
                    font="Inter",
                    font_size=23,
                )
                for k, v in specs_slot
            ]
        ).arrange(DOWN, buff=0.05, aligned_edge=RIGHT)
        fijos = 0.45 + 0.5 + 0.4 + 2 * pad_x
        contenido = max(
            logo.width + etiqueta.width + tokens_s.width,  # type: ignore[union-attr]
            com_s.width + specs_s.width,
        )
        f_w = min(1.0, (chip_w - fijos) / contenido) if contenido else 1.0
        if f_w < 1.0:
            for mo in (logo, etiqueta, tokens_s, com_s, specs_s):
                mo.scale(f_w)

        alto_a = max(logo.height, etiqueta.height, tokens_s.height)  # type: ignore[union-attr]
        alto_b = max(com_s.height, specs_s.height)
        chip_h = self.style.ranking_card_height
        gap_contenido = gap_ab if alto_b > 0 else 0.0
        contenido_h = alto_a + gap_contenido + alto_b
        limite_contenido_h = max(0.01, chip_h - 2 * pad_v_s)
        f_contenido_h = (
            min(1.0, limite_contenido_h / contenido_h) if contenido_h else 1.0
        )
        if f_contenido_h < 1.0:
            for mo in (logo, etiqueta, tokens_s, com_s, specs_s):
                mo.scale(f_contenido_h)
            alto_a *= f_contenido_h
            alto_b *= f_contenido_h
            gap_contenido *= f_contenido_h
        disp_h = techo - piso - (filas + 1) * slot_pad
        f_h = min(1.0, disp_h / (filas * chip_h)) if chip_h else 1.0
        if f_h < 1.0:
            for mo in (logo, etiqueta, tokens_s, com_s, specs_s):
                mo.scale(f_h)
            chip_h *= f_h
            alto_a *= f_h
            alto_b *= f_h
            gap_contenido *= f_h

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
        chip.fill_color = self._dark()
        chip.set_fill(opacity=1.0 if destacado else 0.92)
        chip.set_stroke(color_borde, width=2.5)
        chip.move_to([x, y, 0])
        contenido_h = alto_a + gap_contenido + alto_b
        y_a = y + contenido_h / 2 - alto_a / 2
        y_b = y - contenido_h / 2 + alto_b / 2
        logo.move_to([chip.get_left()[0] + pad_x + logo.width / 2, y_a, 0])  # type: ignore[union-attr]
        etiqueta.next_to(logo, RIGHT, buff=0.45)
        etiqueta.set_y(y_a)
        tokens_s.move_to([chip.get_right()[0] - pad_x - tokens_s.width / 2, y_a, 0])

        com_s.move_to([chip.get_left()[0] + pad_x + com_s.width / 2, y_b, 0])
        specs_s.move_to([chip.get_right()[0] - pad_x - specs_s.width / 2, y_b, 0])

        slot = Group(chip, logo, etiqueta, tokens_s, com_s, specs_s)
        fondo = list(self._slots_colocados)
        atenuar_vuelo: list[tuple[object, float]] = []
        for s in self._slots_colocados:
            atenuar_vuelo.append((s[0], self.style.card_landed_chip_opacity))
            atenuar_vuelo.append((s[1:], self.style.card_landed_content_opacity))
        restaurar: list[object] = []
        self._chequear_zonas(f"tarjeta central #{puesto}", tarjeta)
        tarjeta_colocada = scene.ingreso_tarjeta_puesto(
            puesto,
            tarjeta,
            slot,
            atenuar_entrada=fondo,
            opacidad_entrada=self.style.card_entry_dim_opacity,
            atenuar_vuelo=atenuar_vuelo,
            restaurar_vuelo=restaurar,
            opacidad_restaurar=self.style.card_restore_opacity,
            pulso=self.style.card_highlight_pulse_factor if destacado else 0.0,
            pulso_time=self.style.card_highlight_pulse_time,
            shift=(0.0, self.style.card_entry_shift_y, 0.0),
            entrada_time=self.style.card_entry_time,
            espera_time=self.style.card_hold_time,
            vuelo_time=self.style.card_flight_time,
            vuelo_move_ratio=self.style.card_flight_move_ratio,
        )
        self._chequear_zonas(f"fila #{puesto}", tarjeta_colocada)
        self._slots_colocados.append(tarjeta_colocada)

    # ---------- API pública ----------

    def configurar_layout(self, scene) -> None:  # type: ignore[no-untyped-def]
        """Inicializa límites, zonas seguras y estado mutable del render."""
        fh = scene.camera.frame_height
        self.u_px = fh / config.pixel_height
        zona_sup_px = _zona_segura_px(self.style.safe_top_px, config.pixel_height)
        zona_inf_px = _zona_segura_px(self.style.safe_bottom_px, config.pixel_height)
        self._alto_zonas_u = (zona_sup_px + zona_inf_px) * self.u_px
        self._lim_sup = fh / 2 - zona_sup_px * self.u_px
        self._lim_inf = -fh / 2 + zona_inf_px * self.u_px
        self._slots_colocados = []
        self._titulo_ref = None

    def agregar_audio(self, scene) -> None:  # type: ignore[no-untyped-def]
        """Agrega el audio configurado, si el asset puede resolverse."""
        try:
            audio_path, gain = self._resolve_audio()
            scene.add_sound(str(audio_path), gain=gain)
        except (ValueError, FileNotFoundError) as exc:
            print(f"   ⚠ Audio no encontrado: {exc}")

    def agregar_fondo(self, scene) -> None:  # type: ignore[no-untyped-def]
        """Resuelve y compone el fondo configurado o seleccionado por seed."""
        try:
            fondo = self._resolve_background()
            self._fondo_path = fondo
            if fondo is not None:
                self._fondo(scene, fondo)
                print(f"   🖼️ Fondo: {fondo.name} (seed={self.context.seed})")
        except (ValueError, FileNotFoundError) as exc:
            print(f"   ⚠ Fondo no resuelto: {exc}")

    def animar_cierre(self, scene) -> None:  # type: ignore[no-untyped-def]
        """Revela filas, ejecuta la ola y mantiene el ranking final."""
        scene.revelar_top(
            self._slots_colocados,
            opacity=self.style.reveal_opacity,
            run_time=self.style.reveal_time,
        )
        self._chequear_zonas("ranking final", *self._slots_colocados)
        scene.play_scale_wave(
            self._slots_colocados,
            scale_factor=self.style.wave_scale_factor,
            transition_time=self.style.wave_transition_time,
            hold_time=self.style.wave_hold_time,
            between_items_time=self.style.wave_between_items_time,
            repetitions=self.style.wave_repetitions,
            reverse=self.style.wave_reverse,
        )
        self._chequear_zonas("ranking tras ola", *self._slots_colocados)
        scene.espera_final_top(
            float(self.spec.final_hold_seconds),
            min_frames=self.style.final_min_frames,
        )

    def animar_top_completo(self, scene) -> None:  # type: ignore[no-untyped-def]
        """Main del generador: ejecuta todas las etapas del top en orden."""
        self.configurar_layout(scene)
        self.agregar_audio(scene)
        self.agregar_fondo(scene)
        self.agregar_footer(scene)
        self.animar_titulo(scene)
        n = len(self.spec.items)
        for i, item in enumerate(reversed(self.spec.items)):
            puesto = n - i
            self.animar_tarjeta_puesto(scene, puesto, item)
        self.animar_cierre(scene)
