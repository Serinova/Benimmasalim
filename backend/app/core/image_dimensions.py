"""Fallback page image dimensions when no product/template is set.

When product has cover_template/inner_template, orders and generate_book use
resolution_calc.calculate_generation_params(template) for generation_width/height.
Kitap yatay A4: hem kapak hem iç sayfa landscape (genişlik > yükseklik).
"""

from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE

# Yatay A4 oranı (297×210 mm); şablon yokken tek kaynak
COVER_WIDTH, COVER_HEIGHT = DEFAULT_GENERATION_A4_LANDSCAPE
INNER_WIDTH, INNER_HEIGHT = DEFAULT_GENERATION_A4_LANDSCAPE


def get_page_image_dimensions(_page_num: int) -> tuple[int, int]:
    """Kapak ve iç sayfa: yatay A4 (landscape). Fallback when no template."""
    return (INNER_WIDTH, INNER_HEIGHT)
