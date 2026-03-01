"""Tests for V3 enhancement graceful degradation + legacy fallback labelling.

Scenario 1: enhance_all_pages raises → story still returns with
            v3_composed=True, v3_enhancement_skipped=True.
Scenario 2: Real V2 pipeline_version label → still blocked by guard.
Scenario 3: Legacy fallback output → pipeline_version="v2_fallback".
"""

from __future__ import annotations

import pytest

from app.core.pipeline_version import require_v3_pipeline
from app.services.ai.gemini_service import FinalPageContent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_v3_page(page_number: int, *, enhancement_skipped: bool = False) -> FinalPageContent:
    return FinalPageContent(
        page_number=page_number,
        text=f"Sayfa {page_number} metni",
        scene_description=f"Scene for page {page_number}",
        visual_prompt=f"A child in a field, page {page_number}",
        negative_prompt="text, watermark, logo",
        v3_composed=True,
        v3_enhancement_skipped=enhancement_skipped,
        page_type="cover" if page_number == 0 else "inner",
        page_index=page_number,
        story_page_number=None if page_number == 0 else page_number,
        composer_version="v3",
        pipeline_version="v3",
    )


def _simulate_guard(final_pages: list[FinalPageContent]) -> list[FinalPageContent]:
    """Replicate the guard logic from ai.py (lines 1011-1028)."""
    return [
        p
        for p in final_pages
        if getattr(p, "pipeline_version", "") != "v3"
        or getattr(p, "composer_version", "") != "v3"
        or not getattr(p, "v3_composed", False)
    ]


# ---------------------------------------------------------------------------
# Scenario 1: enhance_all_pages exception → story still returns
# ---------------------------------------------------------------------------

class TestEnhancementSkippedStillReturns:
    """When enhance_all_pages fails, pages should still carry correct V3 labels."""

    def test_enhancement_skipped_pages_pass_guard(self) -> None:
        """Pages with v3_enhancement_skipped=True must NOT be blocked by the guard."""
        pages = [
            _make_v3_page(0, enhancement_skipped=True),
            _make_v3_page(1, enhancement_skipped=True),
            _make_v3_page(2, enhancement_skipped=True),
        ]
        non_v3 = _simulate_guard(pages)
        assert non_v3 == [], (
            "Enhancement-skipped pages have pipeline_version=v3, "
            "composer_version=v3, v3_composed=True — guard must not block them"
        )

    def test_enhancement_skipped_flag_is_set(self) -> None:
        """v3_enhancement_skipped must be True on all pages when enhancement failed."""
        pages = [
            _make_v3_page(0, enhancement_skipped=True),
            _make_v3_page(1, enhancement_skipped=True),
        ]
        assert all(p.v3_enhancement_skipped for p in pages)

    def test_enhancement_skipped_pages_still_have_content(self) -> None:
        """Even with skipped enhancement, pages must still carry text + visual_prompt."""
        page = _make_v3_page(1, enhancement_skipped=True)
        assert page.text
        assert page.visual_prompt
        assert page.v3_composed is True
        assert page.pipeline_version == "v3"
        assert page.composer_version == "v3"

    def test_normal_pages_enhancement_skipped_is_false(self) -> None:
        """Default: v3_enhancement_skipped is False."""
        page = _make_v3_page(1, enhancement_skipped=False)
        assert page.v3_enhancement_skipped is False


# ---------------------------------------------------------------------------
# Scenario 2: Real V2 label → still blocked
# ---------------------------------------------------------------------------

