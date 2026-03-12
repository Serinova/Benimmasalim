"""Tests for companion resolution and placeholder replacement."""
import pytest


class TestResolveCompanionPlaceholder:
    """Test _resolve_companion_placeholder function."""

    def test_no_placeholder_returns_unchanged(self):
        """Story without {animal_friend} should pass through unchanged."""
        from app.services.ai._story_blueprint import _resolve_companion_placeholder

        class MockScenario:
            name = "Test"
            custom_inputs_schema = None

        text = "Bu bir hikaye metnidir. Macera başlar."
        result = _resolve_companion_placeholder(MockScenario(), text)
        assert result == text

    def test_placeholder_replaced_with_default(self):
        """Placeholder should be replaced with custom_inputs default."""
        from app.services.ai._story_blueprint import _resolve_companion_placeholder

        class MockScenario:
            name = "Kapadokya Macerası"
            custom_inputs_schema = [
                {
                    "key": "animal_friend",
                    "type": "select",
                    "label": "Yol Arkadaşı",
                    "default": "Cesur Yılkı Atı",
                    "options": [],
                }
            ]

        text = "Çocuk {animal_friend} ile birlikte yola çıktı."
        result = _resolve_companion_placeholder(MockScenario(), text)
        assert "{animal_friend}" not in result
        assert "Cesur Yılkı Atı" in result

    def test_placeholder_replaced_with_fallback(self):
        """When no custom_inputs_schema, should use fallback companion."""
        from app.services.ai._story_blueprint import _resolve_companion_placeholder

        class MockScenario:
            name = "Test"
            custom_inputs_schema = None

        text = "Çocuk {animal_friend} ile yürüdü."
        result = _resolve_companion_placeholder(MockScenario(), text)
        assert "{animal_friend}" not in result
        assert "tilki" in result.lower()

    def test_animal_friend_en_also_resolved(self):
        """Both TR and EN placeholders should be resolved."""
        from app.services.ai._story_blueprint import _resolve_companion_placeholder

        class MockScenario:
            name = "Test"
            custom_inputs_schema = [
                {
                    "key": "animal_friend",
                    "default": "Cesur Dağ Kartalı",
                }
            ]

        text = "TR: {animal_friend} EN: {animal_friend_en}"
        result = _resolve_companion_placeholder(MockScenario(), text)
        assert "{animal_friend}" not in result
        assert "{animal_friend_en}" not in result
        assert "Cesur Dağ Kartalı" in result
        assert "eagle" in result.lower()

    def test_all_known_companions_resolve(self):
        """All companion names in _TR_TO_EN should have valid mappings."""
        from app.services.ai._story_blueprint import _resolve_companion_placeholder

        known_companions = [
            "Cesur Yılkı Atı", "Cesur Step Tilkisi",
            "Cesur Dağ Kartalı", "Minik Beyaz Güvercin",
            "Renkli Papağan", "Gümüş Robot Nova", "Pelüş Ayıcık",
            "Köpek", "Efes Kedisi",
            "Sevimli Zeytin Dalı Serçesi",
            "Altın Çöl Şahini", "Gizemli Sarnıç Kedisi",
            "Konuşan Masal Baykuşu", "Dostça Yunus",
        ]

        for companion_tr in known_companions:
            class MockScenario:
                name = "Test"
                custom_inputs_schema = [{"key": "animal_friend", "default": companion_tr}]

            text = "Friend: {animal_friend} / EN: {animal_friend_en}"
            result = _resolve_companion_placeholder(MockScenario(), text)
            assert "{animal_friend}" not in result, f"TR placeholder not resolved for: {companion_tr}"
            assert "{animal_friend_en}" not in result, f"EN placeholder not resolved for: {companion_tr}"
            assert "a small animal companion" not in result, f"Fallback used for known: {companion_tr}"


