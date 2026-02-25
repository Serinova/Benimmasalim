"""Kıyafet tutarlılığı testleri — 16 sayfa boyunca aynı kıyafet.

BookContext bir kez oluşturulur; tüm iç sayfalarda ve kapakta
aynı kıyafet ifadesi görünmeli, negatif prompt da değişimi engeller.
"""

from app.prompt.book_context import BookContext
from app.prompt.composer import PromptComposer
from app.prompt.negative_builder import build_negative


class TestClothingLockedAcrossPages:
    """Kıyafetin 16 sayfa boyunca sabit kalmasını doğrular."""

    def _make_ctx(self, clothing: str = "red t-shirt and blue jeans", gender: str = "erkek") -> BookContext:
        return BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender=gender,
            style_modifier="default",
            clothing_description=clothing,
            hair_description="short brown hair",
            location_name="Cappadocia",
            story_title="Enes'in Macerası",
        )

    def test_clothing_identical_across_all_16_pages(self):
        """16 iç sayfa prompt'unda kıyafet ifadesi tutarlı olmalı."""
        ctx = self._make_ctx()
        composer = PromptComposer(ctx)
        prompts = [
            composer.compose_page(f"Scene description for page {i}", page_number=i).prompt
            for i in range(1, 17)
        ]
        # Her prompt'ta "red t-shirt" olmalı
        for i, prompt in enumerate(prompts, start=1):
            assert "red t-shirt" in prompt, (
                f"Sayfa {i} prompt'unda kıyafet eksik: '{prompt[:120]}'"
            )

    def test_cover_clothing_matches_inner_pages(self):
        """Kapak prompt'u da iç sayfalarla aynı kıyafeti içermeli."""
        ctx = self._make_ctx()
        composer = PromptComposer(ctx)
        cover = composer.compose_cover("Wide landscape scene with the child").prompt
        page = composer.compose_page("Child exploring a garden", page_number=1).prompt
        assert "red t-shirt" in cover, "Kapakta kıyafet eksik"
        assert "red t-shirt" in page, "İç sayfada kıyafet eksik"

    def test_clothing_consistent_cover_to_last_page(self):
        """Kapaktan son sayfaya kadar kıyafet değişmemeli."""
        ctx = self._make_ctx(clothing="green jacket and white pants")
        composer = PromptComposer(ctx)
        cover = composer.compose_cover("Opening scene").prompt
        last_page = composer.compose_page("Final scene", page_number=16).prompt
        assert "green jacket" in cover
        assert "green jacket" in last_page


class TestClothingNormalizationInPrompt:
    """Türkçe kıyafet ifadelerinin İngilizce'ye çevrildiğini doğrular."""

    def test_turkish_clothing_normalized_in_page_prompt(self):
        """'kırmızı tişört ve mavi pantolon' prompt'ta İngilizce görünmeli."""
        ctx = BookContext.build(
            child_name="Ali",
            child_age=6,
            child_gender="erkek",
            clothing_description="kırmızı tişört ve mavi pantolon",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Child playing", page_number=1)
        assert "red" in result.prompt
        assert "t-shirt" in result.prompt or "tshirt" in result.prompt
        # Türkçe terimin kalmamış olması gerekir
        assert "tişört" not in result.prompt
        assert "pantolon" not in result.prompt

    def test_turkish_clothing_normalized_in_cover_prompt(self):
        """Kapak prompt'unda da normalizasyon geçerli olmalı."""
        ctx = BookContext.build(
            child_name="Ela",
            child_age=5,
            child_gender="kız",
            clothing_description="sarı elbise ve beyaz ayakkabı",
            story_title="Ela'nın Günü",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_cover("Opening scene")
        assert "yellow" in result.prompt
        assert "dress" in result.prompt
        assert "elbise" not in result.prompt


class TestDefaultClothing:
    """Boş kıyafet tanımında gender'a göre doğru default atanır."""

    def test_default_boy_clothing_when_empty(self):
        """Erkek çocuk + boş kıyafet → 'red t-shirt, blue denim overalls, and sneakers'"""
        ctx = BookContext.build(
            child_name="Can",
            child_age=6,
            child_gender="erkek",
            clothing_description="",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Child running", page_number=1)
        assert "red t-shirt" in result.prompt
        assert "blue denim overalls" in result.prompt
        assert "sneakers" in result.prompt

    def test_default_girl_clothing_when_empty(self):
        """Kız çocuk + boş kıyafet → 'yellow t-shirt, blue denim overalls, and pink sneakers'"""
        ctx = BookContext.build(
            child_name="Zeynep",
            child_age=5,
            child_gender="kız",
            clothing_description="",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Child dancing", page_number=1)
        assert "yellow t-shirt" in result.prompt
        assert "blue denim overalls" in result.prompt
        assert "pink sneakers" in result.prompt

    def test_default_boy_clothing_with_whitespace_only(self):
        """Sadece boşluk içeren kıyafet de default'a düşmeli."""
        ctx = BookContext.build(
            child_name="Mert",
            child_age=7,
            child_gender="erkek",
            clothing_description="   ",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Scene", page_number=1)
        assert "red t-shirt" in result.prompt


class TestClothingConsistencyInNegativePrompt:
    """Negatif prompt kıyafet değişimini engeller."""

    def test_negative_blocks_outfit_change(self):
        """build_negative() 'different outfit' ve 'outfit change' içermeli."""
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            clothing_description="red t-shirt and blue jeans",
        )
        negative = build_negative(ctx)
        assert "different outfit" in negative
        assert "outfit change" in negative
        assert "costume change" in negative

    def test_negative_blocks_clothing_change(self):
        """'different clothing' da negatif prompt'ta mevcut olmalı."""
        ctx = BookContext.build(
            child_name="Ela",
            child_age=5,
            child_gender="kız",
        )
        negative = build_negative(ctx)
        assert "different clothing" in negative

    def test_negative_consistent_across_16_pages(self):
        """Tüm sayfalar aynı negatif prompt'u kullanmalı (kıyafet değişimi engellensin)."""
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            clothing_description="red t-shirt and blue jeans",
        )
        composer = PromptComposer(ctx)
        negatives = {
            composer.compose_page(f"Scene {i}", page_number=i).negative_prompt
            for i in range(1, 17)
        }
        assert len(negatives) == 1, (
            f"Negatif prompt sayfa sayfa değişiyor: {len(negatives)} farklı versiyon"
        )
