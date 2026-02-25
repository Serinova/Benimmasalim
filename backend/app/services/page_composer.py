"""Page Composer - Renders text on images according to page templates.

Uses centralized resolution calculation from resolution_calc.py.
NEVER hard-code pixel values here!
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
from app.utils.resolution_calc import (
    A4_LANDSCAPE_HEIGHT_MM,
    A4_LANDSCAPE_WIDTH_MM,
    DEFAULT_DPI,
    mm_to_px,
)

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Cross-platform font resolution: Windows → C:/Windows/Fonts, Linux → fc-match
# ---------------------------------------------------------------------------
_IS_WINDOWS = platform.system() == "Windows"


def _find_linux_font(family: str) -> str:
    """fc-match + Google Fonts dizini ile Linux'ta font dosyasının tam yolunu bul."""
    import glob as _glob

    # Bilinen isim farklılıkları: frontend ismi → dosya slug'ı
    _FONT_ALIASES: dict[str, str] = {
        "fredoka one": "fredoka",  # Font yeniden adlandırıldı
        "fredoka": "fredoka",
        "comic neue": "comicneue",
        "patrick hand": "patrickhand",
        "bubblegum sans": "bubblegumsans",
        "baloo 2": "baloo2",
        "luckiest guy": "luckiestguy",
        "open sans": "opensans",
        "indie flower": "indieflower",
        "shadows into light": "shadowsintolight",
        "architects daughter": "architectsdaughter",
        "just another hand": "justanotherhand",
        "reenie beanie": "reeniebeanie",
        "sue ellen francisco": "sueellenfrancisco",
        "short stack": "shortstack",
        "coming soon": "comingsoon",
        "covered by your grace": "coveredbyyourgrace",
        "permanent marker": "permanentmarker",
        "gloria hallelujah": "gloriahallelujah",
        "amatic sc": "amaticsc",
    }

    # 1) Google Fonts dizininde doğrudan ara (en güvenilir)
    google_dir = "/usr/share/fonts/truetype/google"
    if os.path.isdir(google_dir):
        # Font adından dosya ismi türet: "Comic Neue" → "comicneue", "Baloo 2" → "baloo2"
        raw_slug = family.lower().replace(" ", "")
        slug = _FONT_ALIASES.get(family.lower(), raw_slug)
        for ext in ("*.ttf", "*.otf"):
            for fp in _glob.glob(os.path.join(google_dir, "**", ext), recursive=True):
                fname = os.path.basename(fp).lower()
                # Regular/400 ağırlığı tercih et
                if slug in fname and ("regular" in fname or "-400" in fname or fname.startswith(slug + ".")):
                    return fp
        # İkinci geçiş: slug eşleşen herhangi bir dosya (bold/italic olabilir)
        for ext in ("*.ttf", "*.otf"):
            for fp in _glob.glob(os.path.join(google_dir, "**", ext), recursive=True):
                if slug in os.path.basename(fp).lower():
                    return fp

    # 2) fc-match ile sistem fontlarında ara
    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{file}", family],
            capture_output=True,
            text=True,
            timeout=5,
        )
        path = (result.stdout or "").strip()
        if path:
            return path
    except Exception:
        pass

    # 3) Bilinen fallback yolları
    for fallback in (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ):
        try:
            with open(fallback, "rb"):
                return fallback
        except OSError:
            continue
    return ""


# İlk çağrıda çözümlenen cache (her font family için)
_LINUX_FONT_CACHE: dict[str, str] = {}

# Türkçe'ye özgü sorunlu karakterler (çoğu fontta eksik glyph)
_TURKISH_CRITICAL_CHARS = frozenset("\u015f\u011f\u015e\u011e\u0130\u0131")  # ş ğ Ş Ğ İ ı
# Fallback sıralaması: variable font'lar ve Türkçe desteği kesin olanlar önce
_TURKISH_FALLBACK_FONTS = [
    "Nunito", "Roboto", "Poppins", "Open Sans", "Montserrat",
    "Comfortaa", "Quicksand", "Caveat", "Comic Neue", "Patrick Hand",
    "Pangolin", "Fredoka", "Baloo 2",
]
# Cache: font_path → True/False (Türkçe render edebiliyor mu)
_TURKISH_GLYPH_CACHE: dict[str, bool] = {}

