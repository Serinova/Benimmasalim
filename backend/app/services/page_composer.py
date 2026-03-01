"""Page Composer - Renders text on images according to page templates.

Uses centralized resolution calculation from resolution_calc.py.
NEVER hard-code pixel values here!

Architecture (sub-modules):
  _page_helpers.py    — font resolution, template config, dimension helpers
  _text_renderer.py   — _TextRendererMixin: draw_text, wrap_text
  _cover_renderer.py  — _CoverRendererMixin: cover title, foil, arc text
  page_composer.py    — PageComposer assembly (compose_page, batch, dedication)
"""

import base64
import io
import os
import platform
import subprocess
from typing import Any

import numpy as np
import structlog
from PIL import Image, ImageDraw, ImageFont

from app.models.book_template import PageTemplate
from app.services._cover_renderer import _CoverRendererMixin
from app.services._page_helpers import (
    _auto_trim_borders,
    _resolve_font_path,
    build_template_config,
    effective_page_dimensions_mm,
)
from app.services._text_renderer import _TextRendererMixin
from app.utils.resolution_calc import (
    A4_LANDSCAPE_HEIGHT_MM,
    A4_LANDSCAPE_WIDTH_MM,
    DEFAULT_DPI,
    mm_to_px,
)

logger = structlog.get_logger()

# Re-export for backward compatibility
__all__ = ["PageComposer", "build_template_config", "page_composer", "effective_page_dimensions_mm"]


