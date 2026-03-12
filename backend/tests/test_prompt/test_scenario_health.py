"""Tests for scenario health scoring service."""
import pytest
import warnings

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent


def _make_scenario(**overrides) -> ScenarioContent:
    """Create a minimal ScenarioContent for testing."""
    defaults = {
        "theme_key": "test",
        "name": "Test Senaryo",
        "location_en": "Test",
        "default_page_count": 6,
    }
    defaults.update(overrides)
    return ScenarioContent(**defaults)


def _make_full_scenario(**overrides) -> ScenarioContent:
    """Create a fully populated ScenarioContent for testing max scores."""
    defaults = {
        "theme_key": "test_full",
        "name": "Full Test Senaryo",
        "location_en": "Test Location",
        "default_page_count": 22,
        "story_prompt_tr": " ".join(["kelime"] * 500),
        "outfit_girl": "a beautiful dress with red shoes and matching hat for adventures in style",
        "outfit_boy": "a cool vest with cargo pants and hiking boots for adventures in style",
        "companions": [
            CompanionAnchor(
                name_tr="Test Hayvan",
                name_en="test animal",
                species="dog",
                appearance=(
                    "a friendly golden retriever with floppy ears and wagging tail "
                    "and big brown eyes and fluffy fur"
                ),
            ),
        ],
        "objects": [
            ObjectAnchor(
                name_tr="Test Obje",
                appearance_en="golden ancient medallion with sun symbol, palm-sized",
                prompt_suffix="holding golden medallion — SAME on every page",
            ),
        ],
        "scenario_bible": {
            "companions": [{"name": "test"}],
            "locations": ["loc1", "loc2"],
            "consistency_rules": ["rule1"],
            "no_family": True,
        },
        "location_constraints": (
            "Pages 1-3: outdoor scenes with wide panoramic shots. "
            "Pages 4-6: indoor scenes with close-up details and moody lighting."
        ),
        "cover_prompt_template": " ".join(["word"] * 60),
        "page_prompt_template": " ".join(["word"] * 60),
        "custom_inputs_schema": [
            {"key": "animal_friend", "type": "hidden", "default": "Test Hayvan"},
        ],
    }
    defaults.update(overrides)
    return ScenarioContent(**defaults)


class TestScoreScenario:
    """Unit tests for score_scenario()."""

    def test_empty_scenario_scores_low(self):
        from app.services.scenario_health_service import score_scenario

        sc = _make_scenario()
        report = score_scenario(sc)
        # Empty scenario still gets some points (no Turkish chars, no-companion exemptions)
        # but should score low overall
        assert report.percentage < 50
        assert report.grade in ("D", "F")
        assert len(report.checks) == 10  # 10 checks now
        # Critical checks must exist
        critical = [c for c in report.checks if c.status == "critical"]
        assert len(critical) >= 3  # story_prompt, outfits, bible at minimum

    def test_full_scenario_scores_high(self):
        from app.services.scenario_health_service import score_scenario

        sc = _make_full_scenario()
        report = score_scenario(sc)
        assert report.percentage >= 90, f"Full scenario scored {report.percentage}%"
        assert report.grade == "A"

    def test_partial_scenario(self):
        from app.services.scenario_health_service import score_scenario

        sc = _make_scenario(
            story_prompt_tr=" ".join(["kelime"] * 300),
            outfit_girl="a dress with shoes and hat and boots",
        )
        report = score_scenario(sc)
        assert 0 < report.percentage < 100
        assert report.grade in ("C", "D", "F")

    def test_report_structure(self):
        from app.services.scenario_health_service import score_scenario

        sc = _make_scenario()
        report = score_scenario(sc)
        assert report.max_score == 200
        assert 0 <= report.percentage <= 100
        for check in report.checks:
            assert check.status in ("good", "warning", "critical")
            assert 0 <= check.score <= check.max_score

    def test_no_companion_scenario_exempt(self):
        """Scenarios with no_companion in bible should score well without companions."""
        from app.services.scenario_health_service import score_scenario

        sc = _make_scenario(
            story_prompt_tr=" ".join(["kelime"] * 500),
            outfit_girl="a white modest dress with hijab and sandals for pilgrimage",
            outfit_boy="white kurta with taqiyah cap and sandals for pilgrimage",
            scenario_bible={
                "no_companion": True,
                "locations": ["loc1"],
                "consistency_rules": ["rule1"],
            },
            location_constraints="Pages 1-6: sacred sites with wide reverent shots.",
            cover_prompt_template=" ".join(["word"] * 60),
            page_prompt_template=" ".join(["word"] * 60),
        )
        report = score_scenario(sc)
        # Companion, custom_inputs, objects checks should all be "good"
        companion_check = next(c for c in report.checks if c.name == "companions")
        inputs_check = next(c for c in report.checks if c.name == "custom_inputs")
        objects_check = next(c for c in report.checks if c.name == "objects")
        assert companion_check.status == "good"
        assert inputs_check.status == "good"
        assert objects_check.status == "good"


