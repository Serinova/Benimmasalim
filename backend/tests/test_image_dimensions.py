"""Regression: cover and inner pages must both default to A4 landscape (2048x1448)."""

from app.core.image_dimensions import (
    COVER_HEIGHT,
    COVER_WIDTH,
    INNER_HEIGHT,
    INNER_WIDTH,
    get_page_image_dimensions,
)
from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE


def test_cover_is_landscape() -> None:
    w, h = get_page_image_dimensions(0)
    expected_w, expected_h = DEFAULT_GENERATION_A4_LANDSCAPE
    assert w == expected_w and h == expected_h, f"Cover must be {expected_w}x{expected_h}"
    assert w == COVER_WIDTH and h == COVER_HEIGHT


def test_inner_pages_are_landscape() -> None:
    expected_w, expected_h = DEFAULT_GENERATION_A4_LANDSCAPE
    for page_num in (1, 2, 3, 10):
        w, h = get_page_image_dimensions(page_num)
        assert w == expected_w and h == expected_h, f"Inner page {page_num} must be {expected_w}x{expected_h}"
    assert (INNER_WIDTH, INNER_HEIGHT) == (expected_w, expected_h)

