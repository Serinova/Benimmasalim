"""Style independence: scene-only prompts have no style tokens; style added at single point."""

import pytest

from app.prompt_engine import (
    DEFAULT_COVER_TEMPLATE_EN,
    DEFAULT_INNER_TEMPLATE_EN,
    LIKENESS_HINT_WHEN_REFERENCE,
    compose_visual_prompt,
)

# Tokens that must NOT appear in scene-only (stored) prompts
STYLE_TOKENS_FORBIDDEN_IN_SCENE = (
    "pixar",
    "disney",
    "ghibli",
    "2d",
    "3d",
    "children's book illustration",
    "children's book cover",
    "book cover illustration",
    "anime",
    "watercolor",
    "cartoon",
    "storybook illustration",
)


def test_scene_only_prompt_has_no_style_tokens():
    """Compose with no style_prompt_en must not contain style tokens (scene-only path)."""
    scene = "Running among fairy chimneys in Cappadocia. Balloons in the sky."
    template_cover = DEFAULT_COVER_TEMPLATE_EN
    template_inner = DEFAULT_INNER_TEMPLATE_EN
    clothing = "adventure jacket and comfortable pants"
    for is_cover in (True, False):
        template_en = template_cover if is_cover else template_inner
        prompt, _ = compose_visual_prompt(
            scene_description=scene,
            is_cover=is_cover,
            template_en=template_en,
            clothing_description=clothing,
        )
        lower = prompt.lower()
        for token in STYLE_TOKENS_FORBIDDEN_IN_SCENE:
            assert token not in lower, f"Scene-only prompt must not contain '{token}'"


def test_style_injected_only_at_compose():
    """Style text appears exactly once when added via compose_visual_prompt."""
    scene = "A child in Cappadocia. Text space at bottom."
    style_text = "Pixar-style 3D, vibrant colors"
    prompt, _ = compose_visual_prompt(
        scene,
        template_vars=None,
        is_cover=False,
        style_text=style_text,
        style_negative="",
    )
    assert "STYLE:" in prompt
    assert "Pixar" in prompt or "pixar" in prompt
    # Style block should appear once
    assert prompt.count("STYLE:") == 1


def test_double_style_prevented():
    """Final prompt does not duplicate style_text (e.g. twice)."""
    scene = "Fairy chimneys and balloons. Text space at bottom."
    style_text = "children's book illustration, soft colors"
    prompt, _ = compose_visual_prompt(
        scene,
        template_vars=None,
        is_cover=False,
        style_text=style_text,
        style_negative="",
    )
    # "children's book" might appear once in STYLE block; should not appear twice
    count = prompt.lower().count("children's book")
    assert count <= 1, "Style phrase should not be duplicated"


def test_compose_idempotent_no_double_style_block():
    """Calling compose_visual_prompt on an already-composed prompt must NOT produce STYLE: twice."""
    scene = "A child exploring Cappadocia. Text space at bottom."
    style = "watercolor children's book illustration"
    # First composition (e.g. in api/v1/ai.py for display)
    composed_once, _ = compose_visual_prompt(
        scene,
        is_cover=False,
        style_text=style,
    )
    assert composed_once.count("STYLE:") == 1, "First compose should have exactly 1 STYLE:"

    # Second composition (e.g. in fal_ai_service for generation)
    composed_twice, _ = compose_visual_prompt(
        composed_once,
        is_cover=False,
        style_text=style,
    )
    assert composed_twice.count("STYLE:") == 1, "Second compose must still have exactly 1 STYLE:"
    assert "watercolor" in composed_twice.lower()


def test_compose_strips_old_style_before_new():
    """If input already has STYLE: block, it's replaced — not appended."""
    input_with_style = "A child in Cappadocia.\n\nSTYLE:\nold-style tokens"
    prompt, _ = compose_visual_prompt(
        input_with_style,
        is_cover=False,
        style_text="new-style tokens",
    )
    assert prompt.count("STYLE:") == 1
    assert "new-style tokens" in prompt
    assert "old-style tokens" not in prompt


def test_style_value_with_style_prefix_produces_single_block():
    """If admin stores style value as 'STYLE: watercolor', result must NOT be 'STYLE:\\nSTYLE: ...'."""
    prompt, _ = compose_visual_prompt(
        "Fairy chimneys. Text space at bottom.",
        is_cover=False,
        style_text="STYLE: watercolor soft edges",
    )
    assert prompt.count("STYLE:") == 1
    assert "watercolor soft edges" in prompt


def test_likeness_hint_optional():
    """Likeness hint is applied when provided."""
    scene = "A child in adventure. Text space at bottom."
    prompt_with, _ = compose_visual_prompt(
        scene,
        template_vars=None,
        is_cover=False,
        likeness_hint=LIKENESS_HINT_WHEN_REFERENCE,
    )
    prompt_without, _ = compose_visual_prompt(
        scene,
        template_vars=None,
        is_cover=False,
    )
    assert "hairstyle" in prompt_with.lower() or "Preserve from reference" in prompt_with
    assert "Preserve from reference" not in prompt_without


def test_compose_normalizes_and_validates():
    """Compose path applies Kapadokya->Cappadocia and placeholder validation."""
    out, _ = compose_visual_prompt(
        "Fairy chimneys in Kapadokya. Text space at bottom.",
        template_vars=None,
        is_cover=False,
    )
    assert "Cappadocia" in out
    assert "Kapadokya" not in out

    from app.prompt_engine import VisualPromptValidationError

    with pytest.raises(VisualPromptValidationError):
        compose_visual_prompt(
            "Scene: {scene_description}. Text space at bottom.",
            template_vars=None,
            is_cover=False,
        )
