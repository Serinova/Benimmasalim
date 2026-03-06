"""Page composer helper functions — font resolution, template config, image utils.

Split from page_composer.py for maintainability.
"""

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
_TURKISH_CRITICAL_CHARS = frozenset("\u015f\u011f\u015e\u011e\u0130\u0131")  # ş ğ Å Ä İ ı
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
    """Font dosyasının ş/ğ/Å/Ä/İ/ı glyphlerini gerçekten render edip edemediğini kontrol et.

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
    """Åablondan template_config dict; orders ve admin aynı kaynağı kullansın (yazı konumu/boyut)."""
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
        "text_vertical_align": (getattr(template, "text_vertical_align", None) or "bottom").strip().lower() or "bottom",
        "font_family": (getattr(template, "font_family", None) or "Arial").strip() or "Arial",
        "font_size_pt": _font_pt(getattr(template, "font_size_pt", None)),
        "font_color": (getattr(template, "font_color", None) or "#2D2D2D").strip() or "#2D2D2D",
        "font_weight": (getattr(template, "font_weight", None) or "normal").strip() or "normal",
        "text_align": _normalize_align(getattr(template, "text_align", None)),
        "line_height": _pct(getattr(template, "line_height", None), 1.35),
        "background_color": getattr(template, "background_color", None) or "#FFFFFF",
        "bleed_mm": _pct(getattr(template, "bleed_mm", None), 3.0),
        "text_stroke_enabled": _bool(getattr(template, "text_stroke_enabled", None), False),
        "text_stroke_color": getattr(template, "text_stroke_color", None) or "#FFFFFF",
        "text_stroke_width": _pct(getattr(template, "text_stroke_width", None), 1.0),
        # Metin arkaplan: beyaz bulut (okunabilirlik için)
        "text_bg_enabled": _bool(getattr(template, "text_bg_enabled", None), True),
        "text_bg_color": _safe_hex(getattr(template, "text_bg_color", None), "#FFFFFF"),
        "text_bg_opacity": _safe_int(getattr(template, "text_bg_opacity", None), 230, 0, 255),
        "text_bg_shape": (getattr(template, "text_bg_shape", None) or "cloud").strip() or "cloud",
        "text_bg_blur": _safe_int(getattr(template, "text_bg_blur", None), 50, 0, 200),
        "text_bg_extend_top": _safe_int(getattr(template, "text_bg_extend_top", None), 60, 0, 200),
        "text_bg_extend_bottom": _safe_int(getattr(template, "text_bg_extend_bottom", None), 15, 0, 100),
        "text_bg_extend_sides": _safe_int(getattr(template, "text_bg_extend_sides", None), 10, 0, 50),
        "text_bg_intensity": _safe_int(getattr(template, "text_bg_intensity", None), 100, 50, 100),
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
    page_width_mm: float | None, page_height_mm: float | None
) -> tuple[float, float]:
    """Kitap yatay A4: boyutlar dikeyse (w < h) yatay A4'e çevir.

    None veya sıfır değer gelirse A4 yatay varsayılan kullanılır.
    """
    w = float(page_width_mm) if page_width_mm else A4_LANDSCAPE_WIDTH_MM
    h = float(page_height_mm) if page_height_mm else A4_LANDSCAPE_HEIGHT_MM
    if w < h:
        return A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
    return w, h


# ---------------------------------------------------------------------------
# Otomatik kenar tespiti: AI görselleri bazen beyaz/siyah çerçeve ekler.
# Sabit overscan yetersiz kalabilir; her görsel için adaptif kırpma uygula.
# ---------------------------------------------------------------------------
def _auto_trim_borders(
    img: Image.Image,
    tolerance: int = 25,
    min_strip_px: int = 3,
    max_trim_fraction: float = 0.08,
) -> Image.Image:
    """AI görsellerindeki uniform-renk kenarları tespit edip kırpar.

    tolerance: Piksel std sapması bu değerin altındaysa kenar sayılır (0-255).
               Düşük değer = sadece gerçek düz renk kenarları kırpılır.
    min_strip_px: Bu kadardan az kırpılacak kenar varsa dokunma.
    max_trim_fraction: Her kenardan kesilebilecek maksimum oran (0.0-1.0).
                       Gerçek içeriğin yanlışlıkla kırpılmasını önler.
    """
    arr = np.array(img)
    h, w = arr.shape[:2]

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

    # Maksimum kırpma oranı — içeriğin yanlışlıkla silinmesini önle
    max_v = int(h * max_trim_fraction)
    max_s = int(w * max_trim_fraction)
    top = min(top, max_v)
    bottom = max(bottom, h - max_v)
    left = min(left, max_s)
    right = max(right, w - max_s)

    if top == 0 and bottom == h and left == 0 and right == w:
        return img  # Kenar yok

    cropped = img.crop((left, top, right, bottom))
    logger.info(
        "Auto-trim: removed borders L=%d T=%d R=%d B=%d (orig %dx%d → %dx%d)",
        left, top, w - right, h - bottom, w, h, cropped.width, cropped.height,
    )
    return cropped


