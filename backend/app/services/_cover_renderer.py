"""Cover renderer mixin for PageComposer.

Contains: _draw_cover_title, _create_vertical_gradient, _create_foil_texture,
_load_cover_font, _fit_font_to_width, _fit_font_to_width_v2, _draw_title_banner,
_draw_arc_text, _draw_rotated_char.

Split from page_composer.py for maintainability.
"""

from __future__ import annotations

import math

import numpy as np
import structlog
from PIL import Image, ImageDraw, ImageFont

logger = structlog.get_logger()


class _CoverRendererMixin:
    """Mixin providing cover rendering methods for PageComposer."""
    def _draw_cover_title(
        self,
        img: Image.Image,
        title_text: str,
        page_width_px: int,
        page_height_px: int,
        font_family: str,
        font_size_pt: int,
        font_color: str,
        arc_intensity: int,
        shadow_color: str,
        stroke_color: str,
        y_percent: float,
        dpi: int,
        preset: str = "premium",
        effect: str = "gold_shine",
        letter_spacing: int = 0,
        stroke_width_pct: float | None = None,
    ):
        """Kapak başlığını baskı‑kalitesinde çiz (2× supersample).

        Harf aralığı düzgün advance‑width ile hesaplanır.
        effect != "none" ise gradient + shine + glow efekti uygulanır.
        """
        from PIL import ImageColor, ImageFilter

        SSAA = 2
        preset_cfg = self._COVER_PRESETS.get(preset, self._COVER_PRESETS["premium"])

        W2 = page_width_px * SSAA
        H2 = page_height_px * SSAA

        # ── Font yükle (2× boyut) ──
        base_font_px = max(16, int(font_size_pt * dpi / 72))
        font_px_2x = base_font_px * SSAA
        letter_sp_2x = letter_spacing * SSAA

        font_path = _resolve_font_path(font_family)
        font = self._load_cover_font(font_path, font_px_2x, font_family)

        # Türkçe glyph fallback
        if _text_needs_turkish(title_text) and font_path and not _font_supports_turkish(font_path):
            for _fb_name in _TURKISH_FALLBACK_FONTS:
                _fb_path = _resolve_font_path(_fb_name)
                if _fb_path and _font_supports_turkish(_fb_path):
                    try:
                        font = ImageFont.truetype(_fb_path, font_px_2x)
                        font_path = _fb_path
                        logger.warning("Cover title Turkish fallback → '%s'", _fb_name)
                        break
                    except OSError:
                        continue

        # ── Fit‑to‑width: letter_spacing dahil hesapla ──
        max_text_w = int(W2 * 0.80)
        font, font_px_2x = self._fit_font_to_width_v2(
            font, font_path, font_px_2x, title_text, max_text_w, letter_sp_2x,
        )

        # ── Safe area ──
        y_pct = max(6.0, y_percent)
        start_y_2x = int(H2 * y_pct / 100)

        # Metin sarma
        lines = self._wrap_text_v2(title_text, font, max(1, max_text_w - 20), letter_sp_2x)

        # Satır yüksekliği
        try:
            _bbox = font.getbbox("Ay")
            line_h = int((_bbox[3] - _bbox[1]) * 1.35)
        except Exception:
            line_h = max(int(font_px_2x * 1.4), 1)
        line_h = max(line_h, 1)

        # Stroke kalınlığı: admin ayarı (stroke_width_pct) öncelikli, yoksa preset'ten al
        if stroke_width_pct is not None:
            stroke_pct = stroke_width_pct
        else:
            stroke_pct = preset_cfg.get("stroke_pct", 1.0)
        # stroke_pct == 0 → stroke kapalı (admin 0 yaptıysa zorla stroke basma)
        stroke_px_2x = int(W2 * stroke_pct / 100) if stroke_pct > 0 else 0

        # Effect config
        shine_cfg = self._SHINE_EFFECTS.get(effect) if effect != "none" else None
        if shine_cfg:
            stroke_color = shine_cfg["stroke_override"]

        # Arc
        arc_factor = max(0, min(100, arc_intensity)) / 100.0
        arc_depth_2x = int(line_h * arc_factor) if arc_factor > 0.01 else 0

        text_area_x_2x = (W2 - max_text_w) // 2

        logger.info(
            "Cover title render: preset=%s effect=%s lines=%d font_2x=%d stroke_2x=%d arc=%d ls=%d",
            preset, effect, len(lines), font_px_2x, stroke_px_2x, arc_intensity, letter_sp_2x,
        )

        # ── Transparent overlay at 2× ──
        overlay = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))

        # ── LAYER 1: Banner (premium only, efektte no_banner varsa atla) ──
        if preset_cfg.get("banner") and not (shine_cfg and shine_cfg.get("no_banner")):
            self._draw_title_banner(
                overlay, lines, font, max_text_w, text_area_x_2x,
                start_y_2x, line_h, arc_depth_2x,
                banner_color=preset_cfg.get("banner_color", (11, 27, 43)),
                banner_opacity=preset_cfg.get("banner_opacity", 0.32),
                pad_x=preset_cfg.get("banner_pad_x", 55) * SSAA,
                pad_y=preset_cfg.get("banner_pad_y", 30) * SSAA,
                radius=preset_cfg.get("banner_radius", 42) * SSAA,
                letter_spacing=letter_sp_2x,
            )

        # ── LAYER 2: Outer glow (shine efekti varsa) ──
        if shine_cfg and preset_cfg.get("shadow", True):
            glow_layer = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
            _gc = shine_cfg["glow_color"]
            _glow_fill = (*_gc[:3], 100)
            # Glow genişliği: stroke varsa stroke+extra, yoksa minimal
            _glow_stroke_w = stroke_px_2x + 4 * SSAA if stroke_px_2x > 0 else 3 * SSAA
            self._draw_arc_text(
                img=glow_layer, lines=lines,
                x=text_area_x_2x, width=max_text_w,
                font=font, font_color=_glow_fill,
                stroke_enabled=True, stroke_color=(*_gc[:3], 60),
                stroke_width_px=_glow_stroke_w,
                line_height=line_h, start_y=start_y_2x,
                text_align="center", arc_intensity=arc_intensity,
                letter_spacing=letter_sp_2x,
            )
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=18 * SSAA))
            overlay = Image.alpha_composite(overlay, glow_layer)

        # ── LAYER 3: Drop shadow ──
        if preset_cfg.get("shadow"):
            shadow_layer = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
            s_opacity = preset_cfg.get("shadow_opacity", 0.45)
            s_blur = preset_cfg.get("shadow_blur", 12) * SSAA
            s_y_off = preset_cfg.get("shadow_y_offset", 8) * SSAA

            try:
                _sc = ImageColor.getrgb(shadow_color)
            except Exception:
                _sc = (0, 0, 0)
            _shadow_fill = (*_sc[:3], int(255 * s_opacity))

            self._draw_arc_text(
                img=shadow_layer, lines=lines,
                x=text_area_x_2x, width=max_text_w,
                font=font, font_color=_shadow_fill,
                stroke_enabled=False, stroke_color="",
                stroke_width_px=0, line_height=line_h,
                start_y=start_y_2x + s_y_off,
                text_align="center", arc_intensity=arc_intensity,
                letter_spacing=letter_sp_2x,
            )
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=s_blur))
            overlay = Image.alpha_composite(overlay, shadow_layer)

        # ── LAYER 4: Stroke layer (ayrı çiz, altında kalsın) ──
        if preset_cfg.get("stroke", True) and stroke_px_2x > 0:
            stroke_layer = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
            try:
                _stk_c = ImageColor.getrgb(stroke_color)
            except Exception:
                _stk_c = (50, 30, 10)
            self._draw_arc_text(
                img=stroke_layer, lines=lines,
                x=text_area_x_2x, width=max_text_w,
                font=font, font_color=(*_stk_c[:3], 255),
                stroke_enabled=True, stroke_color=(*_stk_c[:3], 255),
                stroke_width_px=stroke_px_2x,
                line_height=line_h, start_y=start_y_2x,
                text_align="center", arc_intensity=arc_intensity,
                letter_spacing=letter_sp_2x,
            )
            overlay = Image.alpha_composite(overlay, stroke_layer)

        # ── LAYER 5: Main text (foil texture / gradient / solid) ──
        if shine_cfg:
            # a) Beyaz metin çiz → alpha mask al
            text_mask_layer = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
            self._draw_arc_text(
                img=text_mask_layer, lines=lines,
                x=text_area_x_2x, width=max_text_w,
                font=font, font_color=(255, 255, 255, 255),
                stroke_enabled=False, stroke_color="",
                stroke_width_px=0, line_height=line_h,
                start_y=start_y_2x,
                text_align="center", arc_intensity=arc_intensity,
                letter_spacing=letter_sp_2x,
            )
            alpha_mask = text_mask_layer.split()[3]  # A channel

            text_top = max(0, start_y_2x - 10)
            text_bottom = min(H2, start_y_2x + len(lines) * line_h + arc_depth_2x + 10)

            if shine_cfg.get("foil_texture"):
                # ── Prosedürel altın yaldız dokusu ──
                foil_img = self._create_foil_texture(
                    W2, H2, text_top, text_bottom,
                    base_color=shine_cfg.get("foil_base", (212, 175, 55)),
                    light_color=shine_cfg.get("foil_light", (255, 223, 100)),
                    dark_color=shine_cfg.get("foil_dark", (139, 101, 8)),
                    spec_color=shine_cfg.get("foil_spec", (255, 250, 205)),
                )
                foil_img.putalpha(alpha_mask)
                overlay = Image.alpha_composite(overlay, foil_img)
            else:
                # Basit gradient fill (rainbow vs)
                gradient_strip = self._create_vertical_gradient(
                    W2, H2, text_top, text_bottom, shine_cfg["gradient"],
                )
                gradient_strip.putalpha(alpha_mask)
                overlay = Image.alpha_composite(overlay, gradient_strip)

                # Highlight shine band
                hl_layer = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
                hl_draw = ImageDraw.Draw(hl_layer)
                hl_y = text_top + (text_bottom - text_top) // 4
                hl_h = max(4, (text_bottom - text_top) // 6)
                hl_color = (*shine_cfg["highlight_color"][:3], 140)
                hl_draw.rectangle([0, hl_y, W2, hl_y + hl_h], fill=hl_color)
                hl_layer = hl_layer.filter(ImageFilter.GaussianBlur(radius=max(3, hl_h // 2)))
                hl_alpha = hl_layer.split()[3]
                combined_alpha = Image.new("L", (W2, H2), 0)
                combined_alpha.paste(hl_alpha, mask=alpha_mask)
                hl_layer.putalpha(combined_alpha)
                overlay = Image.alpha_composite(overlay, hl_layer)
        else:
            # Düz renk metin (efekt yok)
            text_layer = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
            self._draw_arc_text(
                img=text_layer, lines=lines,
                x=text_area_x_2x, width=max_text_w,
                font=font, font_color=font_color,
                stroke_enabled=False, stroke_color="",
                stroke_width_px=0, line_height=line_h,
                start_y=start_y_2x,
                text_align="center", arc_intensity=arc_intensity,
                letter_spacing=letter_sp_2x,
            )
            overlay = Image.alpha_composite(overlay, text_layer)

        # ── Downsample 2× → 1× ──
        overlay_1x = overlay.resize((page_width_px, page_height_px), Image.Resampling.LANCZOS)

        # ── Composite onto original image ──
        img_rgba = img.convert("RGBA")
        img_rgba = Image.alpha_composite(img_rgba, overlay_1x)
        img.paste(img_rgba.convert("RGB"))

    @staticmethod
    def _create_vertical_gradient(
        width: int, height: int,
        top: int, bottom: int,
        colors: list[tuple],
    ) -> Image.Image:
        """Dikey gradient image oluştur (text bounding box alanında)."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if bottom <= top:
            return img

        n_stops = len(colors)
        if n_stops < 2:
            return img

        arr = np.zeros((height, width, 4), dtype=np.uint8)
        segment_h = (bottom - top) / (n_stops - 1)

        for y_px in range(top, min(bottom, height)):
            rel_y = y_px - top
            seg_idx = min(int(rel_y / segment_h), n_stops - 2)
            seg_t = (rel_y - seg_idx * segment_h) / max(1, segment_h)
            seg_t = max(0.0, min(1.0, seg_t))

            c1 = colors[seg_idx]
            c2 = colors[seg_idx + 1]
            r = int(c1[0] + (c2[0] - c1[0]) * seg_t)
            g = int(c1[1] + (c2[1] - c1[1]) * seg_t)
            b = int(c1[2] + (c2[2] - c1[2]) * seg_t)

            arr[y_px, :] = (r, g, b, 255)

        return Image.fromarray(arr, "RGBA")

    @staticmethod
    def _create_foil_texture(
        width: int, height: int,
        top: int, bottom: int,
        base_color: tuple = (212, 175, 55),
        light_color: tuple = (255, 223, 100),
        dark_color: tuple = (139, 101, 8),
        spec_color: tuple = (255, 250, 205),
    ) -> Image.Image:
        """Prosedürel metalik yaldız dokusu oluştur (altın/gümüş/bronz).

        Teknik:
        1. Ana altın rengi ile base layer
        2. Çapraz fırça darbeleri (brushed metal efekti)
        3. Dikey gradient (üstte parlak, altta koyu — 3D derinlik)
        4. Rastgele grain noise (metalik pürüz)
        5. Yatay specular highlight band (ışık yansıması)
        """
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if bottom <= top or bottom <= 0:
            return img

        h = bottom - top
        w = width

        # Float arrays for blending
        base = np.array(base_color, dtype=np.float32)
        light = np.array(light_color, dtype=np.float32)
        dark = np.array(dark_color, dtype=np.float32)
        spec = np.array(spec_color, dtype=np.float32)

        # 1) Dikey gradient: üst = light, orta-üst = base, orta-alt = base, alt = dark
        #    Daha parlak: üst %40 light ağırlıklı, alt sadece %20 dark
        arr = np.zeros((h, w, 3), dtype=np.float32)
        for y in range(h):
            t = y / max(1, h - 1)
            if t < 0.30:
                # Üst: light → base (parlak başlangıç)
                s = t / 0.30
                arr[y, :] = light * (1 - s) + base * s
            elif t < 0.70:
                # Orta geniş bant: base (ana altın rengi)
                arr[y, :] = base
            else:
                # Alt: base → (base*0.7 + dark*0.3) — çok kararmayacak
                s = (t - 0.70) / 0.30
                bottom_color = base * 0.65 + dark * 0.35
                arr[y, :] = base * (1 - s) + bottom_color * s

        # 2) Çapraz fırça darbeleri (brushed metal)
        np.random.seed(42)  # Deterministik
        for _ in range(max(1, h // 3)):
            y_pos = np.random.randint(0, h)
            thickness = np.random.randint(1, max(2, h // 30))
            brightness = np.random.uniform(-0.12, 0.12)
            y1 = max(0, y_pos - thickness)
            y2 = min(h, y_pos + thickness)
            arr[y1:y2, :] = np.clip(arr[y1:y2, :] * (1 + brightness), 0, 255)

        # 3) Fine grain noise (metalik pürüz)
        noise = np.random.uniform(-0.08, 0.08, (h, w, 1)).astype(np.float32)
        arr = np.clip(arr * (1 + noise), 0, 255)

        # 4) Birincil specular highlight band (yatay parlak şerit — üst %18-40)
        #    Daha geniş ve daha yoğun → belirgin ışıltı
        spec_y_start = int(h * 0.15)
        spec_y_end = int(h * 0.42)
        for y in range(spec_y_start, min(spec_y_end, h)):
            center = (spec_y_start + spec_y_end) / 2
            sigma = max(1, (spec_y_end - spec_y_start) / 2.8)
            intensity = np.exp(-0.5 * ((y - center) / sigma) ** 2) * 0.75
            arr[y, :] = arr[y, :] * (1 - intensity) + spec * intensity

        # 5) İkinci specular (alt %55-70 — orta yoğunluk)
        spec2_start = int(h * 0.55)
        spec2_end = int(h * 0.70)
        for y in range(spec2_start, min(spec2_end, h)):
            center = (spec2_start + spec2_end) / 2
            sigma = max(1, (spec2_end - spec2_start) / 3)
            intensity = np.exp(-0.5 * ((y - center) / sigma) ** 2) * 0.40
            arr[y, :] = arr[y, :] * (1 - intensity) + light * intensity

        # Build RGBA image
        result = np.zeros((height, width, 4), dtype=np.uint8)
        clamped = np.clip(arr, 0, 255).astype(np.uint8)
        result[top:bottom, :, :3] = clamped
        result[top:bottom, :, 3] = 255

        return Image.fromarray(result, "RGBA")

    # ── Helper: font loading ──
    @staticmethod
    def _load_cover_font(
        font_path: str | None, size_px: int, family_name: str
    ) -> ImageFont.FreeTypeFont:
        """Load font with fallback chain."""
        for try_px in (size_px, min(size_px, 800), 80):
            try_px = max(16, try_px)
            try:
                return ImageFont.truetype(font_path, try_px)
            except OSError:
                continue
        fallback = _resolve_font_path("Arial")
        try:
            return ImageFont.truetype(fallback, max(16, min(size_px, 800)))
        except OSError:
            return ImageFont.load_default()

    # ── Helper: fit font to max width (legacy) ──
    def _fit_font_to_width(
        self,
        font: ImageFont.FreeTypeFont,
        font_path: str | None,
        font_px: int,
        text: str,
        max_width: int,
    ) -> tuple[ImageFont.FreeTypeFont, int]:
        """Shrink font until single‑line text fits within max_width."""
        for _ in range(20):
            try:
                bbox = font.getbbox(text)
                text_w = bbox[2] - bbox[0]
            except Exception:
                break
            if text_w <= max_width or font_px <= 20:
                break
            font_px = int(font_px * 0.9)
            font_px = max(20, font_px)
            try:
                font = ImageFont.truetype(font_path, font_px)
            except OSError:
                break
        return font, font_px

    # ── Helper: fit font to max width v2 (advance width + letter spacing) ──
    def _fit_font_to_width_v2(
        self,
        font: ImageFont.FreeTypeFont,
        font_path: str | None,
        font_px: int,
        text: str,
        max_width: int,
        letter_spacing: int = 0,
    ) -> tuple[ImageFont.FreeTypeFont, int]:
        """Shrink font until text width (advance + letter_spacing) fits within max_width."""
        for _ in range(30):
            try:
                text_w = font.getlength(text) + letter_spacing * max(0, len(text) - 1)
            except Exception:
                try:
                    bbox = font.getbbox(text)
                    text_w = bbox[2] - bbox[0]
                except Exception:
                    break
            if text_w <= max_width or font_px <= 20:
                break
            font_px = int(font_px * 0.92)
            font_px = max(20, font_px)
            try:
                font = ImageFont.truetype(font_path, font_px)
            except OSError:
                break
        return font, font_px

    # ── Helper: draw banner / plaque behind text ──
    @staticmethod
    def _draw_title_banner(
        overlay: Image.Image,
        lines: list[str],
        font: ImageFont.FreeTypeFont,
        text_area_width: int,
        text_area_x: int,
        start_y: int,
        line_height: int,
        arc_depth: int,
        banner_color: tuple = (11, 27, 43),
        banner_opacity: float = 0.32,
        pad_x: int = 110,
        pad_y: int = 60,
        radius: int = 84,
        letter_spacing: int = 0,
    ):
        """Draw a semi‑transparent rounded rectangle behind the title text."""
        max_line_w = 0
        for ln in lines:
            try:
                w = font.getlength(ln) + letter_spacing * max(0, len(ln) - 1)
                max_line_w = max(max_line_w, int(w))
            except Exception:
                try:
                    _bbox = font.getbbox(ln)
                    max_line_w = max(max_line_w, _bbox[2] - _bbox[0])
                except Exception:
                    pass

        total_h = len(lines) * line_height + arc_depth
        center_x = text_area_x + text_area_width // 2

        # Banner rect
        bx1 = center_x - max_line_w // 2 - pad_x
        by1 = start_y - pad_y
        bx2 = center_x + max_line_w // 2 + pad_x
        by2 = start_y + total_h + pad_y

        # Clamp to image bounds
        bx1 = max(0, bx1)
        by1 = max(0, by1)
        bx2 = min(overlay.width, bx2)
        by2 = min(overlay.height, by2)

        banner_layer = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(banner_layer)
        fill = (*banner_color[:3], int(255 * banner_opacity))
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=radius, fill=fill)

        # Soft edge via slight blur
        from PIL import ImageFilter
        banner_layer = banner_layer.filter(ImageFilter.GaussianBlur(radius=max(4, radius // 6)))
        # Composite onto overlay
        _tmp = Image.alpha_composite(overlay, banner_layer)
        overlay.paste(_tmp)

    # ── Core arc text renderer (RGBA‑aware, advance‑width spacing) ──
    def _draw_arc_text(
        self,
        img: Image.Image,
        lines: list[str],
        x: int, width: int,
        font: ImageFont.FreeTypeFont,
        font_color: str | tuple,
        stroke_enabled: bool,
        stroke_color: str | tuple,
        stroke_width_px: int,
        line_height: int,
        start_y: int,
        text_align: str,
        arc_intensity: int = 35,
        letter_spacing: int = 0,
    ):
        """Metni kavisli (hilal/ark) şeklinde çiz.

        Harf genişlikleri getlength() (advance width) ile hesaplanır.
        letter_spacing: ekstra piksel aralık (her karakter arasına eklenir).
        """
        arc_factor = max(0, min(100, arc_intensity)) / 100.0
        arc_depth = int(line_height * arc_factor) if arc_factor > 0.01 else 0

        for line_idx, line in enumerate(lines):
            line_y_base = start_y + line_idx * line_height

            # ── Advance width ile karakter genişlikleri ──
            char_widths: list[float] = []
            for ch in line:
                try:
                    adv = font.getlength(ch)
                except Exception:
                    bbox = font.getbbox(ch)
                    adv = float(bbox[2] - bbox[0])
                char_widths.append(adv + letter_spacing)

            total_line_width = sum(char_widths)
            if total_line_width <= 0:
                continue

            if text_align == "center":
                start_x = x + (width - total_line_width) / 2
            elif text_align == "right":
                start_x = x + width - total_line_width - 10
            else:
                start_x = x + 10

            cursor_x = start_x
            for ch_idx, ch in enumerate(line):
                ch_w = char_widths[ch_idx]

                if total_line_width > 0:
                    char_center = cursor_x + ch_w / 2 - start_x
                    t = (char_center / total_line_width) * 2 - 1
                else:
                    t = 0

                dy = int(arc_depth * (t ** 2)) if arc_depth > 0 else 0
                max_rotation = 3.5 * (arc_factor if arc_factor > 0 else 0)
                rotation_deg = -t * max_rotation
                ch_y = line_y_base + dy

                if abs(rotation_deg) > 0.5 and arc_depth > 0:
                    self._draw_rotated_char(
                        img, ch, int(cursor_x), ch_y, font, font_color,
                        rotation_deg, stroke_enabled, stroke_color, stroke_width_px,
                    )
                else:
                    draw = ImageDraw.Draw(img)
                    if stroke_enabled and stroke_width_px > 0:
                        draw.text(
                            (int(cursor_x), ch_y), ch, font=font,
                            fill=font_color,
                            stroke_width=stroke_width_px,
                            stroke_fill=stroke_color,
                        )
                    else:
                        draw.text((int(cursor_x), ch_y), ch, font=font, fill=font_color)

                cursor_x += ch_w

    def _draw_rotated_char(
        self,
        img: Image.Image,
        char: str,
        cx: int, cy: int,
        font: ImageFont.FreeTypeFont,
        font_color: str,
        angle_deg: float,
        stroke_enabled: bool,
        stroke_color: str,
        stroke_width_px: int,
    ):
        """Tek bir karakteri belirli açıyla döndürüp resme yapıştır."""
        # Karakter boyutunu hesapla
        bbox = font.getbbox(char)
        ch_w = bbox[2] - bbox[0]
        ch_h = bbox[3] - bbox[1]
        padding = max(ch_w, ch_h) // 2 + stroke_width_px + 4

        # Geçici RGBA canvas (karakter + padding)
        tmp_size = (ch_w + 2 * padding, ch_h + 2 * padding)
        tmp = Image.new("RGBA", tmp_size, (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp)

        # Karakter pozisyonu (canvas ortasında)
        draw_x = padding - bbox[0]
        draw_y = padding - bbox[1]

        if stroke_enabled and stroke_width_px > 0:
            tmp_draw.text(
                (draw_x, draw_y), char, font=font,
                fill=font_color,
                stroke_width=stroke_width_px,
                stroke_fill=stroke_color,
            )
        else:
            tmp_draw.text((draw_x, draw_y), char, font=font, fill=font_color)

        # Döndür
        rotated = tmp.rotate(angle_deg, resample=Image.Resampling.BICUBIC, expand=False)

        # Resme yapıştır (alpha destekli)
        paste_x = cx - padding + bbox[0]
        paste_y = cy - padding + bbox[1]

        # Güvenli sınır kontrolü
        if paste_x + rotated.width > 0 and paste_y + rotated.height > 0:
            if paste_x < img.width and paste_y < img.height:
                if img.mode == "RGBA":
                    # RGBA katman: alpha_composite ile şeffaflığı koru
                    img.paste(rotated, (paste_x, paste_y), rotated)
                else:
                    # RGB image: eski yöntem
                    img_rgba = img.convert("RGBA")
                    img_rgba.paste(rotated, (paste_x, paste_y), rotated)
                    img.paste(img_rgba.convert("RGB"))