# .notdef referans image (bir kez üretilir, tüm fontlar için kullanılır)
_NOTDEF_TEST_SIZE = (80, 50)
_NOTDEF_FONT_SIZE = 30


def _font_supports_turkish(font_path: str) -> bool:
    """Font dosyasının ş/ğ/Ş/Ğ/İ/ı glyphlerini gerçekten render edip edemediğini kontrol et.

    Eski yöntem (mask.size kontrolü) .notdef glyphini (□ kutusu) yakalayamıyor.
    Yeni yöntem: Her Türkçe karakteri küçük bir Image'a çizip .notdef referansıyla
    piksel bazında karşılaştırır. Aynıysa font o karakteri desteklemiyor demektir.
    """
    if font_path in _TURKISH_GLYPH_CACHE:
        return _TURKISH_GLYPH_CACHE[font_path]
    try:
        test_font = ImageFont.truetype(font_path, _NOTDEF_FONT_SIZE)

        # .notdef referansı: kesinlikle var olmayan bir Unicode noktası (U+FFFF)
        notdef_img = Image.new("L", _NOTDEF_TEST_SIZE, 0)
        ImageDraw.Draw(notdef_img).text((5, 5), "\uffff", font=test_font, fill=255)
        notdef_bytes = notdef_img.tobytes()

        for ch in _TURKISH_CRITICAL_CHARS:
            ch_img = Image.new("L", _NOTDEF_TEST_SIZE, 0)
            ImageDraw.Draw(ch_img).text((5, 5), ch, font=test_font, fill=255)
            ch_bytes = ch_img.tobytes()

            # Tamamen boş (hiç piksel yok) → desteklemiyor
            if ch_bytes == bytes(len(ch_bytes)):
                _TURKISH_GLYPH_CACHE[font_path] = False
                return False

            # .notdef ile birebir aynı → font .notdef kutusu çiziyor, gerçek glyph yok
            if ch_bytes == notdef_bytes:
                _TURKISH_GLYPH_CACHE[font_path] = False
                return False

        _TURKISH_GLYPH_CACHE[font_path] = True
        return True
    except Exception:
        _TURKISH_GLYPH_CACHE[font_path] = False
        return False


def _text_needs_turkish(text: str) -> bool:
    """Metnin Türkçe'ye özgü sorunlu karakterler içerip içermediğini kontrol et."""
    return bool(_TURKISH_CRITICAL_CHARS & set(text))


def _resolve_font_path(family: str) -> str:
    """Font family adını platform bağımsız dosya yoluna çevir."""
    if _IS_WINDOWS:
        return FONT_PATHS_WIN.get(family, _DEFAULT_FONT_PATH_WIN)
    # Linux / Docker
    if family not in _LINUX_FONT_CACHE:
        _LINUX_FONT_CACHE[family] = _find_linux_font(family)
    return _LINUX_FONT_CACHE[family] or _find_linux_font("sans-serif")


