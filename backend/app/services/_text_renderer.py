"""Text renderer mixin for PageComposer.

Contains: _draw_text (main text drawing), _wrap_text, _wrap_text_v2.

Split from page_composer.py for maintainability.
"""

from __future__ import annotations

import structlog
from PIL import Image, ImageDraw, ImageFont

logger = structlog.get_logger()


class _TextRendererMixin:
    """Mixin providing text rendering methods for PageComposer."""
    def _draw_text(
        self,
        img: Image.Image,
        text: str,
        x: int,
        y: int,
        width: int,
        height: int,
        font_family: str,
        font_size_pt: int,
        font_color: str,
        text_align: str,
        text_position: str,
        dpi: int,
        stroke_enabled: bool = False,
        stroke_color: str = "#FFFFFF",
        stroke_width: float = 1.0,
        bg_enabled: bool = True,
        bg_color: str = "#FFFFFF",
        bg_opacity: int = 230,
        bg_shape: str = "cloud",
        bg_blur: int = 50,
        bg_extend_top: int = 60,
        bg_extend_bottom: int = 15,
        bg_extend_sides: int = 6,
        bg_intensity: int = 100,
        font_weight: str = "normal",
        vertical_align: str = "bottom",
        line_height_ratio: float = 1.35,
        text_padding_px: int = 24,
        drop_shadow_enabled: bool = False,
        drop_shadow_opacity: float = 0.38,
        drop_shadow_blur: int = 12,
        drop_shadow_offset: tuple[int, int] = (3, 6),
    ):
        """Draw text on the image: optional scrim/gradient bg, stroke, drop shadow, padding."""
        draw = ImageDraw.Draw(img)

        # Convert pt to pixels (at given DPI); en az 10px olmalı yoksa yazı çizilmez
        font_size_px = max(10, int(font_size_pt * dpi / 72))

        # Cross-platform font yükleme: _resolve_font_path Windows/Linux uyumlu yol döner
        font_path = _resolve_font_path(font_family)
        logger.info("Font resolve: '%s' → '%s' weight=%s", font_family, font_path, font_weight)
        font = None
        for try_px in (font_size_px, min(font_size_px, 500), 50):
            if try_px < 10:
                try_px = 10
            try:
                font = ImageFont.truetype(font_path, try_px)
                if try_px != font_size_px:
                    logger.warning(
                        "Font loaded at %spx (requested %spx) for %s path=%s",
                        try_px, font_size_px, font_family, font_path,
                    )
                    font_size_px = try_px
                break
            except OSError:
                continue
        if font is None:
            fallback_path = _resolve_font_path("Arial")
            try:
                font = ImageFont.truetype(fallback_path, max(10, min(font_size_px, 500)))
                font_size_px = max(10, min(font_size_px, 500))
                logger.warning("Could not load %s (%s), using fallback %s", font_family, font_path, fallback_path)
            except OSError:
                font = ImageFont.load_default()
                font_size_px = 20
                logger.error("No truetype font available, using Pillow default (low quality text)")

        # ── Font Weight (variable font desteği) ──
        if font and font_weight and font_weight != "normal":
            _wght = {"light": 300, "bold": 700, "extrabold": 800, "black": 900}.get(font_weight)
            if _wght is None:
                try:
                    _wght = int(font_weight)
                except (ValueError, TypeError):
                    _wght = None
            if _wght is not None:
                try:
                    font.set_variation_by_axes([float(_wght)])
                    logger.info("Font weight set to %d via variable axes", _wght)
                except Exception:
                    # Variable font değilse veya axes yoksa, faux bold: stroke ile simüle et
                    if _wght >= 600 and not stroke_enabled:
                        stroke_enabled = True
                        stroke_color = font_color
                        stroke_width = max(stroke_width, 0.5 + (_wght - 400) / 600)
                        logger.info("Faux bold via stroke: weight=%d stroke_w=%.1f", _wght, stroke_width)

        # ── Türkçe Glyph Fallback ──
        # Metin ş/ğ/Å/Ä/İ/ı içeriyorsa ve font bunları render edemiyorsa otomatik fallback
        if _text_needs_turkish(text) and font_path and not _font_supports_turkish(font_path):
            _orig_family = font_family
            _found_fallback = False
            for _fb_name in _TURKISH_FALLBACK_FONTS:
                _fb_path = _resolve_font_path(_fb_name)
                if _fb_path and _fb_path != font_path and _font_supports_turkish(_fb_path):
                    try:
                        font = ImageFont.truetype(_fb_path, font_size_px)
                        font_path = _fb_path
                        _found_fallback = True
                        logger.warning(
                            "Turkish glyph fallback: '%s' cannot render ş/ğ, using '%s' (%s)",
                            _orig_family, _fb_name, _fb_path,
                        )
                        break
                    except OSError:
                        continue
            # Hiçbir Google Font çalışmadıysa sistem fontuna düş (DejaVu Türkçe destekler)
            if not _found_fallback:
                for _sys_path in (
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                ):
                    if os.path.isfile(_sys_path):
                        try:
                            font = ImageFont.truetype(_sys_path, font_size_px)
                            font_path = _sys_path
                            logger.warning(
                                "Turkish system font fallback: '%s' → '%s'",
                                _orig_family, _sys_path,
                            )
                            break
                        except OSError:
                            continue

        # Metin arkaplan gradient: admin panelden kontrol edilir
        if bg_enabled and text_position in ("overlay", "bottom"):
            _bg_r, _bg_g, _bg_b = self._hex_to_rgb(bg_color)
            _bg_max_alpha = min(255, max(0, bg_opacity))

            logger.info(
                "Gradient BG: color=%s rgb=(%d,%d,%d) opacity=%d shape=%s blur=%d ext_top=%d ext_bot=%d ext_sides=%d intensity=%d",
                bg_color, _bg_r, _bg_g, _bg_b, _bg_max_alpha, bg_shape, bg_blur,
                bg_extend_top, bg_extend_bottom, bg_extend_sides, bg_intensity,
            )

            alpha_mask = self._build_gradient_mask(
                img_size=img.size,
                x=x, y=y, width=width, height=height,
                shape=bg_shape,
                blur_radius=bg_blur,
                max_alpha=_bg_max_alpha,
                extend_top_pct=bg_extend_top,
                extend_bottom_pct=bg_extend_bottom,
                extend_sides_pct=bg_extend_sides,
                intensity_pct=bg_intensity,
            )

            # Renk katmanı + alpha mask → overlay
            color_layer = Image.new("RGBA", img.size, (_bg_r, _bg_g, _bg_b, 0))
            # Alpha mask'ı color_layer'ın alpha kanalına uygula
            color_layer.putalpha(alpha_mask)

            # Composite
            img_rgba = img.convert("RGBA")
            img.paste(Image.alpha_composite(img_rgba, color_layer).convert("RGB"))
            draw = ImageDraw.Draw(img)

        # İç padding ve güvenli alan (24px)
        pad = max(0, min(text_padding_px, width // 4, height // 4))
        inner_x = x + pad
        inner_y = y + pad
        inner_w = max(1, width - 2 * pad)
        inner_h = max(1, height - 2 * pad)

        wrap_width = max(1, inner_w - 1)
        lines = self._wrap_text(text, font, wrap_width)

        # Satır yüksekliği: font metrik * line_height_ratio (1.25–1.45)
        try:
            metric_bbox = font.getbbox("Ay")
            line_height = int((metric_bbox[3] - metric_bbox[1]) * line_height_ratio)
        except Exception:
            line_height = max(int(font_size_px * line_height_ratio), 1)
        if line_height < 1:
            line_height = max(int(font_size_px * line_height_ratio), 1)
        total_text_height = len(lines) * line_height

        # Dikey hizalama: top / center / bottom (padding içinde)
        if vertical_align == "top":
            start_y = inner_y
        elif vertical_align == "bottom":
            start_y = max(inner_y, inner_y + inner_h - total_text_height)
        else:
            start_y_raw = int(inner_y + (inner_h - total_text_height) / 2)
            start_y = max(inner_y, min(start_y_raw, inner_y + inner_h - total_text_height))

        stroke_width_px = max(0, int(stroke_width * dpi / 72)) if stroke_enabled else 0
        if stroke_enabled and stroke_width_px < 2 and dpi >= 150:
            stroke_width_px = max(2, int(4 * dpi / 300))
        logger.debug(
            "StoryTextOverlay: stroke=%s stroke_px=%s line_height_ratio=%s pad=%s",
            stroke_enabled, stroke_width_px, line_height_ratio, pad,
        )

        line_positions: list[tuple[int, int]] = []
        for i, line in enumerate(lines):
            line_y = start_y + i * line_height
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            if text_align == "center":
                line_x = int(inner_x + (inner_w - line_width) / 2)
            elif text_align == "right":
                line_x = int(inner_x + inner_w - line_width - 10)
            else:
                line_x = int(inner_x + 10)
            line_positions.append((line_x, line_y))

        # Drop shadow: tek katman, blur, sonra metin (çift çizim yok)
        if drop_shadow_enabled and lines and 0 < drop_shadow_opacity <= 1 and drop_shadow_blur > 0:
            from PIL import ImageFilter

            img_rgba = img.convert("RGBA")
            shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            dx, dy = drop_shadow_offset[0], drop_shadow_offset[1]
            for (lx, ly), line in zip(line_positions, lines):
                shadow_draw.text((lx + dx, ly + dy), line, font=font, fill=(0, 0, 0, 255))
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=min(drop_shadow_blur, 30)))
            arr = np.array(shadow_layer)
            arr[:, :, 3] = (arr[:, :, 3] * drop_shadow_opacity).astype(np.uint8)
            shadow_layer = Image.fromarray(arr)
            img_rgba = Image.alpha_composite(img_rgba, shadow_layer)
            img.paste(img_rgba.convert("RGB"))
            draw = ImageDraw.Draw(img)

        # Metin: stroke + fill (tek çizim)
        for (line_x, line_y), line in zip(line_positions, lines):
            if stroke_enabled and stroke_width_px > 0:
                draw.text(
                    (line_x, line_y),
                    line,
                    font=font,
                    fill=font_color,
                    stroke_width=stroke_width_px,
                    stroke_fill=stroke_color,
                )
            else:
                draw.text((line_x, line_y), line, font=font, fill=font_color)

    # =====================================================================
    #  COVER TITLE — Preset‑aware, supersampled, print‑ready
    # =====================================================================
    #  Presets:
    #    minimal  → strong stroke only
    #    classic  → stroke + blurred drop‑shadow
    #    premium  → stroke + blurred drop‑shadow + semi‑transparent banner
    # =====================================================================

    _COVER_PRESETS: dict[str, dict] = {
        "minimal": {
            "stroke": True,
            "shadow": False,
            "banner": False,
            "stroke_pct": 1.0,     # stroke = 1.0% of image width
        },
        "classic": {
            "stroke": True,
            "shadow": True,
            "banner": False,
            "stroke_pct": 1.0,
            "shadow_opacity": 0.45,
            "shadow_blur": 12,     # base blur px (scaled by SSAA)
            "shadow_y_offset": 8,  # base y offset px
        },
        "premium": {
            "stroke": True,
            "shadow": True,
            "banner": True,
            "stroke_pct": 0.9,
            "shadow_opacity": 0.40,
            "shadow_blur": 14,
            "shadow_y_offset": 10,
            "banner_color": (11, 27, 43),  # dark navy
            "banner_opacity": 0.32,
            "banner_pad_x": 55,
            "banner_pad_y": 30,
            "banner_radius": 42,
        },
    }

    # ── Parıltılı efekt renk paletleri ──
    _SHINE_EFFECTS: dict[str, dict] = {
        "gold_shine": {
            "gradient": [(255, 250, 205), (255, 223, 0), (218, 165, 32), (255, 223, 0), (255, 250, 205)],
            "highlight_color": (255, 255, 230),
            "glow_color": (255, 210, 60),
            "stroke_override": "#5C4000",
            "foil_texture": True,       # prosedürel altın yaldız dokusu
            "foil_base": (235, 195, 55),  # ana altın — daha parlak
            "foil_light": (255, 240, 120),  # parlak altın — daha canlı
            "foil_dark": (170, 120, 20),   # koyu altın — çok karartma
            "foil_spec": (255, 255, 220),  # specular highlight — daha beyaz
            "no_banner": True,
        },
        "silver_shine": {
            "gradient": [(255, 255, 255), (192, 192, 192), (128, 128, 128), (192, 192, 192), (255, 255, 255)],
            "highlight_color": (255, 255, 255),
            "glow_color": (200, 200, 255),
            "stroke_override": "#2F2F3F",
            "foil_texture": True,
            "foil_base": (192, 192, 192),
            "foil_light": (240, 240, 255),
            "foil_dark": (100, 100, 110),
            "foil_spec": (255, 255, 255),
            "no_banner": True,
        },
        "bronze_shine": {
            "gradient": [(255, 222, 173), (205, 133, 63), (139, 69, 19), (205, 133, 63), (255, 222, 173)],
            "highlight_color": (255, 240, 220),
            "glow_color": (200, 150, 80),
            "stroke_override": "#3D1F00",
            "foil_texture": True,
            "foil_base": (180, 120, 60),
            "foil_light": (230, 180, 100),
            "foil_dark": (100, 60, 20),
            "foil_spec": (255, 230, 180),
            "no_banner": True,
        },
        "rainbow": {
            "gradient": [(255, 107, 107), (254, 202, 87), (72, 219, 251), (255, 159, 243), (84, 160, 255)],
            "highlight_color": (255, 255, 255),
            "glow_color": (200, 200, 255),
            "stroke_override": "#1A1A3E",
            "foil_texture": False,
        },
    }

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        """Wrap text to fit within max_width. max_width en az 1 olmalı."""
        max_width = max(1, max_width)
        words = text.split()
        lines: list[str] = []
        current_line: list[str] = []

        for word in words:
            test_line = " ".join(current_line + [word])
            try:
                line_width = font.getlength(test_line)
            except Exception:
                bbox = font.getbbox(test_line)
                line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _wrap_text_v2(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int, letter_spacing: int = 0,
    ) -> list[str]:
        """Wrap text with getlength + letter_spacing hesabı."""
        max_width = max(1, max_width)
        words = text.split()
        lines: list[str] = []
        current_line: list[str] = []

        def _line_w(s: str) -> float:
            try:
                base = font.getlength(s)
            except Exception:
                bbox = font.getbbox(s)
                base = float(bbox[2] - bbox[0])
            return base + letter_spacing * max(0, len(s) - 1)

        for word in words:
            test_line = " ".join(current_line + [word])
            if _line_w(test_line) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

