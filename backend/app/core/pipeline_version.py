"""Pipeline version guard utilities (V3 single source of truth)."""

from __future__ import annotations

from typing import Literal

PipelineVersion = Literal["v3"]


def prompt_builder_name_for_version(pipeline_version: str) -> str:
    if pipeline_version != "v3":
        return "blocked_non_v3_builder"
    return "v3_blueprint_visual_prompt_builder"


def require_v3_pipeline(*, pipeline_version: str, job_id: str, route: str) -> None:
    """Fail hard when pipeline is not V3."""
    if pipeline_version != "v3":
        raise ValueError(
            "V2_LABEL_BLOCKED: expected v3. "
            f"received={pipeline_version!r}, route={route}, jobId={job_id}"
        )