def build_template_config(template: Any) -> dict:
    """Şablondan template_config dict; orders ve admin aynı kaynağı kullansın (yazı konumu/boyut)."""
    def _pct(v: Any, default: float) -> float:
        if v is None:
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _font_pt(v: Any) -> int:
        if v is None:
            return 14
        try:
            n = int(v)
        except (TypeError, ValueError):
            return 14
        return min(732, max(8, n))

    text_position = (getattr(template, "text_position", None) or "bottom").lower()
    text_y_raw = _pct(getattr(template, "text_y_percent", None), 72.0)
    # "bottom" ise yazı gerçekten altta olsun; Y küçük kalmışsa (frontend sadece position gönderip y göndermemiş olabilir) 72 yap
    if text_position == "bottom" and text_y_raw < 50:
        text_y_raw = 72.0
    elif text_position == "top" and text_y_raw > 50:
        text_y_raw = 10.0

    def _bool(v: Any, default: bool) -> bool:
        if v is None:
            return default
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() not in ("false", "0", "no", "off", "")
        return bool(v)

    def _normalize_align(v: Any) -> str:
        a = (v or "center").strip().lower()
        if a in ("left", "center", "right"):
            return a
        return "center"

    def _safe_hex(v: Any, default: str) -> str:
        """Hex renk değerini güvenli şekilde al."""
        if v is None:
            return default
        s = str(v).strip()
        if not s:
            return default
        if not s.startswith("#"):
            s = "#" + s
        # 6 haneli hex mi kontrol
        clean = s.lstrip("#")
        if len(clean) == 6:
            try:
                int(clean, 16)
                return s
            except ValueError:
                pass
        return default

    def _safe_int(v: Any, default: int, lo: int, hi: int) -> int:
        """Integer değeri güvenli şekilde al, min/max sınırla."""
        if v is None:
            return default
        try:
            n = int(v)
        except (TypeError, ValueError):
            return default
        return min(hi, max(lo, n))

    return {
        "page_type": (getattr(template, "page_type", None) or "inner").lower(),
        "text_enabled": _bool(getattr(template, "text_enabled", None), True),
        "image_x_percent": _pct(getattr(template, "image_x_percent", None), 0.0),
        "image_y_percent": _pct(getattr(template, "image_y_percent", None), 0.0),
        "image_width_percent": _pct(getattr(template, "image_width_percent", None), 100.0),
        "image_height_percent": _pct(getattr(template, "image_height_percent", None), 100.0),
        "text_x_percent": _pct(getattr(template, "text_x_percent", None), 5.0),
        "text_y_percent": text_y_raw,
        "text_width_percent": _pct(getattr(template, "text_width_percent", None), 90.0),
        "text_height_percent": _pct(getattr(template, "text_height_percent", None), 25.0),
        "text_position": text_position,
        "font_family": (getattr(template, "font_family", None) or "Arial").strip() or "Arial",
        "font_size_pt": _font_pt(getattr(template, "font_size_pt", None)),
        "font_color": (getattr(template, "font_color", None) or "#FFFFFF").strip() or "#FFFFFF",
        "font_weight": (getattr(template, "font_weight", None) or "normal").strip() or "normal",
        "text_align": _normalize_align(getattr(template, "text_align", None)),
        "background_color": getattr(template, "background_color", None) or "#FFFFFF",
        "bleed_mm": _pct(getattr(template, "bleed_mm", None), 3.0),
        "text_stroke_enabled": _bool(getattr(template, "text_stroke_enabled", None), True),
        "text_stroke_color": getattr(template, "text_stroke_color", None) or "#000000",
        "text_stroke_width": _pct(getattr(template, "text_stroke_width", None), 2.0),
        # Metin arkaplan gradient
        "text_bg_enabled": _bool(getattr(template, "text_bg_enabled", None), True),
        "text_bg_color": _safe_hex(getattr(template, "text_bg_color", None), "#000000"),
        "text_bg_opacity": _safe_int(getattr(template, "text_bg_opacity", None), 180, 0, 255),
        "text_bg_shape": (getattr(template, "text_bg_shape", None) or "soft_vignette").strip() or "soft_vignette",
        "text_bg_blur": _safe_int(getattr(template, "text_bg_blur", None), 30, 0, 80),
        # Cover Title — kaynak: "overlay" (PIL WordArt) veya "gemini" (Gemini native text)
        "cover_title_source": (getattr(template, "cover_title_source", None) or "gemini").strip() or "gemini",
        # Cover Title — WordArt kapak başlığı
        "cover_title_enabled": _bool(getattr(template, "cover_title_enabled", None), True),
        "cover_title_font_family": (getattr(template, "cover_title_font_family", None) or "Lobster").strip() or "Lobster",
        "cover_title_font_size_pt": _safe_int(getattr(template, "cover_title_font_size_pt", None), 48, 16, 96),
        "cover_title_font_color": _safe_hex(getattr(template, "cover_title_font_color", None), "#FFD700"),
        "cover_title_arc_intensity": _safe_int(getattr(template, "cover_title_arc_intensity", None), 35, 0, 100),
        "cover_title_shadow_enabled": _bool(getattr(template, "cover_title_shadow_enabled", None), True),
        "cover_title_shadow_color": _safe_hex(getattr(template, "cover_title_shadow_color", None), "#000000"),
        "cover_title_shadow_offset": _safe_int(getattr(template, "cover_title_shadow_offset", None), 3, 0, 15),
        "cover_title_stroke_width": _pct(getattr(template, "cover_title_stroke_width", None), 2.0),
        "cover_title_stroke_color": _safe_hex(getattr(template, "cover_title_stroke_color", None), "#8B6914"),
        "cover_title_y_percent": _pct(getattr(template, "cover_title_y_percent", None), 5.0),
        "cover_title_preset": (getattr(template, "cover_title_preset", None) or "premium").strip() or "premium",
        "cover_title_effect": (getattr(template, "cover_title_effect", None) or "gold_shine").strip() or "gold_shine",
        "cover_title_letter_spacing": _safe_int(getattr(template, "cover_title_letter_spacing", None), 0, -5, 20),
    }