class TestBibleKeysCheck:
    """Tests for the new bible keys check."""

    def test_empty_bible_critical(self):
        from app.services.scenario_health_service import _check_bible_keys

        sc = _make_scenario()
        check = _check_bible_keys(sc)
        assert check.status == "critical"
        assert check.score == 0

    def test_full_bible_good(self):
        from app.services.scenario_health_service import _check_bible_keys

        sc = _make_full_scenario()
        check = _check_bible_keys(sc)
        assert check.status == "good"
        assert check.score == 20

    def test_partial_bible_warning(self):
        from app.services.scenario_health_service import _check_bible_keys

        sc = _make_scenario(
            scenario_bible={"companions": [{"name": "test"}]}
        )
        check = _check_bible_keys(sc)
        assert check.status == "warning"
        assert 0 < check.score < 20


class TestCustomInputsCheck:
    """Tests for the new custom_inputs check."""

    def test_companion_without_inputs_critical(self):
        from app.services.scenario_health_service import _check_custom_inputs

        sc = _make_scenario(
            companions=[
                CompanionAnchor(
                    name_tr="Tilki", name_en="fox", species="fox",
                    appearance="a small red fox with bushy tail and green eyes",
                ),
            ],
        )
        check = _check_custom_inputs(sc)
        assert check.status == "critical"
        assert check.score == 0


class TestTurkishCharsCheck:
    """Tests for Turkish character detection."""

    def test_english_outfit_good(self):
        from app.services.scenario_health_service import _check_turkish_chars

        sc = _make_scenario(
            outfit_girl="a beautiful red dress with golden embroidery",
            outfit_boy="cargo pants and hiking boots",
        )
        check = _check_turkish_chars(sc)
        assert check.status == "good"
        assert check.score == 20


class TestPlaceholderCheck:
    """Tests for placeholder validation."""

    def test_resolvable_placeholders_good(self):
        from app.services.scenario_health_service import _check_placeholders

        sc = _make_scenario(
            story_prompt_tr="Hikaye {child_name} ile {animal_friend} hakkında."
        )
        check = _check_placeholders(sc)
        assert check.status == "good"

    def test_unresolvable_placeholder_critical(self):
        from app.services.scenario_health_service import _check_placeholders

        sc = _make_scenario(
            story_prompt_tr="Hikaye {child_name} ve {guide} ile başlar."
        )
        check = _check_placeholders(sc)
        assert check.status == "critical"
        assert check.score == 0


class TestScenarioContentValidation:
    """Tests for ScenarioContent.__post_init__ validation."""

    def test_turkish_outfit_raises_error(self):
        """Turkish chars in outfit should raise ValueError."""
        with pytest.raises(ValueError, match="Turkish characters"):
            _make_scenario(outfit_girl="güzel bir elbise")

    def test_english_outfit_no_error(self):
        """English outfit should not raise."""
        sc = _make_scenario(outfit_girl="a beautiful red dress")
        assert sc.outfit_girl == "a beautiful red dress"

    def test_short_prompt_warning(self):
        """Short prompt should emit a warning, not error."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _make_scenario(story_prompt_tr=" ".join(["word"] * 100))
            assert len(w) >= 1
            assert "story_prompt_tr" in str(w[0].message)

    def test_good_prompt_no_warning(self):
        """Prompt >= 300 words should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _make_scenario(story_prompt_tr=" ".join(["word"] * 400))
            prompt_warnings = [x for x in w if "story_prompt_tr" in str(x.message)]
            assert len(prompt_warnings) == 0


class TestGetAllScenarioHealth:
    """Integration test — reads from the live registry."""

    def test_returns_reports_for_all_scenarios(self):
        from app.services.scenario_health_service import get_all_scenario_health

        reports = get_all_scenario_health()
        # We know there are 17+ registered scenarios
        assert len(reports) >= 15  # at least most should be present
        for r in reports:
            assert 0 <= r.percentage <= 100

    def test_cappadocia_scores_high(self):
        """Cappadocia is the most mature scenario — should score A or B."""
        from app.services.scenario_health_service import get_all_scenario_health

        reports = get_all_scenario_health()
        cappadocia = next((r for r in reports if r.theme_key == "cappadocia"), None)
        assert cappadocia is not None
        assert cappadocia.percentage >= 75, f"Cappadocia scored {cappadocia.percentage}%"
        assert cappadocia.grade in ("A", "B")