class PageComposer(_CoverRendererMixin, _TextRendererMixin):
    """Composes final page images by rendering text on AI-generated images
    according to page template settings.

    Method groups (via mixins):
      _TextRendererMixin  → _draw_text, _wrap_text, _wrap_text_v2
      _CoverRendererMixin → _draw_cover_title, _create_foil_texture, etc.
    """

    def compose_page(
        self,
        image_base64: str,
        text: str,
        template_config: dict,
        page_width_mm: float = 297,
        page_height_mm: float = 210,
        dpi: int = DEFAULT_DPI,
    ) -> str:
        """
        Compose a final page by rendering text on the image.

        Args:
            image_base64: Base64 encoded AI-generated image
            text: Text content to render
            template_config: Page template configuration with:
                - text_position: "top", "bottom", "overlay", etc.
                - text_x_percent, text_y_percent: Position percentages
                - text_width_percent, text_height_percent: Size percentages
                - font_family, font_size_pt, font_color
                - text_align: "left", "center", "right"
                - background_color (for text area if not overlay)
            page_width_mm: Page width in mm
            page_height_mm: Page height in mm
            dpi: Output resolution

        Returns:
            Base64 encoded composed image
        """
        try:
            # Decode base64 image
            if "," in image_base64:
                image_data = base64.b64decode(image_base64.split(",")[1])
            else:
                image_data = base64.b64decode(image_base64)

            # Open image
            img = Image.open(io.BytesIO(image_data))

            # Calculate page size in pixels using centralized function
            # Include bleed for print-ready output
            bleed_mm = template_config.get("bleed_mm", 3.0)  # Default 3mm bleed
            page_width_px = mm_to_px(page_width_mm, bleed_mm=bleed_mm, dpi=dpi)
            page_height_px = mm_to_px(page_height_mm, bleed_mm=bleed_mm, dpi=dpi)

            logger.info(
                f"Page composer: creating canvas {page_width_px}x{page_height_px}px (from {page_width_mm}x{page_height_mm}mm + {bleed_mm}mm bleed)"
            )

            # Create final page canvas
            background_color = template_config.get("background_color", "#FFFFFF")
            final_page = Image.new("RGB", (page_width_px, page_height_px), background_color)

            def _pct(key: str, default: float) -> float:
                v = template_config.get(key, default)
                if v is None:
                    return default
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return default

            # Metin konumu: overscan, kırpma ve text_position bağımlı mantık için erken tanımla
            text_position = (template_config.get("text_position") or "bottom").lower()

            # Get image placement from template (coerce to float)
            # Default: resim tüm sayfayı kaplar (100x100%), metin üstte overlay olarak çizilir.
            img_x_pct = _pct("image_x_percent", 0.0)
            img_y_pct = _pct("image_y_percent", 0.0)
            img_width_pct = _pct("image_width_percent", 100.0)
            img_height_pct = _pct("image_height_percent", 100.0)

            # Calculate image position and size (box on canvas)
            img_x = int(page_width_px * img_x_pct / 100)
            img_y = int(page_height_px * img_y_pct / 100)
            box_w = max(1, int(page_width_px * img_width_pct / 100))
            box_h = max(1, int(page_height_px * img_height_pct / 100))
            # Kutu sayfa sınırını aşmasın
            box_w = min(box_w, page_width_px - img_x)
            box_h = min(box_h, page_height_px - img_y)
            if box_w < 1 or box_h < 1:
                box_w = max(1, page_width_px - img_x)
                box_h = max(1, page_height_px - img_y)

            # Otomatik kenar tespiti — AI'nin eklediği beyaz/siyah border'ları kırp
            img = _auto_trim_borders(img, tolerance=40, min_strip_px=3)

            src_w, src_h = img.size
            logger.info(
                "Page composer image: src=%sx%s box=%sx%s at (%s,%s) canvas=%sx%s",
                src_w, src_h, box_w, box_h, img_x, img_y, page_width_px, page_height_px,
            )

            # Oranı koru: kutuyu doldur + overscan (AI kenar boşluklarını kırp).
            # Kapak: 1.03 (başlık AI'da, hafif kırpma OK); iç sayfa: 1.05 (daha agresif).
            _is_cover_page = template_config.get("page_type", "inner") == "cover"
            _OVERSCAN = 1.03 if _is_cover_page else 1.05
            if src_w > 0 and src_h > 0 and box_w > 0 and box_h > 0:
                scale = max(box_w / src_w, box_h / src_h) * _OVERSCAN
                new_w = int(round(src_w * scale))
                new_h = int(round(src_h * scale))
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                crop_left = max(0, (new_w - box_w) // 2)
                crop_top = 0 if _is_cover_page else max(0, (new_h - box_h) // 2)
                crop_right = min(new_w, crop_left + box_w)
                crop_bottom = min(new_h, crop_top + box_h)
                img_cropped = img_resized.crop((crop_left, crop_top, crop_right, crop_bottom))
                final_page.paste(img_cropped, (img_x, img_y))
            elif box_w > 0 and box_h > 0:
                # Kaynak boş/hatalı; kutu yine de doldurulmaz (arka plan kalır)
                logger.warning("Page composer: source image size %sx%s, skipping paste", src_w, src_h)

            # Get text placement from template (coerce to float; konum şablondan)
            text_x_pct = _pct("text_x_percent", 5.0)
            text_y_pct = _pct("text_y_percent", 72.0)
            text_width_pct = _pct("text_width_percent", 90.0)
            text_height_pct = _pct("text_height_percent", 25.0)
            # text_position zaten yukarıda tanımlandı (overscan/kırpma için erken gerekli)

            # Calculate text area
            text_x = int(page_width_px * text_x_pct / 100)
            text_y = int(page_height_px * text_y_pct / 100)
            text_width = int(page_width_px * text_width_pct / 100)
            text_height = int(page_height_px * text_height_pct / 100)

            # Metin: şablonda açıkça False değilse True (iç sayfada hep yazı olsun)
            text_enabled = template_config.get("text_enabled", True)
            if isinstance(text_enabled, str):
                text_enabled = str(text_enabled).lower() not in ("false", "0", "no", "off")

            # Sadece kesin dosya yolu ise çizme (path gibi görünmeyen hikaye metni çizilsin)
            draw_text = (text or "").strip()
            if draw_text and (
                "workspaceStorage" in draw_text
                or (draw_text.startswith("file:///") and draw_text.count("/") > 3)
                or (len(draw_text) < 200 and draw_text.startswith("C:\\") and "\\" in draw_text and ".png" in draw_text)
            ):
                logger.warning(
                    "Page composer: skipping text that looks like file path (first 80 chars: %s)",
                    draw_text[:80],
                )
                draw_text = ""

            if not draw_text and (text or "").strip():
                logger.warning("Page composer: text empty after filter, original len=%s", len((text or "").strip()))
            if draw_text and not text_enabled:
                logger.info("Page composer: text skipped (text_enabled=False in template)")

            # ── Kapak Sayfası: WordArt başlık ──
            _cover_title_enabled = template_config.get("cover_title_enabled", True)
            # "gemini" modunda başlık zaten görselin içinde üretildi — overlay atlanır.
            _cover_title_source = template_config.get("cover_title_source", "gemini")
            if _is_cover_page and draw_text and _cover_title_enabled and _cover_title_source != "gemini":
                _ct_preset = template_config.get("cover_title_preset", "premium")
                _ct_font_family = template_config.get("cover_title_font_family") or "Lobster"
                _ct_font_size_pt = template_config.get("cover_title_font_size_pt", 48)
                _ct_font_color = template_config.get("cover_title_font_color") or "#FFD700"
                _ct_arc = template_config.get("cover_title_arc_intensity", 35)
                _ct_shadow_color = template_config.get("cover_title_shadow_color") or "#000000"
                _ct_stroke_c = template_config.get("cover_title_stroke_color") or "#8B6914"
                _ct_y_pct = template_config.get("cover_title_y_percent", 5.0)
                _ct_effect = template_config.get("cover_title_effect", "gold_shine")
                _ct_letter_sp = template_config.get("cover_title_letter_spacing", 0)
                _ct_stroke_w = template_config.get("cover_title_stroke_width")
                logger.info(
                    "Cover title WordArt: preset=%s effect=%s font=%s size=%s arc=%s letter_sp=%s stroke_w=%s",
                    _ct_preset, _ct_effect, _ct_font_family, _ct_font_size_pt, _ct_arc, _ct_letter_sp, _ct_stroke_w,
                )
                try:
                    self._draw_cover_title(
                        img=final_page,
                        title_text=draw_text,
                        page_width_px=page_width_px,
                        page_height_px=page_height_px,
                        font_family=_ct_font_family,
                        font_size_pt=_ct_font_size_pt,
                        font_color=_ct_font_color,
                        arc_intensity=_ct_arc,
                        shadow_color=_ct_shadow_color,
                        stroke_color=_ct_stroke_c,
                        y_percent=_ct_y_pct,
                        dpi=dpi,
                        preset=_ct_preset,
                        effect=_ct_effect,
                        letter_spacing=_ct_letter_sp,
                        stroke_width_pct=_ct_stroke_w,
                    )
                except Exception as e:
                    logger.exception("Page composer _draw_cover_title failed: %s", e)
                    raise
            # ── İç Sayfa: scrim + normal metin ──
            elif draw_text and text_enabled and not _is_cover_page:
                # Alt %35 scrim (siyah→şeffaf gradient) — metin okunurluğu
                self._draw_bottom_scrim(
                    final_page,
                    page_width_px,
                    page_height_px,
                    bottom_pct=0.35,
                    max_alpha_float=0.65,
                    blur_px=40,
                )
                # font_size_pt: şablondan al; admin ayarına saygı göster (min 8pt, max 732pt)
                _fs = template_config.get("font_size_pt", 14)
                font_size_pt = 14 if not isinstance(_fs, (int, float)) or _fs < 8 or _fs > 732 else int(_fs)
                font_size_pt = max(8, min(732, font_size_pt))
                font_size_px = int(font_size_pt * dpi / 72)
                logger.info(
                    "Page composer text: font_size_pt=%s, dpi=%s -> font_size_px=%s, "
                    "text_pos x%%=%s y%%=%s w%%=%s h%%=%s, canvas=%sx%s",
                    font_size_pt, dpi, font_size_px,
                    text_x_pct, text_y_pct, text_width_pct, text_height_pct,
                    page_width_px, page_height_px,
                )
                _font_family = template_config.get("font_family") or "Arial"
                _font_color = template_config.get("font_color") or "#2D2D2D"
                _font_weight = template_config.get("font_weight", "normal")
                _stroke_on = template_config.get("text_stroke_enabled", False)
                _stroke_color = template_config.get("text_stroke_color") or "#FFFFFF"
                _stroke_width = template_config.get("text_stroke_width", 1.0)
                logger.info(
                    "Page composer typography: family=%s color=%s stroke=%s stroke_color=%s stroke_w=%s",
                    _font_family, _font_color, _stroke_on, _stroke_color, _stroke_width,
                )
                try:
                    self._draw_text(
                        img=final_page,
                        text=draw_text,
                        x=text_x,
                        y=text_y,
                        width=text_width,
                        height=text_height,
                        font_family=_font_family,
                        font_size_pt=font_size_pt,
                        font_color=_font_color,
                        text_align=template_config.get("text_align", "center"),
                        text_position=text_position,
                        dpi=dpi,
                        stroke_enabled=_stroke_on,
                        stroke_color=_stroke_color,
                        stroke_width=_stroke_width,
                        bg_enabled=False,
                        bg_color=template_config.get("text_bg_color", "#FFFFFF"),
                        bg_opacity=template_config.get("text_bg_opacity", 230),
                        bg_shape=template_config.get("text_bg_shape", "cloud"),
                        bg_blur=template_config.get("text_bg_blur", 50),
                        bg_extend_top=template_config.get("text_bg_extend_top", 60),
                        bg_extend_bottom=template_config.get("text_bg_extend_bottom", 15),
                        bg_extend_sides=template_config.get("text_bg_extend_sides", 6),
                        bg_intensity=template_config.get("text_bg_intensity", 100),
                        font_weight=_font_weight,
                        vertical_align=template_config.get("text_vertical_align", "bottom"),
                        line_height_ratio=template_config.get("line_height", 1.35),
                        text_padding_px=24,
                        drop_shadow_enabled=True,
                        drop_shadow_opacity=0.38,
                        drop_shadow_blur=12,
                        drop_shadow_offset=(3, 6),
                    )
                except Exception as e:
                    logger.exception("Page composer _draw_text failed: %s", e)
                    raise
            elif text and not text_enabled:
                logger.debug("Text rendering skipped (text_enabled=False)")

            # Convert to base64 with 300 DPI metadata for print
            buffer = io.BytesIO()
            final_page.save(buffer, format="PNG", dpi=(300, 300))
            buffer.seek(0)

            composed_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{composed_base64}"

        except Exception as e:
            logger.error("Failed to compose page", error=str(e))
            # Return original image if composition fails
            return image_base64

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Hex rengi (r, g, b) tuple'a çevir."""
        h = hex_color.lstrip("#")
        try:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except (ValueError, IndexError):
            return 0, 0, 0

    @staticmethod
    def _draw_bottom_scrim(
        img: Image.Image,
        page_width_px: int,
        page_height_px: int,
        bottom_pct: float = 0.35,
        max_alpha_float: float = 0.65,
        blur_px: int = 40,
    ) -> None:
        """Sayfanın alt kısmına siyah→şeffaf gradient scrim çizer (metin okunurluğu).
        Scrim: altta rgba(0,0,0,0.55~0.70), yukarı doğru rgba(0,0,0,0). Yumuşak geçiş için blur.
        """
        from PIL import ImageFilter

        if bottom_pct <= 0 or max_alpha_float <= 0:
            return
        strip_top = int(page_height_px * (1.0 - bottom_pct))
        strip_bottom = page_height_px
        strip_h = strip_bottom - strip_top
        if strip_h <= 0:
            return

        scrim = Image.new("RGBA", (page_width_px, page_height_px), (0, 0, 0, 0))
        pix = np.array(scrim)
        max_alpha_uint8 = min(255, int(max_alpha_float * 255))
        for row in range(strip_top, strip_bottom):
            t = (row - strip_top) / strip_h
            t = t * t * (3.0 - 2.0 * t)
            alpha = int(max_alpha_uint8 * t)
            pix[row, :, 0] = 0
            pix[row, :, 1] = 0
            pix[row, :, 2] = 0
            pix[row, :, 3] = alpha

        scrim = Image.fromarray(pix)
        if blur_px > 0:
            scrim = scrim.filter(ImageFilter.GaussianBlur(radius=min(blur_px, 60)))
        img_rgba = img.convert("RGBA")
        img_rgba = Image.alpha_composite(img_rgba, scrim)
        img.paste(img_rgba.convert("RGB"))

    def _build_gradient_mask(
        self,
        img_size: tuple[int, int],
        x: int, y: int, width: int, height: int,
        shape: str,
        blur_radius: int,
        max_alpha: int,
        extend_top_pct: int = 60,
        extend_bottom_pct: int = 15,
        extend_sides_pct: int = 10,
        intensity_pct: int = 100,
    ) -> Image.Image:
        """Gradient alpha mask oluştur — şekle göre yumuşak geçişli çerçeve.

        Cloud shape: metin alanının tamamını kaplayan, ortada tam opak,
        kenarlara ve üste doğru yumuşak bulutsu geçiş.

        Args:
            extend_top_pct: Metin üstüne % uzantı (0=metin hizasında, 150=çok yukarı)
            extend_bottom_pct: Metin altına % uzantı
            extend_sides_pct: Yanlara % margin (0=kenara kadar, 30=çok dar)
            intensity_pct: İç alan yoğunluk (50=yarı saydam, 100=tam opak plato)
        """
        import math

        from PIL import ImageFilter

        iw, ih = img_size

        if shape == "cloud":
            # ── CLOUD: Admin-kontrollü beyaz bulut ──
            extend_top = int(height * max(0, min(200, extend_top_pct)) / 100)
            extend_bot = int(height * max(0, min(100, extend_bottom_pct)) / 100)
            # extend_sides: sayfa genişliğine göre % uzantı (her iki yana)
            extend_side_px = int(iw * max(0, min(50, extend_sides_pct)) / 100)

            area_top = max(0, y - extend_top)
            area_bot = min(ih, y + height + extend_bot)
            area_left = max(0, x - extend_side_px)
            area_right = min(iw, x + width + extend_side_px)
            area_h = area_bot - area_top
            area_w = area_right - area_left

            rows = np.arange(area_top, area_bot, dtype=np.float32)
            cols = np.arange(area_left, area_right, dtype=np.float32)
            if len(rows) == 0 or len(cols) == 0:
                return Image.new("L", img_size, 0)

            col_grid, row_grid = np.meshgrid(cols, rows)

            # Normalised coords [0..1] within the EXTENDED area
            col_n = (col_grid - area_left) / max(1, area_w)
            row_n = (row_grid - area_top) / max(1, area_h)

            # ── Vertical profile: plateau in text zone, short fade at edges ──
            text_top_n = (y - area_top) / max(1, area_h)
            text_bot_n = (y + height - area_top) / max(1, area_h)
            # Fade zones: sadece extend bölgesinin %60'ı fade, geri kalanı tam opak
            top_fade_start = max(0.0, text_top_n * 0.4)
            bot_fade_end = min(1.0, text_bot_n + (1.0 - text_bot_n) * 0.6)

            vert_alpha = np.ones_like(row_n, dtype=np.float32)
            # Top fade
            top_mask = row_n < text_top_n
            top_progress = np.clip(
                (row_n - top_fade_start) / max(0.01, text_top_n - top_fade_start),
                0.0, 1.0,
            )
            top_progress = top_progress * top_progress * (3.0 - 2.0 * top_progress)
            vert_alpha = np.where(top_mask, top_progress, vert_alpha)
            # Bottom fade
            bot_mask = row_n > text_bot_n
            bot_progress = np.clip(
                (bot_fade_end - row_n) / max(0.01, bot_fade_end - text_bot_n),
                0.0, 1.0,
            )
            bot_progress = bot_progress * bot_progress * (3.0 - 2.0 * bot_progress)
            vert_alpha = np.where(bot_mask, bot_progress, vert_alpha)

            # ── Horizontal edge fade: sadece en dış %5 fade, geri kalan tam opak ──
            edge_fade_pct = 0.05
            horiz_alpha = np.clip(
                np.minimum(col_n, 1.0 - col_n) / edge_fade_pct,
                0.0, 1.0,
            )
            horiz_alpha = horiz_alpha * horiz_alpha * (3.0 - 2.0 * horiz_alpha)

            # ── Multi-octave noise for organic cloud boundary ──
            noise = (
                np.sin(col_n * 5.7 + row_n * 4.3) * 0.03
                + np.sin(col_n * 11.3 + row_n * 9.7) * 0.02
                + np.sin(row_n * 7.1 + col_n * 3.1) * 0.02
            )

            intensity_factor = max(0.5, min(1.0, intensity_pct / 100.0))

            combined = vert_alpha * horiz_alpha * intensity_factor
            # Noise only at very edges
            edge_zone = combined < 0.85
            combined = np.where(
                edge_zone,
                np.clip(combined + noise, 0.0, 1.0),
                combined,
            )

            cloud_arr = np.zeros((ih, iw), dtype=np.uint8)
            result = np.clip(combined * max_alpha, 0, 255).astype(np.uint8)
            cloud_arr[area_top:area_bot, area_left:area_left + result.shape[1]] = result

            mask = Image.fromarray(cloud_arr)
            effective_blur = max(blur_radius, 15)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=effective_blur))
            return mask

        # ── Non-cloud shapes: extend/intensity parametreleri artık tümünde aktif ──
        extend_top = int(height * max(0, min(200, extend_top_pct)) / 100)
        extend_bot = int(height * max(0, min(100, extend_bottom_pct)) / 100)
        extend_side_px = int(iw * max(0, min(50, extend_sides_pct)) / 100)
        intensity_factor = max(0.5, min(1.0, intensity_pct / 100.0))

        area_top = max(0, y - extend_top)
        area_bot = min(ih, y + height + extend_bot)
        area_left = max(0, x - extend_side_px)
        area_right = min(iw, x + width + extend_side_px)
        area_h = area_bot - area_top
        area_w = area_right - area_left
        edge_fade_pct = 0.05

        if shape == "rectangle":
            rows = np.arange(area_top, area_bot, dtype=np.float32)
            cols = np.arange(area_left, area_right, dtype=np.float32)
            if len(rows) == 0 or len(cols) == 0:
                return Image.new("L", img_size, 0)

            col_grid, row_grid = np.meshgrid(cols, rows)
            col_n = (col_grid - area_left) / max(1, area_w)
            row_n = (row_grid - area_top) / max(1, area_h)

            text_top_n = (y - area_top) / max(1, area_h)
            text_bot_n = (y + height - area_top) / max(1, area_h)

            vert_alpha = np.ones_like(row_n, dtype=np.float32)
            top_mask = row_n < text_top_n
            top_progress = np.clip(row_n / max(0.01, text_top_n), 0.0, 1.0)
            vert_alpha = np.where(top_mask, top_progress, vert_alpha)
            bot_mask = row_n > text_bot_n
            bot_progress = np.clip((1.0 - row_n) / max(0.01, 1.0 - text_bot_n), 0.0, 1.0)
            vert_alpha = np.where(bot_mask, bot_progress, vert_alpha)

            combined = vert_alpha * intensity_factor
            rect_arr = np.zeros((ih, iw), dtype=np.uint8)
            result = np.clip(combined * max_alpha, 0, 255).astype(np.uint8)
            rect_arr[area_top:area_bot, area_left:area_left + result.shape[1]] = result
            mask = Image.fromarray(rect_arr)
            if blur_radius > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            return mask

        elif shape == "rounded":
            rows = np.arange(area_top, area_bot, dtype=np.float32)
            cols = np.arange(area_left, area_right, dtype=np.float32)
            if len(rows) == 0 or len(cols) == 0:
                return Image.new("L", img_size, 0)

            col_grid, row_grid = np.meshgrid(cols, rows)
            col_n = (col_grid - area_left) / max(1, area_w)
            row_n = (row_grid - area_top) / max(1, area_h)

            text_top_n = (y - area_top) / max(1, area_h)
            text_bot_n = (y + height - area_top) / max(1, area_h)

            vert_alpha = np.ones_like(row_n, dtype=np.float32)
            top_mask = row_n < text_top_n
            top_progress = np.clip(row_n / max(0.01, text_top_n), 0.0, 1.0)
            vert_alpha = np.where(top_mask, top_progress, vert_alpha)
            bot_mask = row_n > text_bot_n
            bot_progress = np.clip((1.0 - row_n) / max(0.01, 1.0 - text_bot_n), 0.0, 1.0)
            vert_alpha = np.where(bot_mask, bot_progress, vert_alpha)

            horiz_alpha = np.clip(np.minimum(col_n, 1.0 - col_n) / edge_fade_pct, 0.0, 1.0)

            combined = vert_alpha * horiz_alpha * intensity_factor
            rounded_arr = np.zeros((ih, iw), dtype=np.uint8)
            result = np.clip(combined * max_alpha, 0, 255).astype(np.uint8)
            rounded_arr[area_top:area_bot, area_left:area_left + result.shape[1]] = result

            corner_r = max(20, min(area_w, area_h) // 6)
            corner_mask = Image.new("L", img_size, 0)
            cd = ImageDraw.Draw(corner_mask)
            cd.rounded_rectangle(
                [area_left, area_top, area_right, area_bot],
                radius=corner_r,
                fill=255,
            )
            if blur_radius > 0:
                corner_mask = corner_mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            mask = Image.fromarray(np.minimum(rounded_arr, np.array(corner_mask)))
            return mask

        elif shape == "soft_vignette":
            rows = np.arange(area_top, area_bot, dtype=np.float32)
            cols = np.arange(area_left, area_right, dtype=np.float32)
            if len(rows) == 0 or len(cols) == 0:
                return Image.new("L", img_size, 0)

            col_grid, row_grid = np.meshgrid(cols, rows)
            col_n = (col_grid - area_left) / max(1, area_w)
            row_n = (row_grid - area_top) / max(1, area_h)

            text_top_n = (y - area_top) / max(1, area_h)
            text_bot_n = (y + height - area_top) / max(1, area_h)

            vert_alpha = np.ones_like(row_n, dtype=np.float32)
            top_mask = row_n < text_top_n
            top_progress = np.clip(row_n / max(0.01, text_top_n), 0.0, 1.0)
            top_progress = top_progress * top_progress * (3.0 - 2.0 * top_progress)
            vert_alpha = np.where(top_mask, top_progress, vert_alpha)
            bot_mask = row_n > text_bot_n
            bot_progress = np.clip((1.0 - row_n) / max(0.01, 1.0 - text_bot_n), 0.0, 1.0)
            bot_progress = bot_progress * bot_progress * (3.0 - 2.0 * bot_progress)
            vert_alpha = np.where(bot_mask, bot_progress, vert_alpha)

            horiz_alpha = np.clip(np.minimum(col_n, 1.0 - col_n) / edge_fade_pct, 0.0, 1.0)
            horiz_alpha = horiz_alpha * horiz_alpha * (3.0 - 2.0 * horiz_alpha)

            combined = vert_alpha * horiz_alpha * intensity_factor
            vig_arr = np.zeros((ih, iw), dtype=np.uint8)
            result = np.clip(combined * max_alpha, 0, 255).astype(np.uint8)
            vig_arr[area_top:area_bot, area_left:area_left + result.shape[1]] = result
            mask = Image.fromarray(vig_arr)
            effective_blur = max(blur_radius, 15)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=effective_blur))
            return mask

        elif shape == "wavy":
            rows = np.arange(area_top, area_bot, dtype=np.float32)
            cols = np.arange(area_left, area_right, dtype=np.float32)
            if len(rows) == 0 or len(cols) == 0:
                return Image.new("L", img_size, 0)

            freq = max(3, area_w // 80)
            col_grid, row_grid = np.meshgrid(cols, rows)
            col_n = (col_grid - area_left) / max(1, area_w)
            row_n = (row_grid - area_top) / max(1, area_h)

            text_top_n = (y - area_top) / max(1, area_h)
            text_bot_n = (y + height - area_top) / max(1, area_h)

            vert_alpha = np.ones_like(row_n, dtype=np.float32)
            top_mask = row_n < text_top_n
            top_progress = np.clip(row_n / max(0.01, text_top_n), 0.0, 1.0)
            vert_alpha = np.where(top_mask, top_progress, vert_alpha)
            bot_mask = row_n > text_bot_n
            bot_progress = np.clip((1.0 - row_n) / max(0.01, 1.0 - text_bot_n), 0.0, 1.0)
            vert_alpha = np.where(bot_mask, bot_progress, vert_alpha)

            wave_offset = np.sin(col_n * freq * math.pi * 2) * 0.06
            edge_dist = np.minimum(col_n, 1.0 - col_n)
            edge_threshold = edge_fade_pct + wave_offset
            edge_fade = np.clip(edge_dist / np.maximum(edge_threshold, 0.001), 0.0, 1.0)

            combined = vert_alpha * edge_fade * intensity_factor
            wavy_arr = np.zeros((ih, iw), dtype=np.uint8)
            result = np.clip(combined * max_alpha, 0, 255).astype(np.uint8)
            wavy_arr[area_top:area_bot, area_left:area_left + result.shape[1]] = result
            mask = Image.fromarray(wavy_arr)
            if blur_radius > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(radius=max(blur_radius // 2, 5)))
            return mask

        # Fallback
        mask = Image.new("L", img_size, 0)
        mask_arr = np.array(mask)
        for row in range(area_top, area_bot):
            progress = (row - area_top) / max(1, area_h)
            alpha = int(max_alpha * progress * intensity_factor)
            mask_arr[row, area_left:area_right] = min(255, alpha)
        mask = Image.fromarray(mask_arr)
        effective_blur = max(blur_radius, 15)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=effective_blur))
        return mask

    def compose_page_with_template(
        self,
        image_base64: str,
        text: str,
        template: PageTemplate,
        dpi: int = DEFAULT_DPI,
    ) -> str:
        """
        Compose a page using a PageTemplate for dimensions and settings.

        Kitap yatay A4: şablon dikeyse (width < height) yatay A4 boyutlarını zorlar.

        Args:
            image_base64: Base64 encoded AI-generated image
            text: Text content to render
            template: PageTemplate with all dimension and style settings
            dpi: Output resolution

        Returns:
            Base64 encoded composed image
        """
        # Tek kaynak: build_template_config (Y düzeltmesi, font clamp, stroke vb.)
        template_config = build_template_config(template)

        # Kitap yatay A4: şablon dikeyse yatay A4 zorla
        pw, ph = template.page_width_mm, template.page_height_mm
        if pw < ph:
            pw, ph = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM

        return self.compose_page(
            image_base64=image_base64,
            text=text,
            template_config=template_config,
            page_width_mm=pw,
            page_height_mm=ph,
            dpi=dpi,
        )

    def compose_pages_batch(
        self,
        pages: list[dict],
        template_config: dict,
        page_width_mm: float = 297,
        page_height_mm: float = 210,
        dpi: int = DEFAULT_DPI,
    ) -> list[dict]:
        """
        Compose multiple pages with template settings.

        Args:
            pages: List of page dicts with page_number, text, image_base64
            template_config: Page template configuration
            page_width_mm: Page width in mm
            page_height_mm: Page height in mm
            dpi: Output DPI

        Returns:
            Pages with composed_image_base64 added
        """
        composed_pages = []

        for page in pages:
            page_copy = page.copy()

            if page.get("image_base64"):
                composed_image = self.compose_page(
                    image_base64=page["image_base64"],
                    text=page.get("text", ""),
                    template_config=template_config,
                    page_width_mm=page_width_mm,
                    page_height_mm=page_height_mm,
                    dpi=dpi,
                )
                page_copy["composed_image_base64"] = composed_image

            composed_pages.append(page_copy)

        return composed_pages

    def compose_pages_batch_with_template(
        self,
        pages: list[dict],
        template: PageTemplate,
        dpi: int = DEFAULT_DPI,
    ) -> list[dict]:
        """
        Compose multiple pages using a PageTemplate.

        Args:
            pages: List of page dicts with page_number, text, image_base64
            template: PageTemplate with all settings
            dpi: Output DPI

        Returns:
            Pages with composed_image_base64 added
        """
        composed_pages = []

        for page in pages:
            page_copy = page.copy()

            if page.get("image_base64"):
                composed_image = self.compose_page_with_template(
                    image_base64=page["image_base64"],
                    text=page.get("text", ""),
                    template=template,
                    dpi=dpi,
                )
                page_copy["composed_image_base64"] = composed_image

            composed_pages.append(page_copy)

        return composed_pages

    # -----------------------------------------------------------------
    # Dedication (Karşılama) Sayfası — AI görseli yok, pastel arka plan + metin
    # -----------------------------------------------------------------
    def compose_dedication_page(
        self,
        text: str,
        template_config: dict | None = None,
        page_width_mm: float = 297,
        page_height_mm: float = 210,
        dpi: int = DEFAULT_DPI,
    ) -> str:
        """Render a dedication page with a solid pastel background and centred text.

        Args:
            text: Dedication text (already resolved — no {child_name} placeholder).
            template_config: Optional config dict (from build_template_config) for a
                dedication-type PageTemplate. If None, sensible defaults are used.
            page_width_mm: Page width in mm.
            page_height_mm: Page height in mm.
            dpi: Output resolution.

        Returns:
            Base64-encoded PNG image of the composed page.
        """
        page_width_mm, page_height_mm = effective_page_dimensions_mm(
            page_width_mm, page_height_mm
        )
        canvas_w = mm_to_px(page_width_mm, dpi)
        canvas_h = mm_to_px(page_height_mm, dpi)

        # Defaults for dedication pages
        cfg = template_config or {}
        bg_color = cfg.get("background_color", "#FFF5E6")
        font_family = cfg.get("font_family", "Nunito")
        font_size_pt = cfg.get("font_size_pt", 28)
        font_color = cfg.get("font_color", "#5B4636")
        text_align = cfg.get("text_align", "center")

        # Create canvas
        canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)

        if not text or not text.strip():
            # Empty dedication page — just return the background
            buf = io.BytesIO()
            canvas.save(buf, format="PNG", quality=95)
            return base64.b64encode(buf.getvalue()).decode()

        # Resolve font
        font_size_px = max(10, int(font_size_pt * dpi / 72))
        font_path = _resolve_font_path(font_family)
        font: ImageFont.FreeTypeFont | None = None
        for try_px in (font_size_px, min(font_size_px, 500), 50):
            try_px = max(10, try_px)
            try:
                font = ImageFont.truetype(font_path, try_px)
                font_size_px = try_px
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()
            font_size_px = 20

        # Turkish fallback
        if _text_needs_turkish(text) and not _font_supports_turkish(font_path):
            for fb in _TURKISH_FALLBACK_FONTS:
                fb_path = _resolve_font_path(fb)
                if _font_supports_turkish(fb_path):
                    try:
                        font = ImageFont.truetype(fb_path, font_size_px)
                        font_path = fb_path
                    except OSError:
                        pass
                    break

        # Text area: centre with 15% padding each side
        pad_x = int(canvas_w * 0.15)
        text_area_w = canvas_w - 2 * pad_x

        # Word-wrap
        lines = self._wrap_text(text, font, text_area_w)

        # Compute total text height
        line_height_factor = 1.6
        line_h = int(font_size_px * line_height_factor)
        total_text_h = line_h * len(lines)

        # Centre vertically
        start_y = max(0, (canvas_h - total_text_h) // 2)

        draw = ImageDraw.Draw(canvas)

        # Optional decorative border (subtle)
        border_color = cfg.get("font_color", "#5B4636")
        border_w = max(2, int(dpi * 0.02))
        inset = int(canvas_w * 0.06)
        draw.rounded_rectangle(
            [inset, inset, canvas_w - inset, canvas_h - inset],
            radius=int(dpi * 0.15),
            outline=border_color,
            width=border_w,
        )

        # Draw each line
        for i, line in enumerate(lines):
            y = start_y + i * line_h
            try:
                line_w = font.getlength(line)
            except Exception:
                bbox = font.getbbox(line)
                line_w = bbox[2] - bbox[0]

            if text_align == "left":
                x = pad_x
            elif text_align == "right":
                x = canvas_w - pad_x - int(line_w)
            else:
                x = (canvas_w - int(line_w)) // 2

            # Soft shadow
            shadow_offset = max(1, int(font_size_px * 0.03))
            shadow_color = "#00000033"
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)

            # Main text
            draw.text((x, y), line, font=font, fill=font_color)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG", quality=95)
        return base64.b64encode(buf.getvalue()).decode()


# Singleton
page_composer = PageComposer()