# Font paths - Windows yolları (Linux'ta _resolve_font_path fc-match kullanır)
_DEFAULT_FONT_PATH_WIN = "C:/Windows/Fonts/arial.ttf"
FONT_PATHS_WIN = {
    "Arial": _DEFAULT_FONT_PATH_WIN,
    "Nunito": _DEFAULT_FONT_PATH_WIN,
    "Quicksand": _DEFAULT_FONT_PATH_WIN,
    "Comfortaa": _DEFAULT_FONT_PATH_WIN,
    "Baloo 2": _DEFAULT_FONT_PATH_WIN,
    "Bubblegum Sans": _DEFAULT_FONT_PATH_WIN,
    "Comic Neue": _DEFAULT_FONT_PATH_WIN,
    "Patrick Hand": _DEFAULT_FONT_PATH_WIN,
    "Caveat": _DEFAULT_FONT_PATH_WIN,
    "Lobster": _DEFAULT_FONT_PATH_WIN,
    "Pacifico": _DEFAULT_FONT_PATH_WIN,
    "Fredoka One": _DEFAULT_FONT_PATH_WIN,
    "Bangers": _DEFAULT_FONT_PATH_WIN,
    "Chewy": _DEFAULT_FONT_PATH_WIN,
    "Luckiest Guy": _DEFAULT_FONT_PATH_WIN,
    "Poppins": _DEFAULT_FONT_PATH_WIN,
    "Montserrat": _DEFAULT_FONT_PATH_WIN,
    "Open Sans": _DEFAULT_FONT_PATH_WIN,
    "Roboto": _DEFAULT_FONT_PATH_WIN,
    "Comic Sans MS": "C:/Windows/Fonts/comic.ttf",
    "Georgia": "C:/Windows/Fonts/georgia.ttf",
    "Verdana": "C:/Windows/Fonts/verdana.ttf",
}


def effective_page_dimensions_mm(
    page_width_mm: float, page_height_mm: float
) -> tuple[float, float]:
    """Kitap yatay A4: boyutlar dikeyse (w < h) yatay A4'e çevir."""
    if page_width_mm < page_height_mm:
        return A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
    return page_width_mm, page_height_mm


