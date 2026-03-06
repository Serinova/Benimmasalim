"""Backward-compatibility shim for visual_prompt_validator."""

from app.prompt_engine import (
    VisualValidationReport,
    autofix_visual_prompts as autofix,  # noqa: F401
    validate_visual_prompts as validate_all,  # noqa: F401
)

ValidationResult = VisualValidationReport