class TestExtractCompanionFromPages:
    """Test _extract_companion_from_pages function."""

    def test_no_scenario_returns_empty(self):
        """No scenario should return empty tuple."""
        from app.tasks.generate_book import _extract_companion_from_pages

        name, species, appearance = _extract_companion_from_pages([], None)
        assert name == ""
        assert species == ""
        assert appearance == ""

    def test_scenario_with_animal_friend_default(self):
        """Should extract companion from custom_inputs_schema."""
        from app.tasks.generate_book import _extract_companion_from_pages

        class MockScenario:
            name = "Kapadokya Macerası"
            custom_inputs_schema = [
                {
                    "key": "animal_friend",
                    "default": "Cesur Yılkı Atı",
                }
            ]

        name, species, appearance = _extract_companion_from_pages([], MockScenario())
        assert name == "Yılkı"
        assert species == "wild horse"
        assert "horse" in appearance.lower()

    def test_scenario_without_custom_inputs(self):
        """Scenario without custom_inputs should return empty."""
        from app.tasks.generate_book import _extract_companion_from_pages

        class MockScenario:
            name = "Galata"
            custom_inputs_schema = None

        name, species, appearance = _extract_companion_from_pages([], MockScenario())
        assert name == ""
        assert species == ""

    def test_all_known_companions_extract(self):
        """All known companion defaults should extract properly."""
        from app.tasks.generate_book import _extract_companion_from_pages

        companions_to_test = {
            "Cesur Yılkı Atı": "wild horse",
            "Cesur Step Tilkisi": "fox",
            "Cesur Dağ Kartalı": "eagle",
            "Minik Beyaz Güvercin": "dove",
            "Renkli Papağan": "macaw parrot",
            "Gümüş Robot Nova": "robot",
            "Pelüş Ayıcık": "teddy bear plushie",
            "Köpek": "dog",
            "Efes Kedisi": "cat",
            "Altın Çöl Şahini": "hawk",
            "Gizemli Sarnıç Kedisi": "cat",
            "Konuşan Masal Baykuşu": "owl",
            "Dostça Yunus": "dolphin",
        }

        for companion_tr, expected_species in companions_to_test.items():
            class MockScenario:
                name = "Test"
                custom_inputs_schema = [
                    {"key": "animal_friend", "default": companion_tr}
                ]

            name, species, appearance = _extract_companion_from_pages([], MockScenario())
            assert species == expected_species, f"Failed for {companion_tr}: got {species}"
            assert name != "", f"Name is empty for {companion_tr}"
            assert appearance != "", f"Appearance is empty for {companion_tr}"


class TestBookContextWithCompanion:
    """Test that BookContext properly receives companion info."""

    def test_book_context_with_companion(self):
        """BookContext should store companion fields."""
        from app.prompt.book_context import BookContext

        ctx = BookContext.build(
            child_name="Ali",
            child_age=7,
            child_gender="erkek",
            companion_name="Yılkı",
            companion_species="wild horse",
            companion_appearance="small brown wild Cappadocian horse",
        )
        assert ctx.companion_name == "Yılkı"
        assert ctx.companion_species == "wild horse"
        assert "horse" in ctx.companion_appearance

    def test_book_context_default_empty_companion(self):
        """BookContext without companion should have empty fields."""
        from app.prompt.book_context import BookContext

        ctx = BookContext.build(
            child_name="Ali",
            child_age=7,
            child_gender="erkek",
        )
        assert ctx.companion_name == ""
        assert ctx.companion_species == ""


class TestCastLockWithCompanion:
    """Test that page_builder generates correct CAST LOCK."""

    def test_cast_lock_with_companion(self):
        """When companion is set, CAST LOCK should include both child and companion."""
        from app.prompt.book_context import BookContext
        from app.prompt.page_builder import build_page_prompt

        ctx = BookContext.build(
            child_name="Ali",
            child_age=7,
            child_gender="erkek",
            companion_name="Yılkı",
            companion_species="wild horse",
            companion_appearance="small brown wild horse",
        )
        prompt = build_page_prompt(ctx, "Ali runs through a field", page_number=1)
        assert "CAST LOCK" in prompt
        assert "Yılkı" in prompt
        assert "wild horse" in prompt
        assert "two characters" in prompt.lower() or "EXACTLY two" in prompt

    def test_cast_lock_without_companion(self):
        """Without companion, CAST LOCK should allow only one character."""
        from app.prompt.book_context import BookContext
        from app.prompt.page_builder import build_page_prompt

        ctx = BookContext.build(
            child_name="Ali",
            child_age=7,
            child_gender="erkek",
        )
        prompt = build_page_prompt(ctx, "Ali walks alone", page_number=1)
        assert "CAST LOCK" in prompt
        assert "Only ONE" in prompt or "ONE human character" in prompt