# ---------------------------------------------------------------------------
# Otomatik kenar tespiti: AI görselleri bazen beyaz/siyah çerçeve ekler.
# Sabit overscan yetersiz kalabilir; her görsel için adaptif kırpma uygula.
# ---------------------------------------------------------------------------
def _auto_trim_borders(img: Image.Image, tolerance: int = 25, min_strip_px: int = 3) -> Image.Image:
    """AI görsellerindeki uniform-renk kenarları tespit edip kırpar.

    tolerance: Piksel değerleri arasında kabul edilen max fark (0-255).
    min_strip_px: Bu kadardan az kırpılacak kenar varsa dokunma.
    """
    arr = np.array(img)
    h, w = arr.shape[:2]

    # Her kenardan ortalama rengi hesapla ve uniform mu kontrol et
    def _is_uniform_row(row_idx: int) -> bool:
        row = arr[row_idx].astype(np.float32)
        return bool(np.all(np.std(row, axis=0) < tolerance))

    def _is_uniform_col(col_idx: int) -> bool:
        col = arr[:, col_idx].astype(np.float32)
        return bool(np.all(np.std(col, axis=0) < tolerance))

    # Üstten tara
    top = 0
    while top < h // 4 and _is_uniform_row(top):
        top += 1
    # Alttan tara
    bottom = h
    while bottom > h * 3 // 4 and _is_uniform_row(bottom - 1):
        bottom -= 1
    # Soldan tara
    left = 0
    while left < w // 4 and _is_uniform_col(left):
        left += 1
    # Sağdan tara
    right = w
    while right > w * 3 // 4 and _is_uniform_col(right - 1):
        right -= 1

    # Çok az kırpma (< min_strip_px) gereksiz
    if top < min_strip_px:
        top = 0
    if (h - bottom) < min_strip_px:
        bottom = h
    if left < min_strip_px:
        left = 0
    if (w - right) < min_strip_px:
        right = w

    if top == 0 and bottom == h and left == 0 and right == w:
        return img  # Kenar yok

    cropped = img.crop((left, top, right, bottom))
    logger.info(
        "Auto-trim: removed borders L=%d T=%d R=%d B=%d (orig %dx%d → %dx%d)",
        left, top, w - right, h - bottom, w, h, cropped.width, cropped.height,
    )
    return cropped


