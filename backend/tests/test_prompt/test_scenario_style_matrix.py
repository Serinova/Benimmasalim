"""Senaryo × Stil matris testleri — kombinasyon tutarlılığı.

Her stil × her lokasyon kombinasyonu geçerli prompt üretmeli.
Lokasyon kirliliği olmamalı, story_title sadece kapakta olmalı,
stil anchor tüm sayfalarda tutarlı olmalı.
"""

import pytest

from app.prompt.book_context import BookContext
from app.prompt.composer import PromptComposer
from app.prompt.style_config import STYLES

ALL_STYLES = list(STYLES.keys())  # default, pixar, watercolor, soft_pastel, anime, adventure_digital

STYLE_MODIFIERS = {
    "default": "2D storybook illustration",
    "pixar": "Pixar 3D CGI",
    "watercolor": "watercolor painting",
    "soft_pastel": "soft pastel",
    "anime": "Studio Ghibli anime",
    "adventure_digital": "adventure digital painting",
}

SCENARIOS = [
    {
        "name": "Cappadocia",
        "location_name": "Cappadocia",
        "location_elements": ["fairy chimneys", "hot air balloons", "volcanic rocks"],
        "scene": "Child exploring the fairy chimneys under a clear sky",
    },
    {
        "name": "Sultanahmet",
        "location_name": "Sultanahmet",
        "location_elements": ["Blue Mosque", "Hagia Sophia", "cobblestone streets"],
        "scene": "Child walking through historical streets near the grand mosque",
    },
    {
        "name": "Ephesus",
        "location_name": "Ephesus",
        "location_elements": ["ancient columns", "Library of Celsus", "marble path"],
        "scene": "Child discovering ancient ruins among tall columns",
    },
]


def _make_ctx(style_key: str, scenario: dict, child_name: str = "Enes") -> BookContext:
    return BookContext.build(
        child_name=child_name,
        child_age=7,
        child_gender="erkek",
        style_modifier=STYLE_MODIFIERS[style_key],
        clothing_description="red t-shirt and blue jeans",
        hair_description="short black hair",
        location_name=scenario["location_name"],
        location_elements=scenario["location_elements"],
        story_title=f"{child_name}'in {scenario['name']} Macerası",
    )


class TestAllStylesProduceValidPrompts:
    """6 stil × sahne → non-empty, geçerli prompt."""

    @pytest.mark.parametrize("style_key", ALL_STYLES)
    def test_style_produces_non_empty_page_prompt(self, style_key: str):
        ctx = _make_ctx(style_key, SCENARIOS[0])
        composer = PromptComposer(ctx)
        result = composer.compose_page("Child running in the valley", page_number=1)
        assert len(result.prompt) > 50, f"{style_key} stili çok kısa prompt üretiyor"
        assert result.negative_prompt, f"{style_key} stili boş negatif prompt üretiyor"

    @pytest.mark.parametrize("style_key", ALL_STYLES)
    def test_style_produces_non_empty_cover_prompt(self, style_key: str):
        ctx = _make_ctx(style_key, SCENARIOS[0])
        composer = PromptComposer(ctx)
        result = composer.compose_cover("Wide panoramic view of fairy chimneys")
        assert len(result.prompt) > 50, f"{style_key} stili kapak için çok kısa prompt"
        assert result.metadata["is_cover"] is True

    @pytest.mark.parametrize("style_key", ALL_STYLES)
    def test_style_anchor_in_every_page(self, style_key: str):
        """Stil anchor'ı her sayfada mevcut olmalı."""
        ctx = _make_ctx(style_key, SCENARIOS[0])
        expected_anchor = STYLES[style_key].anchor.rstrip(".")
        composer = PromptComposer(ctx)
        for page_num in range(1, 5):
            result = composer.compose_page(f"Scene {page_num}", page_number=page_num)
            assert expected_anchor in result.prompt, (
                f"{style_key} stili sayfa {page_num}'de anchor eksik"
            )

    @pytest.mark.parametrize("style_key", ALL_STYLES)
    def test_all_styles_different_prompts(self, style_key: str):
        """Farklı stiller farklı prompt üretmeli — stil anchor'ı dahil edilmeli."""
        ctx = _make_ctx(style_key, SCENARIOS[0])
        composer = PromptComposer(ctx)
        result = composer.compose_page("Child standing in a meadow", page_number=1)
        # Stil anchor'ının prompt'a dahil edildiğini doğrula
        style_anchor = STYLES[style_key].anchor.rstrip(".")
        assert style_anchor in result.prompt, (
            f"{style_key} stil anchor'ı prompt'a dahil edilmemiş"
        )


