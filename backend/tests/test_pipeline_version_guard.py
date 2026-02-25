from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.admin.orders import _detect_pipeline_version
from app.api.v1.orders import StoryPageData, _ensure_v3_story_pages
from app.core.pipeline_version import require_v3_pipeline


def test_require_v3_pipeline_passes_for_v3() -> None:
    require_v3_pipeline(
        pipeline_version="v3",
        job_id="job-123",
        route="/api/v1/trials/create",
    )


def test_require_v3_pipeline_fails_for_non_v3() -> None:
    with pytest.raises(ValueError, match="V2_LABEL_BLOCKED: expected v3"):
        require_v3_pipeline(
            pipeline_version="v2",
            job_id="job-456",
            route="/api/v1/ai/generate-story",
        )


def test_detect_pipeline_version_prefers_cache_blueprint() -> None:
    preview = SimpleNamespace(
        generated_prompts_cache={"blueprint_json": {"title": "x"}, "pipeline_version": "v2"},
        story_pages=[],
    )
    assert _detect_pipeline_version(preview) == "v3"


def test_detect_pipeline_version_from_cache_prompt_flags() -> None:
    preview = SimpleNamespace(
        generated_prompts_cache={
            "prompts": [
                {"page_number": 0, "pipeline_version": "v3"},
                {"page_number": 1, "composer_version": "v3"},
            ]
        },
        story_pages=[],
    )
    assert _detect_pipeline_version(preview) == "v3"


def test_detect_pipeline_version_defaults_to_v3_when_markers_missing() -> None:
    preview = SimpleNamespace(generated_prompts_cache={}, story_pages=[])
    assert _detect_pipeline_version(preview) == "v3"


def test_orders_payload_blocks_non_v3_pipeline() -> None:
    with pytest.raises(HTTPException) as exc:
        _ensure_v3_story_pages(
            [
                StoryPageData(
                    page_number=1,
                    text="x",
                    visual_prompt="y",
                    pipeline_version="v2",
                    composer_version="v2",
                )
            ],
            route="/api/v1/orders/submit-preview-async",
        )
    assert exc.value.status_code == 400
