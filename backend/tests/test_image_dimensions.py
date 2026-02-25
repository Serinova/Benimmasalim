"""Regression: cover must be portrait 768x1024, inner pages landscape 1024x768."""

from app.core.image_dimensions import (
    COVER_HEIGHT,
    COVER_WIDTH,
    INNER_HEIGHT,
    INNER_WIDTH,
    get_page_image_dimensions,
)


def test_cover_is_portrait_768x1024() -> None:
    w, h = get_page_image_dimensions(0)
    assert w == 768 and h == 1024, "Cover (page_index 0) must be portrait 768x1024"
    assert w == COVER_WIDTH and h == COVER_HEIGHT


def test_inner_pages_are_landscape_1024x768() -> None:
    for page_num in (1, 2, 3, 10):
        w, h = get_page_image_dimensions(page_num)
        assert w == 1024 and h == 768, f"Inner page {page_num} must be landscape 1024x768"
    assert (INNER_WIDTH, INNER_HEIGHT) == (1024, 768)


def test_dimensions_swapped_fails() -> None:
    """If someone swaps cover/inner, tests fail."""
    w0, h0 = get_page_image_dimensions(0)
    w1, h1 = get_page_image_dimensions(1)
    assert (w0, h0) != (w1, h1)
    assert (w0, h0) == (768, 1024)
    assert (w1, h1) == (1024, 768)
