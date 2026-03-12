"""PromptComposer testleri — tutarlılık doğrulaması."""

import pytest

from app.prompt.book_context import BookContext
from app.prompt.composer import PromptComposer


class TestPromptComposer:
    @pytest.fixture
    def ctx(self) -> BookContext:
        return BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            style_modifier="pixar",
            clothing_description="red t-shirt and blue jeans",
            face_reference_url="https://example.com/face.jpg",
            page_count=16,
            story_title="Enes'in Kapadokya Macerası",
        )

    def test_cover_prompt_contains_style(self, ctx: BookContext):
        composer = PromptComposer(ctx)
        result = composer.compose_cover("A magical cave with fairy chimneys")
        assert "Pixar" in result.prompt
        assert result.negative_prompt
        assert result.metadata["is_cover"] is True

    def test_page_prompt_contains_style(self, ctx: BookContext):
        composer = PromptComposer(ctx)
        result = composer.compose_page("Child exploring a garden", page_number=3)
        assert "Pixar" in result.prompt
        assert result.metadata["page_number"] == 3
        assert result.metadata["is_cover"] is False

    def test_negative_prompt_consistent_across_pages(self, ctx: BookContext):
        composer = PromptComposer(ctx)
        cover = composer.compose_cover("Scene A")
        page1 = composer.compose_page("Scene B", page_number=1)
        page2 = composer.compose_page("Scene C", page_number=2)
        assert cover.negative_prompt == page1.negative_prompt == page2.negative_prompt

    def test_clothing_in_prompt(self, ctx: BookContext):
        composer = PromptComposer(ctx)
        result = composer.compose_page("Child running", page_number=1)
        assert "red t-shirt" in result.prompt

    def test_face_reference_adds_likeness(self, ctx: BookContext):
        composer = PromptComposer(ctx)
        result = composer.compose_page("Scene", page_number=1)
        assert "stylized illustration" in result.prompt.lower() or "likeness" in result.prompt.lower()

    def test_no_face_reference_no_likeness(self):
        ctx = BookContext.build(
            child_name="Ali",
            child_age=5,
            child_gender="erkek",
            style_modifier="watercolor",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Scene", page_number=1)
        # Without face_reference_url, the PuLID likeness hint should not be injected.
        # Note: 'reference' can appear as part of style template (e.g. "from the reference photo")
        # so we only check the explicit likeness hint string is absent.
        from app.prompt.templates import LIKENESS_HINT
        assert LIKENESS_HINT not in result.prompt

    def test_all_styles_produce_different_prompts(self):
        styles = ["default", "pixar", "watercolor", "anime", "soft_pastel", "adventure_digital"]
        prompts: set[str] = set()
        for style_name in styles:
            ctx = BookContext.build(
                child_name="Test",
                child_age=6,
                child_gender="erkek",
                style_modifier=style_name,
            )
            composer = PromptComposer(ctx)
            result = composer.compose_page("A child standing in a meadow", page_number=1)
            prompts.add(result.prompt[:200])
        assert len(prompts) == len(styles), "Her stil farklı prompt üretmeli"

    def test_prompt_length_within_limits(self, ctx: BookContext):
        long_scene = "A child exploring " * 100
        composer = PromptComposer(ctx)
        result = composer.compose_page(long_scene, page_number=1)
        assert len(result.prompt) <= 2048


class TestNegativePromptConsistency:
    """Negatif prompt'un kitap boyunca sabit kaldığını doğrular."""

    def test_same_negative_for_all_pages(self):
        ctx = BookContext.build(
            child_name="Ela",
            child_age=5,
            child_gender="kız",
            style_modifier="anime",
            face_reference_url="https://example.com/face.jpg",
        )
        composer = PromptComposer(ctx)
        negatives = set()
        for i in range(10):
            result = composer.compose_page(f"Scene {i}", page_number=i + 1)
            negatives.add(result.negative_prompt)
        assert len(negatives) == 1, "Tüm sayfalar aynı negatif prompt kullanmalı"