class PageComposer:
    """
    Composes final page images by rendering text on AI-generated images
    according to page template settings.
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
            # ── İç Sayfa: normal metin ──
            elif draw_text and text_enabled and not _is_cover_page:
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
                _font_color = template_config.get("font_color") or "#FFFFFF"
                _font_weight = template_config.get("font_weight", "normal")
                _stroke_on = template_config.get("text_stroke_enabled", True)
                _stroke_color = template_config.get("text_stroke_color") or "#000000"
                _stroke_width = template_config.get("text_stroke_width", 2.0)
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
                        bg_enabled=template_config.get("text_bg_enabled", True),
                        bg_color=template_config.get("text_bg_color", "#000000"),
                        bg_opacity=template_config.get("text_bg_opacity", 180),
                        bg_shape=template_config.get("text_bg_shape", "soft_vignette"),
                        bg_blur=template_config.get("text_bg_blur", 30),
                        font_weight=_font_weight,
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

    def _build_gradient_mask(
        self,
        img_size: tuple[int, int],
        x: int, y: int, width: int, height: int,
        shape: str,
        blur_radius: int,
        max_alpha: int,
    ) -> Image.Image:
        """Gradient alpha mask oluştur — şekle göre yumuşak geçişli çerçeve."""
        import math

        from PIL import ImageFilter

        iw, ih = img_size
        # Gradient'in kapsadığı alan (yukarı doğru %30 ek pay)
        grad_start_y = max(0, y - int(height * 0.3))
        grad_end_y = min(y + height, ih)
        grad_h = grad_end_y - grad_start_y

        # 1) Temel dikey gradient (yukarı→aşağı koyulaşan)
        mask = Image.new("L", img_size, 0)
        mask_arr = np.array(mask)

        for row in range(grad_start_y, grad_end_y):
            progress = (row - grad_start_y) / max(1, grad_h)
            alpha = int(max_alpha * progress)
            mask_arr[row, x : x + width] = min(255, alpha)

        mask = Image.fromarray(mask_arr)

        # 2) Şekle göre kenar maskeleme
        if shape == "rectangle":
            # Düz dikdörtgen — blur yok, sert kenar
            pass

        elif shape == "rounded":
            # Yuvarlatılmış köşeler
            corner_r = max(20, min(width, height) // 6)
            corner_mask = Image.new("L", img_size, 0)
            cd = ImageDraw.Draw(corner_mask)
            cd.rounded_rectangle(
                [x, grad_start_y, x + width, grad_end_y],
                radius=corner_r,
                fill=255,
            )
            if blur_radius > 0:
                corner_mask = corner_mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            # mask * corner_mask (element-wise min)
            mask = Image.fromarray(np.minimum(np.array(mask), np.array(corner_mask)))

        elif shape == "soft_vignette":
            # Yumuşak vignette — kenarlar gaussian blur ile yumuşar
            # İç alan tam opak, kenarlar yumuşak geçişli
            pad_x = max(20, width // 8)
            pad_y = max(15, grad_h // 6)
            vig = Image.new("L", img_size, 0)
            vd = ImageDraw.Draw(vig)
            # İç dikdörtgen çiz
            vd.rectangle(
                [x + pad_x, grad_start_y + pad_y, x + width - pad_x, grad_end_y - pad_y],
                fill=255,
            )
            # Gaussian blur ile kenarları yumuşat
            effective_blur = max(blur_radius, 25)
            vig = vig.filter(ImageFilter.GaussianBlur(radius=effective_blur))
            mask = Image.fromarray(np.minimum(np.array(mask), np.array(vig)))

        elif shape == "wavy":
            # Dalgalı kenarlar — sinüs dalgasıyla organik geçiş
            wavy_mask = np.zeros((ih, iw), dtype=np.uint8)
            freq = max(3, width // 80)  # dalga frekansı
            amplitude = max(10, min(width, height) // 12)

            for row in range(grad_start_y, grad_end_y):
                progress = (row - grad_start_y) / max(1, grad_h)
                base_alpha = int(max_alpha * progress)

                for col in range(x, min(x + width, iw)):
                    # Sol ve sağ kenar dalgası
                    col_progress = (col - x) / max(1, width)
                    # Kenar mesafesi (0=kenarda, 1=ortada)
                    edge_dist = min(col_progress, 1 - col_progress) * 2
                    # Sinüs dalgası kenar yumuşatma
                    wave_offset = math.sin(row / max(1, grad_h) * freq * math.pi * 2) * amplitude
                    edge_threshold = 0.15 + (wave_offset / max(1, width))
                    if edge_dist < edge_threshold:
                        fade = edge_dist / max(0.001, edge_threshold)
                        wavy_mask[row, col] = int(base_alpha * fade)
                    else:
                        # Üst kenar dalgalı geçiş
                        top_dist = (row - grad_start_y) / max(1, grad_h)
                        wave_top = math.sin(col / max(1, width) * freq * math.pi * 2) * 0.08
                        top_threshold = 0.15 + wave_top
                        if top_dist < top_threshold:
                            fade = top_dist / max(0.001, top_threshold)
                            wavy_mask[row, col] = int(base_alpha * fade)
                        else:
                            wavy_mask[row, col] = base_alpha

            mask = Image.fromarray(wavy_mask)
            if blur_radius > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(radius=max(blur_radius // 2, 5)))

        elif shape == "cloud":
            # Bulutsu/organik kenarlar — Perlin-benzeri gürültü
            cloud_mask = np.zeros((ih, iw), dtype=np.uint8)
            # Basit noise: birden fazla sinüs katmanı ile organik kenar
            for row in range(grad_start_y, grad_end_y):
                progress = (row - grad_start_y) / max(1, grad_h)
                base_alpha = int(max_alpha * progress)
                for col in range(x, min(x + width, iw)):
                    col_n = (col - x) / max(1, width)
                    row_n = (row - grad_start_y) / max(1, grad_h)
                    # Kenar mesafesi
                    edge_x = min(col_n, 1 - col_n) * 2
                    edge_y = min(row_n, 1 - row_n) * 2
                    edge = min(edge_x, edge_y)
                    # Çoklu sinüs ile organik kenar
                    noise = (
                        math.sin(col_n * 7.3 + row_n * 5.1) * 0.06
                        + math.sin(col_n * 13.7 + row_n * 11.3) * 0.04
                        + math.sin(row_n * 8.9 + col_n * 3.7) * 0.05
                    )
                    threshold = 0.12 + noise
                    if edge < threshold:
                        fade = edge / max(0.001, threshold)
                        cloud_mask[row, col] = int(base_alpha * fade * fade)  # quadratic easing
                    else:
                        cloud_mask[row, col] = base_alpha

            mask = Image.fromarray(cloud_mask)
            if blur_radius > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(radius=max(blur_radius // 2, 8)))

        else:
            # Bilinmeyen shape → soft_vignette fallback
            effective_blur = max(blur_radius, 25)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=effective_blur))

        return mask

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
        stroke_color: str = "#000000",
        stroke_width: float = 1.0,
        bg_enabled: bool = True,
        bg_color: str = "#000000",
        bg_opacity: int = 180,
        bg_shape: str = "soft_vignette",
        bg_blur: int = 30,
        font_weight: str = "normal",
    ):
        """Draw text on the image with word wrapping, optional stroke and gradient background."""
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
        # Metin ş/ğ/Ş/Ğ/İ/ı içeriyorsa ve font bunları render edemiyorsa otomatik fallback
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
                "Gradient BG: color=%s rgb=(%d,%d,%d) opacity=%d shape=%s blur=%d",
                bg_color, _bg_r, _bg_g, _bg_b, _bg_max_alpha, bg_shape, bg_blur,
            )

            # Şekle göre alpha mask oluştur
            alpha_mask = self._build_gradient_mask(
                img_size=img.size,
                x=x, y=y, width=width, height=height,
                shape=bg_shape,
                blur_radius=bg_blur,
                max_alpha=_bg_max_alpha,
            )

            # Renk katmanı + alpha mask → overlay
            color_layer = Image.new("RGBA", img.size, (_bg_r, _bg_g, _bg_b, 0))
            # Alpha mask'ı color_layer'ın alpha kanalına uygula
            color_layer.putalpha(alpha_mask)

            # Composite
            img_rgba = img.convert("RGBA")
            img.paste(Image.alpha_composite(img_rgba, color_layer).convert("RGB"))
            draw = ImageDraw.Draw(img)

        # Word wrap: max_width en az 1 (küçük kutuda taşma önlenir)
        wrap_width = max(1, width - 20)
        lines = self._wrap_text(text, font, wrap_width)

        # Satır yüksekliği: font metriklerinden (tutarlı konum, kayma yok)
        try:
            metric_bbox = font.getbbox("Ay")
            line_height = int((metric_bbox[3] - metric_bbox[1]) * 1.2)
        except Exception:
            line_height = max(int(font_size_px * 1.4), 1)
        if line_height < 1:
            line_height = max(int(font_size_px * 1.4), 1)
        total_text_height = len(lines) * line_height

        # Dikey ortalama; metin kutusu dışına taşmasın
        start_y_raw = int(y + (height - total_text_height) / 2)
        start_y = max(y, min(start_y_raw, y + height - total_text_height)) if total_text_height <= height else y

        # Calculate stroke width in pixels (scale with DPI)
        stroke_width_px = int(stroke_width * dpi / 72) if stroke_enabled else 0

        logger.debug(
            "Drawing text with stroke",
            stroke_enabled=stroke_enabled,
            stroke_color=stroke_color,
            stroke_width_px=stroke_width_px,
        )

        # İç sayfalar: düz metin (kapak artık _draw_cover_title ile çiziliyor)
        for i, line in enumerate(lines):
            line_y = start_y + i * line_height

            # Yatay hizalama için satır genişliği
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]

            if text_align == "center":
                line_x = int(x + (width - line_width) / 2)
            elif text_align == "right":
                line_x = int(x + width - line_width - 10)
            else:
                line_x = int(x + 10)

            # Draw text with optional stroke
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
