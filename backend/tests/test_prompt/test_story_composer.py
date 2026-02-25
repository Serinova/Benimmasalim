"""Hikaye prompt composer testleri."""

from unittest.mock import MagicMock

import pytest

from app.prompt.story_composer import compose_story_prompt


class TestComposeStoryPrompt:
    @pytest.fixture
    def scenario(self):
        s = MagicMock()
        s.story_prompt_tr = "Çocuk uzay macerasına çıkar"
        s.ai_prompt_template = None
        s.location_en = "Cappadocia"
        s.flags = {"no_family": True}
        s.name = "Uzay Macerası"
        return s

    @pytest.fixture
    def outcomes(self):
        o1 = MagicMock()
        o1.name = "Cesaret"
        o1.effective_ai_instruction = "Çocuk korkularıyla yüzleşmeli"
        o2 = MagicMock()
        o2.name = "Paylaşma"
        o2.effective_ai_instruction = "Çocuk paylaşmanın değerini öğrenmeli"
        return [o1, o2]

    def test_contains_child_name(self, scenario, outcomes):
        prompt = compose_story_prompt(scenario, outcomes, "Enes", 7, "erkek", 16)
        assert "Enes" in prompt

    def test_contains_page_count(self, scenario, outcomes):
        prompt = compose_story_prompt(scenario, outcomes, "Enes", 7, "erkek", 16)
        assert "16" in prompt

    def test_contains_location(self, scenario, outcomes):
        prompt = compose_story_prompt(scenario, outcomes, "Enes", 7, "erkek")
        assert "Cappadocia" in prompt

    def test_contains_no_family_rule(self, scenario, outcomes):
        prompt = compose_story_prompt(scenario, outcomes, "Enes", 7, "erkek")
        assert "anne" in prompt.lower() or "AİLE" in prompt

    def test_contains_educational_values(self, scenario, outcomes):
        prompt = compose_story_prompt(scenario, outcomes, "Enes", 7, "erkek")
        assert "Cesaret" in prompt
        assert "Paylaşma" in prompt

    def test_gender_erkek(self, scenario, outcomes):
        prompt = compose_story_prompt(scenario, outcomes, "Ali", 6, "erkek")
        assert "erkek çocuk" in prompt

    def test_gender_kiz(self, scenario, outcomes):
        prompt = compose_story_prompt(scenario, outcomes, "Ela", 5, "kız")
        assert "kız çocuk" in prompt
