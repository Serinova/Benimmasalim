"""Mini E2E: Admin preview detail returns cache-busted page_images and generation manifest.

Requires test DB (test_benimmasalim). Set E2E_RUN=1 and have DB running to execute.
"""

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story_preview import StoryPreview
from app.prompt_engine import STRICT_NEGATIVE_ADDITIONS, get_strict_negative_additions

E2E_RUN = os.environ.get("E2E_RUN", "").strip() == "1"


@pytest.mark.asyncio
@pytest.mark.skipif(not E2E_RUN, reason="E2E requires E2E_RUN=1 and test DB test_benimmasalim")
async def test_preview_detail_cache_bust_and_manifest(db_session: AsyncSession, client):
    """Create a preview with page_images + generation_manifest_json, GET detail, assert cache bust and manifest."""
    now = datetime.now(UTC)
    preview = StoryPreview(
        parent_name="E2E Parent",
        parent_email="e2e@test.local",
        child_name="E2E Child",
        child_age=5,
        story_title="E2E Story",
        story_pages=[
            {"page_number": 0, "text": "Cover", "visual_prompt": "Cover scene"},
            {"page_number": 1, "text": "Page 1", "visual_prompt": "Page 1 scene"},
        ],
        status="PENDING",
        page_images={
            "0": "https://storage.example.com/stories/abc/page_0.png",
            "1": "https://storage.example.com/stories/abc/page_1.png",
        },
        generation_manifest_json={
            "0": {
                "provider": "fal",
                "model": "fal-ai/flux-pulid",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "width": 768,
                "height": 1024,
                "is_cover": True,
                "prompt_hash": "a1b2c3d4e5f6",
                "negative_hash": "f6e5d4c3b2a1",
                "reference_image_used": True,
            },
            "1": {
                "provider": "fal",
                "model": "fal-ai/flux-pulid",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "width": 1024,
                "height": 768,
                "is_cover": False,
                "prompt_hash": "x9y8z7w6",
                "negative_hash": "w6z7y8x9",
                "reference_image_used": True,
            },
        },
        updated_at=now,
    )
    db_session.add(preview)
    await db_session.flush()
    preview_id = preview.id

    response = await client.get(f"/api/v1/admin/orders/previews-test/{preview_id}")
    assert response.status_code == 200, response.text
    data = response.json()

    # A) page_images URLs must have ?v= or &v= (cache bust)
    page_images = data.get("page_images") or {}
    assert "0" in page_images and "1" in page_images
    url0 = page_images["0"]
    url1 = page_images["1"]
    assert "?v=" in url0 or "&v=" in url0, f"page_images['0'] should have cache-bust param: {url0}"
    assert "?v=" in url1 or "&v=" in url1, f"page_images['1'] should have cache-bust param: {url1}"

    # B) generation_manifest_json present and populated
    manifest = data.get("generation_manifest_json")
    assert manifest is not None, "generation_manifest_json should be present"
    assert "0" in manifest and "1" in manifest

    # C) page "0": is_cover=true, width=768, height=1024
    m0 = manifest["0"]
    assert m0.get("is_cover") is True, "page 0 must be cover"
    assert m0.get("width") == 768 and m0.get("height") == 1024, "page 0 must be 768x1024"

    # D) page "1": is_cover=false, width=1024, height=768
    m1 = manifest["1"]
    assert m1.get("is_cover") is False, "page 1 must not be cover"
    assert m1.get("width") == 1024 and m1.get("height") == 768, "page 1 must be 1024x768"

    # E) strict negative additions include typographic (consistency with manifest/prompt_debug)
    strict_negative = get_strict_negative_additions()
    assert "typographic" in strict_negative, "STRICT_NEGATIVE_ADDITIONS must include typographic"
    assert strict_negative == STRICT_NEGATIVE_ADDITIONS