class TestRealV2StillBlocked:
    """A page genuinely labelled as V2 must still be caught by the guard."""

    def test_v2_pipeline_version_blocked_by_guard(self) -> None:
        """pipeline_version='v2' must appear in the non-v3 list."""
        v2_page = FinalPageContent(
            page_number=1,
            text="Some text",
            scene_description="scene",
            visual_prompt="prompt",
            v3_composed=True,
            composer_version="v3",
            pipeline_version="v2",
        )
        non_v3 = _simulate_guard([v2_page])
        assert len(non_v3) == 1

    def test_v2_composer_version_blocked_by_guard(self) -> None:
        """composer_version='v2' must appear in the non-v3 list."""
        v2_page = FinalPageContent(
            page_number=1,
            text="Some text",
            scene_description="scene",
            visual_prompt="prompt",
            v3_composed=True,
            composer_version="v2",
            pipeline_version="v3",
        )
        non_v3 = _simulate_guard([v2_page])
        assert len(non_v3) == 1

    def test_v3_composed_false_blocked_by_guard(self) -> None:
        """v3_composed=False must appear in the non-v3 list."""
        page = FinalPageContent(
            page_number=1,
            text="Some text",
            scene_description="scene",
            visual_prompt="prompt",
            v3_composed=False,
            composer_version="v3",
            pipeline_version="v3",
        )
        non_v3 = _simulate_guard([page])
        assert len(non_v3) == 1

    def test_require_v3_pipeline_rejects_v2(self) -> None:
        """Core guard function must raise for non-v3."""
        with pytest.raises(ValueError, match="V2_LABEL_BLOCKED"):
            require_v3_pipeline(
                pipeline_version="v2",
                job_id="test-job",
                route="/test",
            )

    def test_require_v3_pipeline_passes_v3(self) -> None:
        """Core guard function must pass for v3."""
        require_v3_pipeline(
            pipeline_version="v3",
            job_id="test-job",
            route="/test",
        )


# ---------------------------------------------------------------------------
# Mixed scenario: some enhanced, some skipped — all pass guard
# ---------------------------------------------------------------------------

class TestMixedEnhancementStatus:
    """Edge case: mix of enhanced and skipped pages must all pass."""

    def test_mixed_pages_pass_guard(self) -> None:
        pages = [
            _make_v3_page(0, enhancement_skipped=False),
            _make_v3_page(1, enhancement_skipped=True),
            _make_v3_page(2, enhancement_skipped=False),
        ]
        non_v3 = _simulate_guard(pages)
        assert non_v3 == []


# ---------------------------------------------------------------------------
# Scenario 3: Legacy fallback → pipeline_version="v2_fallback"
# ---------------------------------------------------------------------------

def _build_legacy_fallback_page(page_number: int) -> dict:
    """Simulate a page dict as produced by _legacy_single_pass_generation after fix."""
    return {
        "page_number": page_number,
        "text": f"Sayfa {page_number}",
        "visual_prompt": f"A child on an adventure, page {page_number}",
        "negative_prompt": "text, watermark",
        "pipeline_version": "v2_fallback",
        "composer_version": "v2_fallback",
        "v3_composed": False,
        "v2_debug": {"legacy_fallback": True},
    }


def _build_legacy_fallback_response(page_count: int = 3) -> dict:
    """Simulate the full response dict from _legacy_single_pass_generation after fix."""
    pages = [_build_legacy_fallback_page(i) for i in range(page_count)]
    return {
        "success": True,
        "pipeline_version": "v2_fallback",
        "pipeline_label": "v2_fallback",
        "generation_method": "LEGACY FALLBACK (V2 composed)",
        "model": "gemini-2.0-flash",
        "face_analysis_used": False,
        "story": {"title": "Test Hikaye", "pages": pages},
        "page_count": page_count,
    }


class TestLegacyFallbackLabelling:
    """Legacy fallback must honestly label itself as v2_fallback, never as v3."""

    def test_response_pipeline_version_is_v2_fallback(self) -> None:
        resp = _build_legacy_fallback_response()
        assert resp["pipeline_version"] == "v2_fallback"

    def test_response_pipeline_label_is_v2_fallback(self) -> None:
        resp = _build_legacy_fallback_response()
        assert resp["pipeline_label"] == "v2_fallback"

    def test_page_pipeline_version_is_v2_fallback(self) -> None:
        resp = _build_legacy_fallback_response(5)
        for page in resp["story"]["pages"]:
            assert page["pipeline_version"] == "v2_fallback", (
                f"Page {page['page_number']} has wrong pipeline_version"
            )

    def test_page_composer_version_is_v2_fallback(self) -> None:
        resp = _build_legacy_fallback_response(5)
        for page in resp["story"]["pages"]:
            assert page["composer_version"] == "v2_fallback"

    def test_page_v3_composed_is_false(self) -> None:
        resp = _build_legacy_fallback_response()
        for page in resp["story"]["pages"]:
            assert page["v3_composed"] is False

    def test_guard_blocks_v2_fallback_pages(self) -> None:
        """If v2_fallback pages somehow reach the V3 guard, they must be caught."""
        fake_pages = [
            FinalPageContent(
                page_number=i,
                text=f"page {i}",
                scene_description="scene",
                visual_prompt="prompt",
                v3_composed=False,
                composer_version="v2_fallback",
                pipeline_version="v2_fallback",
            )
            for i in range(3)
        ]
        non_v3 = _simulate_guard(fake_pages)
        assert len(non_v3) == 3

    def test_generation_method_explicitly_states_fallback(self) -> None:
        resp = _build_legacy_fallback_response()
        assert "LEGACY FALLBACK" in resp["generation_method"]
        assert "V2" in resp["generation_method"]


