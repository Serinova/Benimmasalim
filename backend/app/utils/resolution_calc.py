"""Dynamic resolution calculation from template dimensions.

CRITICAL: Never hard-code pixel values! Always use these functions.

Flow:
1. PageTemplate → mm dimensions
2. mm_to_px() → target pixel dimensions
3. calculate_generation_params() → AI generation + upscale strategy
4. resize_to_target() → final exact dimensions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from PIL import Image

    from app.models.book_template import PageTemplate


MM_TO_INCH = 25.4
DEFAULT_DPI = 300
DEFAULT_AI_MAX_SIZE = 2048  # Nano Banana 2 supports native 2K generation

# Yatay A4 (297×210 mm) oranı ≈1.414. Kitap yatay A4 ise üretim bu oranda.
# Nano Banana 2 ile 2K native üretim — 4x yerine 2x upscale yeterli.
DEFAULT_GENERATION_A4_LANDSCAPE = (2048, 1448)  # width, height (2048/1448 ≈ 1.414)

# Kitap baskı formatı: yatay A4 (mm). Tüm varsayılanlar ve "şablon dikeyse yine yatay kullan" bu değere dayanır.
A4_LANDSCAPE_WIDTH_MM = 297.0
A4_LANDSCAPE_HEIGHT_MM = 210.0


class GenerationParams(TypedDict):
    """Parameters for AI image generation with upscale strategy."""

    generation_width: int
    generation_height: int
    target_width: int
    target_height: int
    upscale_factor: int
    aspect_ratio: str
    needs_upscale: bool


def mm_to_px(mm: float, bleed_mm: float = 0.0, dpi: int = DEFAULT_DPI) -> int:
    """
    Convert millimeters to pixels with optional bleed.

    Formula: ((mm + 2 * bleed) / 25.4) * DPI

    Args:
        mm: Dimension in millimeters
        bleed_mm: Bleed margin in mm (added to both sides)
        dpi: Dots per inch (default 300 for print)

    Returns:
        Dimension in pixels (rounded to int)

    Example:
        >>> mm_to_px(210, bleed_mm=3)  # A4 width with 3mm bleed
        2551
    """
    total_mm = mm + (2 * bleed_mm)
    return int((total_mm / MM_TO_INCH) * dpi)


def calculate_target_resolution(
    template: PageTemplate, include_bleed: bool = True, dpi: int = DEFAULT_DPI
) -> tuple[int, int]:
    """
    Calculate target pixel resolution from PageTemplate dimensions.

    ALWAYS use this instead of hard-coded values!

    Args:
        template: PageTemplate with page_width_mm, page_height_mm, bleed_mm
        include_bleed: Whether to include bleed margin
        dpi: DPI for calculation (default 300)

    Returns:
        Tuple of (width_px, height_px)

    Example:
        >>> template = PageTemplate(page_width_mm=210, page_height_mm=210, bleed_mm=3)
        >>> calculate_target_resolution(template)
        (2551, 2551)
    """
    bleed = template.bleed_mm if include_bleed else 0.0

    width_px = mm_to_px(template.page_width_mm, bleed_mm=bleed, dpi=dpi)
    height_px = mm_to_px(template.page_height_mm, bleed_mm=bleed, dpi=dpi)

    return width_px, height_px


def calculate_target_resolution_from_mm(
    width_mm: float,
    height_mm: float,
    bleed_mm: float = 3.0,
    include_bleed: bool = True,
    dpi: int = DEFAULT_DPI,
) -> tuple[int, int]:
    """
    Calculate target pixel resolution from raw mm dimensions.

    Use when you don't have a PageTemplate object.

    Args:
        width_mm: Width in millimeters
        height_mm: Height in millimeters
        bleed_mm: Bleed margin in mm
        include_bleed: Whether to include bleed margin
        dpi: DPI for calculation

    Returns:
        Tuple of (width_px, height_px)
    """
    bleed = bleed_mm if include_bleed else 0.0

    width_px = mm_to_px(width_mm, bleed_mm=bleed, dpi=dpi)
    height_px = mm_to_px(height_mm, bleed_mm=bleed, dpi=dpi)

    return width_px, height_px


def get_effective_generation_params(
    template: PageTemplate,
    ai_max_size: int = DEFAULT_AI_MAX_SIZE,
    dpi: int = DEFAULT_DPI,
    force_landscape_a4_if_portrait: bool = True,
) -> GenerationParams:
    """
    Şablondan üretim parametrelerini alır; şablon dikeyse (w < h) kitap yatay A4 olduğu için
    yatay A4 (297×210 mm) parametrelerini döndürür. Böylece AI görseli ve upscale hedefi hep yatay A4 olur.
    """
    params = calculate_generation_params(template, ai_max_size=ai_max_size, dpi=dpi)
    if not force_landscape_a4_if_portrait:
        return params
    if params["generation_width"] >= params["generation_height"]:
        return params
    return calculate_generation_params_from_mm(
        A4_LANDSCAPE_WIDTH_MM,
        A4_LANDSCAPE_HEIGHT_MM,
        bleed_mm=template.bleed_mm,
        ai_max_size=ai_max_size,
        dpi=dpi,
    )


def calculate_generation_params(
    template: PageTemplate, ai_max_size: int = DEFAULT_AI_MAX_SIZE, dpi: int = DEFAULT_DPI
) -> GenerationParams:
    """
    Calculate AI generation parameters with upscale strategy.

    Since most AI APIs limit to 1024px, this function calculates:
    - Optimal generation size (maintaining aspect ratio)
    - Required upscale factor to reach target resolution
    - Final target dimensions for print quality

    Args:
        template: PageTemplate with dimensions
        ai_max_size: Maximum size AI can generate (default 1024)
        dpi: DPI for target calculation

    Returns:
        GenerationParams dict with all necessary parameters

    Example:
        >>> template = PageTemplate(page_width_mm=210, page_height_mm=210, bleed_mm=3)
        >>> params = calculate_generation_params(template)
        >>> params["generation_width"]
        1024
        >>> params["target_width"]
        2551
        >>> params["upscale_factor"]
        4
    """
    target_w, target_h = calculate_target_resolution(template, dpi=dpi)

    # Calculate aspect ratio
    aspect = target_w / target_h

    # Determine AI generation size maintaining aspect ratio
    if target_w >= target_h:
        gen_w = min(target_w, ai_max_size)
        gen_h = int(gen_w / aspect)
        # Ensure gen_h doesn't exceed max
        if gen_h > ai_max_size:
            gen_h = ai_max_size
            gen_w = int(gen_h * aspect)
    else:
        gen_h = min(target_h, ai_max_size)
        gen_w = int(gen_h * aspect)
        # Ensure gen_w doesn't exceed max
        if gen_w > ai_max_size:
            gen_w = ai_max_size
            gen_h = int(gen_w / aspect)

    # Calculate upscale factor needed
    scale_w = target_w / gen_w
    scale_h = target_h / gen_h
    scale = max(scale_w, scale_h)

    # Determine upscale factor (Real-ESRGAN supports 2x or 4x)
    if scale <= 1.0:
        upscale_factor = 1
        needs_upscale = False
    elif scale <= 2.0:
        upscale_factor = 2
        needs_upscale = True
    else:
        upscale_factor = 4
        needs_upscale = True

    # Calculate aspect ratio string for AI APIs
    aspect_ratio = _calculate_aspect_ratio_string(gen_w, gen_h)

    return GenerationParams(
        generation_width=gen_w,
        generation_height=gen_h,
        target_width=target_w,
        target_height=target_h,
        upscale_factor=upscale_factor,
        aspect_ratio=aspect_ratio,
        needs_upscale=needs_upscale,
    )


def calculate_generation_params_from_mm(
    width_mm: float,
    height_mm: float,
    bleed_mm: float = 3.0,
    ai_max_size: int = DEFAULT_AI_MAX_SIZE,
    dpi: int = DEFAULT_DPI,
) -> GenerationParams:
    """
    Calculate AI generation parameters from raw mm dimensions.

    Use when you don't have a PageTemplate object.
    """
    target_w, target_h = calculate_target_resolution_from_mm(width_mm, height_mm, bleed_mm, dpi=dpi)

    aspect = target_w / target_h

    if target_w >= target_h:
        gen_w = min(target_w, ai_max_size)
        gen_h = int(gen_w / aspect)
        if gen_h > ai_max_size:
            gen_h = ai_max_size
            gen_w = int(gen_h * aspect)
    else:
        gen_h = min(target_h, ai_max_size)
        gen_w = int(gen_h * aspect)
        if gen_w > ai_max_size:
            gen_w = ai_max_size
            gen_h = int(gen_w / aspect)

    scale = max(target_w / gen_w, target_h / gen_h)

    if scale <= 1.0:
        upscale_factor = 1
        needs_upscale = False
    elif scale <= 2.0:
        upscale_factor = 2
        needs_upscale = True
    else:
        upscale_factor = 4
        needs_upscale = True

    aspect_ratio = _calculate_aspect_ratio_string(gen_w, gen_h)

    return GenerationParams(
        generation_width=gen_w,
        generation_height=gen_h,
        target_width=target_w,
        target_height=target_h,
        upscale_factor=upscale_factor,
        aspect_ratio=aspect_ratio,
        needs_upscale=needs_upscale,
    )


def _calculate_aspect_ratio_string(width: int, height: int) -> str:
    """
    Calculate aspect ratio string for AI APIs.

    Returns common ratios like "1:1", "3:4", "4:3", "9:16", "16:9"
    or simplified ratio for others.
    """
    from math import gcd

    # Common AI-supported aspect ratios
    ratio = width / height

    # Check for common ratios with small tolerance
    common_ratios = {
        1.0: "1:1",
        0.75: "3:4",
        1.333: "4:3",
        0.5625: "9:16",
        1.778: "16:9",
    }

    for target_ratio, ratio_str in common_ratios.items():
        if abs(ratio - target_ratio) < 0.05:
            return ratio_str

    # Calculate simplified ratio
    divisor = gcd(width, height)
    ratio_w = width // divisor
    ratio_h = height // divisor

    # Simplify large ratios
    if ratio_w > 20 or ratio_h > 20:
        if ratio > 1:
            return "4:3" if ratio < 1.5 else "16:9"
        else:
            return "3:4" if ratio > 0.67 else "9:16"

    return f"{ratio_w}:{ratio_h}"


def px_to_mm(px: int, dpi: int = DEFAULT_DPI) -> float:
    """
    Convert pixels to millimeters.

    Args:
        px: Dimension in pixels
        dpi: Dots per inch

    Returns:
        Dimension in millimeters
    """
    return (px / dpi) * MM_TO_INCH


def calculate_aspect_ratio(width_mm: float, height_mm: float) -> str:
    """
    Calculate aspect ratio string (e.g., "1:1", "2:3").

    Args:
        width_mm: Width in millimeters
        height_mm: Height in millimeters

    Returns:
        Aspect ratio as string
    """
    from math import gcd

    # Convert to integers for GCD calculation
    w = int(width_mm * 10)
    h = int(height_mm * 10)

    divisor = gcd(w, h)
    ratio_w = w // divisor
    ratio_h = h // divisor

    # Simplify common ratios
    if ratio_w == ratio_h:
        return "1:1"

    return f"{ratio_w}:{ratio_h}"


def resize_to_target(
    image: Image.Image,
    target_width: int,
    target_height: int,
    is_cover: bool = False,
) -> Image.Image:
    """
    Crop-to-fill + resize: oranı koruyarak hedef boyuta getir.

    Kaynak ve hedef oranı farklıysa kırpar (stretch YAPMAZ).
    is_cover=True ise kapak için üstten kırpma yapılmaz (başlık korunur),
    fazla yükseklik alttan alınır.

    Args:
        image: PIL Image object
        target_width: Target width in pixels
        target_height: Target height in pixels
        is_cover: Kapak görseli mi? True ise alttan kırpar.

    Returns:
        Resized PIL Image with exact target dimensions

    Example:
        >>> from PIL import Image
        >>> img = Image.new("RGB", (1024, 1024))
        >>> result = resize_to_target(img, 3578, 2551)
        >>> result.size
        (3578, 2551)
    """
    from PIL import Image as PILImage

    src_w, src_h = image.size
    if src_w <= 0 or src_h <= 0 or target_width <= 0 or target_height <= 0:
        return image.resize((max(1, target_width), max(1, target_height)), PILImage.Resampling.LANCZOS)

    src_ratio = src_w / src_h
    tgt_ratio = target_width / target_height

    # Oran yakınsa (< %2 fark) doğrudan resize yeterli
    if abs(src_ratio - tgt_ratio) / max(tgt_ratio, 0.001) < 0.02:
        return image.resize((target_width, target_height), PILImage.Resampling.LANCZOS)

    # Crop-to-fill: büyük boyutu kırp, küçük boyutu koru
    if src_ratio > tgt_ratio:
        # Kaynak daha geniş → genişlikten kırp (merkez)
        new_w = int(src_h * tgt_ratio)
        offset = (src_w - new_w) // 2
        image = image.crop((offset, 0, offset + new_w, src_h))
    else:
        # Kaynak daha uzun → yükseklikten kırp
        new_h = int(src_w / tgt_ratio)
        # Kapak: üstten kırpma YOK — Gemini title'ı üste koyar; alttan kırp
        # iç sayfa: merkez
        offset = src_h - new_h if is_cover else (src_h - new_h) // 2
        image = image.crop((0, offset, src_w, offset + new_h))

    return image.resize((target_width, target_height), PILImage.Resampling.LANCZOS)


def resize_image_bytes_to_target(
    image_bytes: bytes,
    target_width: int,
    target_height: int,
    output_format: str = "PNG",
    dpi: int = DEFAULT_DPI,
    is_cover: bool = False,
) -> bytes:
    """
    Resize image bytes to exact target dimensions with correct DPI metadata.

    Convenience function that handles bytes input/output.

    Args:
        image_bytes: Input image as bytes
        target_width: Target width in pixels
        target_height: Target height in pixels
        output_format: Output format (PNG, JPEG, etc.)
        dpi: DPI metadata to embed (default 300 for print)

    Returns:
        Resized image as bytes with correct DPI metadata
    """
    from io import BytesIO

    import structlog
    from PIL import Image as PILImage
    from PIL.PngImagePlugin import PngInfo

    logger = structlog.get_logger()

    img = PILImage.open(BytesIO(image_bytes))
    original_size = img.size
    logger.info(f"Resizing image from {original_size} to ({target_width}, {target_height})")

    resized = resize_to_target(img, target_width, target_height, is_cover=is_cover)
    logger.info(f"Resized image size: {resized.size}")

    output = BytesIO()

    if output_format.upper() == "PNG":
        # Add DPI metadata for PNG
        pnginfo = PngInfo()
        # PNG uses pixels per meter (1 inch = 0.0254 meters)
        pnginfo.add_text("dpi", str(dpi))
        resized.save(output, format=output_format, pnginfo=pnginfo, dpi=(dpi, dpi))
    else:
        # JPEG and others support dpi parameter directly
        resized.save(output, format=output_format, quality=95, dpi=(dpi, dpi))

    result = output.getvalue()
    logger.info(f"Output image bytes: {len(result)}")
    return result
