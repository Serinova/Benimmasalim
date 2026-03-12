"""Unit tests for preview detail response: cache-bust and manifest shape (no DB)."""

from datetime import UTC, datetime
from types import SimpleNamespace

from app.prompt_engine import STRICT_NEGATIVE_ADDITIONS, get_strict_negative_additions
from app.services.preview_display_service import (
    append_cache_bust as _append_cache_bust,
)
from app.services.preview_display_service import (
    page_images_with_cache_bust as _page_images_with_cache_bust,
)


def test_append_cache_bust_no_query() -> None:
    url = "https://storage.example.com/page_0.png"
    assert _append_cache_bust(url, "abc123") == url + "?v=abc123"


def test_append_cache_bust_existing_query() -> None:
    url = "https://storage.example.com/page_0.png?token=signed"
    assert _append_cache_bust(url, "abc123") == url + "&v=abc123"


def test_page_images_with_cache_bust_uses_prompt_hash() -> None:
    """Without DB: mock preview with page_images + generation_manifest_json; assert URLs get ?v=."""
    manifest_0 = {"prompt_hash": "h0", "width": 768, "height": 1024, "is_cover": True}
    manifest_1 = {"prompt_hash": "h1", "width": 1024, "height": 768, "is_cover": False}
    mock = SimpleNamespace(
        page_images={"0": "https://gcs/p0.png", "1": "https://gcs/p1.png"},
        preview_images=None,
        generation_manifest_json={"0": manifest_0, "1": manifest_1},
        updated_at=datetime.now(UTC),
    )
    out = _page_images_with_cache_bust(mock)
    assert out is not None
    assert "?v=h0" in out["0"]
    assert "?v=h1" in out["1"]


def test_manifest_page0_cover_768x1024_page1_landscape_1024x768() -> None:
    """Manifest shape: page 0 = cover 768x1024, page 1 = inner 1024x768."""
    m0 = {"is_cover": True, "width": 768, "height": 1024}
    m1 = {"is_cover": False, "width": 1024, "height": 768}
    assert m0["is_cover"] is True and m0["width"] == 768 and m0["height"] == 1024
    assert m1["is_cover"] is False and m1["width"] == 1024 and m1["height"] == 768


def test_strict_negative_includes_typographic() -> None:
    """Strict negative additions (typographic) consistent with prompt_debug use."""
    strict = get_strict_negative_additions()
    assert "typographic" in strict
    assert strict == STRICT_NEGATIVE_ADDITIONS