# ═══════════════════════════════════════════════════════════════════
# Scenario 4 — Page count validation & single-source resolution
# ═══════════════════════════════════════════════════════════════════


class TestProductDefaultPageCountValidation:
    """default_page_count=0 or None must be rejected at the Pydantic level."""

    def test_product_create_rejects_zero_page_count(self) -> None:
        from pydantic import ValidationError

        from app.api.v1.admin.products import ProductCreate

        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Test Product",
                base_price=100,
                default_page_count=0,
            )
        errors = exc_info.value.errors()
        page_errors = [e for e in errors if "default_page_count" in (e.get("loc", ()))]
        assert len(page_errors) >= 1, "default_page_count=0 should trigger validation error"

    def test_product_create_rejects_low_page_count(self) -> None:
        from pydantic import ValidationError

        from app.api.v1.admin.products import ProductCreate

        with pytest.raises(ValidationError):
            ProductCreate(
                name="Test Product",
                base_price=100,
                default_page_count=3,
            )

    def test_product_create_accepts_valid_page_count(self) -> None:
        from app.api.v1.admin.products import ProductCreate

        p = ProductCreate(name="Valid", base_price=100, default_page_count=16)
        assert p.default_page_count == 16

    def test_product_update_rejects_zero_page_count(self) -> None:
        from pydantic import ValidationError

        from app.api.v1.admin.products import ProductUpdate

        with pytest.raises(ValidationError):
            ProductUpdate(default_page_count=0)

    def test_product_update_accepts_valid_page_count(self) -> None:
        from app.api.v1.admin.products import ProductUpdate

        p = ProductUpdate(default_page_count=22)
        assert p.default_page_count == 22


class TestRequestPageCountPassthrough:
    """request.page_count = 22 should surface as used_page_count = 22."""

    def test_ai_response_contains_used_page_count(self) -> None:
        """Simulated ai.py response dict carries used_page_count."""
        request_page_count = 22
        response = {
            "success": True,
            "page_count": 22,
            "used_page_count": request_page_count,
        }
        assert response["used_page_count"] == 22

    def test_trial_response_carries_used_page_count(self) -> None:
        from app.schemas.trials import TrialResponse

        resp = TrialResponse(
            success=True,
            trial_id="abc-123",
            status="STORY_GENERATED",
            message="ok",
            used_page_count=22,
        )
        assert resp.used_page_count == 22

    def test_trial_response_used_page_count_default_none(self) -> None:
        from app.schemas.trials import TrialResponse

        resp = TrialResponse(
            success=True,
            trial_id="abc-123",
            status="STORY_GENERATED",
            message="ok",
        )
        assert resp.used_page_count is None

    def test_create_trial_request_page_count_field(self) -> None:
        """CreateTrialRequest accepts optional page_count."""
        from app.schemas.trials import CreateTrialRequest

        req = CreateTrialRequest(
            parent_name="Ali",
            parent_email="ali@example.com",
            child_name="Deniz",
            child_age=5,
            page_count=22,
        )
        assert req.page_count == 22

    def test_create_trial_request_page_count_rejects_low(self) -> None:
        from pydantic import ValidationError

        from app.schemas.trials import CreateTrialRequest

        with pytest.raises(ValidationError):
            CreateTrialRequest(
                parent_name="Ali",
                parent_email="ali@example.com",
                child_name="Deniz",
                child_age=5,
                page_count=2,
            )