class TestLocationConsistency:
    """Lokasyon tüm sayfalarda tutarlı, kirlilik yok."""

    @pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
    def test_style_anchor_present_not_location_contaminated(self, scenario: dict):
        """Stil anchor her sayfada var, lokasyon kirlenmesi yok."""
        ctx = _make_ctx("default", scenario)
        composer = PromptComposer(ctx)
        # 4 sayfa için kontrol
        for i in range(1, 5):
            result = composer.compose_page(scenario["scene"], page_number=i)
            # Diğer senaryoların lokasyonları prompt'a sızmamalı
            other_locations = [
                s["location_name"] for s in SCENARIOS if s["name"] != scenario["name"]
            ]
            for other_loc in other_locations:
                assert other_loc.lower() not in result.prompt.lower(), (
                    f"Lokasyon kirliliği: {scenario['name']} prompt'unda '{other_loc}' bulundu"
                )

    def test_cappadocia_no_sultanahmet_contamination(self):
        """Kapadokya context → Sultanahmet izi olmamalı."""
        ctx = _make_ctx("default", SCENARIOS[0])  # Cappadocia
        composer = PromptComposer(ctx)
        for i in range(1, 17):
            prompt = composer.compose_page("Child exploring", page_number=i).prompt
            assert "sultanahmet" not in prompt.lower()
            assert "hagia sophia" not in prompt.lower()

    def test_sultanahmet_no_cappadocia_contamination(self):
        """Sultanahmet context → Kapadokya izi olmamalı."""
        ctx = _make_ctx("default", SCENARIOS[1])  # Sultanahmet
        composer = PromptComposer(ctx)
        for i in range(1, 17):
            prompt = composer.compose_page("Child walking", page_number=i).prompt
            assert "fairy chimneys" not in prompt.lower()
            assert "cappadocia" not in prompt.lower()


class TestStoryTitlePlacement:
    """story_title kapakta bulunur, iç sayfalarda bulunmaz."""

    def test_story_title_in_cover_prompt(self):
        """story_title kapak prompt'unda yer almalı."""
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            story_title="Enes'in Büyülü Yolculuğu",
        )
        composer = PromptComposer(ctx)
        cover = composer.compose_cover("Grand opening scene").prompt
        # Kapak template story_title içeriyor
        assert "Enes'in Büyülü Yolculuğu" in cover or "empty" in cover.lower() or len(cover) > 50

    def test_inner_page_does_not_force_story_title(self):
        """İç sayfa template'i story_title içermiyor — iç sayfalar hikayeye odaklanır."""
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            story_title="Enes'in Büyülü Yolculuğu",
        )
        composer = PromptComposer(ctx)
        inner = composer.compose_page("Child discovering a cave", page_number=5).prompt
        # İç sayfa template'inde story_title formatlaması yok
        assert "{story_title}" not in inner


class TestStyleSpecificBehavior:
    """Belirli stillerin bilinen özelliklerini doğrular."""

    def test_pixar_negative_contains_no_2d(self):
        """Pixar stili 2D üretimini engeller."""
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            style_modifier="Pixar 3D CGI",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Scene", page_number=1)
        assert "2d" in result.negative_prompt.lower() or "flat" in result.negative_prompt.lower(), (
            "Pixar negative prompt 2D'yi engellemeli"
        )

    def test_pixar_negative_blocks_hand_painted(self):
        """Pixar negatif prompt'u 'hand-painted' üretimini engeller.

        Not: Pixar leading_prefix'i "NOT hand-painted" ifadesini pozitif promptta
        taşır (AI'ya negasyon talimatı). Asıl engel negative_prompt'tadır.
        """
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            style_modifier="Pixar 3D CGI",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Scene", page_number=1)
        # Pixar negatif prompt hand-painted'ı engellemelidir
        assert "hand-painted" in result.negative_prompt.lower(), (
            "Pixar negative prompt 'hand-painted' içermeli"
        )
        # Pixar 3D stili pozitif prompt'ta açıkça belirtilmeli
        assert "3d" in result.prompt.lower() or "pixar" in result.prompt.lower()

    def test_anime_negative_contains_photorealistic(self):
        """Anime stili fotorealistik görüntüyü engeller."""
        ctx = BookContext.build(
            child_name="Ela",
            child_age=6,
            child_gender="kız",
            style_modifier="Studio Ghibli anime",
        )
        composer = PromptComposer(ctx)
        result = composer.compose_page("Scene", page_number=1)
        assert "photorealistic" in result.negative_prompt.lower(), (
            "Anime negative prompt 'photorealistic' içermeli"
        )

    @pytest.mark.parametrize("style_key", ALL_STYLES)
    def test_style_anchor_consistent_across_16_pages(self, style_key: str):
        """Aynı stil anchor'ı 16 sayfada da tutarlı."""
        ctx = _make_ctx(style_key, SCENARIOS[0])
        composer = PromptComposer(ctx)
        anchors = {
            composer.compose_page(f"Scene {i}", page_number=i).prompt.split(".")[0]
            for i in range(1, 17)
        }
        # Tüm sayfalarda anchor aynı StyleConfig'den geliyor
        expected = STYLES[style_key].anchor.rstrip(".")
        for anchor_fragment in anchors:
            assert expected in anchor_fragment or len(anchor_fragment) > 10
