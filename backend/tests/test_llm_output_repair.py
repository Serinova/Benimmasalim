"""Tests for LLM output repair utilities."""

import json
import unittest

from app.services.ai.llm_output_repair import (
    extract_and_repair_json,
    repair_blueprint,
    repair_pages,
)

# =============================================================================
# JSON extraction + repair
# =============================================================================


class TestExtractAndRepairJson(unittest.TestCase):

    def test_clean_json_object(self):
        raw = '{"title": "Test", "pages": []}'
        result = extract_and_repair_json(raw)
        self.assertEqual(result["title"], "Test")

    def test_clean_json_array(self):
        raw = '[{"page": 1}]'
        result = extract_and_repair_json(raw)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_markdown_code_block(self):
        raw = 'Some text\n```json\n{"key": "val"}\n```\nMore text'
        result = extract_and_repair_json(raw)
        self.assertEqual(result["key"], "val")

    def test_trailing_comma_repair(self):
        raw = '{"a": 1, "b": 2,}'
        result = extract_and_repair_json(raw)
        self.assertEqual(result["a"], 1)

    def test_unquoted_keys(self):
        raw = '{title: "hello", count: 5}'
        result = extract_and_repair_json(raw)
        self.assertEqual(result["title"], "hello")

    def test_truncated_json_auto_close(self):
        raw = '{"title": "test", "pages": [{"page": 1}'
        result = extract_and_repair_json(raw)
        self.assertEqual(result["title"], "test")

    def test_js_comments_removed(self):
        raw = '{"a": 1 /* comment */, "b": 2 // inline\n}'
        result = extract_and_repair_json(raw)
        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"], 2)

    def test_no_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            extract_and_repair_json("no json here at all")

    def test_preamble_text_before_json(self):
        raw = "Here is the blueprint:\n\n{\"title\": \"Adventure\"}"
        result = extract_and_repair_json(raw)
        self.assertEqual(result["title"], "Adventure")


# =============================================================================
# Blueprint repair
# =============================================================================


class TestRepairBlueprint(unittest.TestCase):

    def _make_minimal_blueprint(self, page_count: int) -> dict:
        return {
            "title": "Test",
            "page_count": page_count,
            "pages": [
                {"page": i + 1, "role": "adventure", "scene_goal": f"Goal {i+1}"}
                for i in range(page_count)
            ],
        }

    def test_correct_blueprint_no_repairs(self):
        bp = self._make_minimal_blueprint(10)
        bp["story_arc"] = {
            "setup": "s",
            "confrontation": "c",
            "resolution": "r",
        }
        for p in bp["pages"]:
            p["act"] = "2"
            p["emotional_state"] = "meraklı"
        repaired, repairs = repair_blueprint(bp, 10)
        self.assertEqual(len(repaired["pages"]), 10)
        # Only repairs for missing optional fields (no story_arc, act, emotional_state repairs)
        arc_repairs = [r for r in repairs if "story_arc" in r]
        self.assertEqual(len(arc_repairs), 0)

    def test_missing_story_arc_added(self):
        bp = self._make_minimal_blueprint(6)
        repaired, repairs = repair_blueprint(bp, 6)
        self.assertIn("story_arc", repaired)
        self.assertTrue(any("story_arc" in r for r in repairs))

    def test_missing_pages_padded(self):
        bp = self._make_minimal_blueprint(5)
        repaired, repairs = repair_blueprint(bp, 10)
        self.assertEqual(len(repaired["pages"]), 10)
        self.assertTrue(any("eksik sayfa" in r for r in repairs))

    def test_excess_pages_trimmed(self):
        bp = self._make_minimal_blueprint(15)
        repaired, repairs = repair_blueprint(bp, 10)
        self.assertEqual(len(repaired["pages"]), 10)
        self.assertTrue(any("kırpıldı" in r for r in repairs))

    def test_missing_act_inferred(self):
        bp = self._make_minimal_blueprint(6)
        repaired, repairs = repair_blueprint(bp, 6)
        for page in repaired["pages"]:
            self.assertIn(page["act"], ("1", "2", "3"))

    def test_missing_emotional_state_filled(self):
        bp = self._make_minimal_blueprint(6)
        repaired, repairs = repair_blueprint(bp, 6)
        for page in repaired["pages"]:
            self.assertTrue(len(page["emotional_state"]) > 0)

    def test_page_numbers_sequential(self):
        bp = self._make_minimal_blueprint(3)
        bp["pages"][0]["page"] = 99
        repaired, _ = repair_blueprint(bp, 3)
        nums = [p["page"] for p in repaired["pages"]]
        self.assertEqual(nums, [1, 2, 3])


# =============================================================================
# Pages (PASS-1) repair
# =============================================================================


class TestRepairPages(unittest.TestCase):

    def _make_blueprint(self, count: int) -> dict:
        return {
            "pages": [
                {
                    "page": i + 1,
                    "role": "adventure",
                    "scene_goal": f"Scene goal {i+1}",
                    "visual_brief_tr": f"Visual brief {i+1}",
                    "emotional_state": "meraklı",
                }
                for i in range(count)
            ]
        }

    def test_correct_pages_no_repairs(self):
        bp = self._make_blueprint(5)
        pages = [
            {
                "page": i + 1,
                "text_tr": f"Hikaye metni sayfa {i+1}. Çocuk maceraya atıldı.",
                "image_prompt_en": f"A child exploring scene {i+1}. Warm sunlight. The child looks curious.",
                "negative_prompt_en": "text, watermark",
            }
            for i in range(5)
        ]
        repaired, repairs = repair_pages(pages, bp, 5)
        self.assertEqual(len(repaired), 5)
        # No placeholder repairs needed (all fields present and long enough)
        placeholder_repairs = [r for r in repairs if "placeholder" in r]
        self.assertEqual(len(placeholder_repairs), 0)

    def test_missing_pages_padded_from_blueprint(self):
        bp = self._make_blueprint(10)
        pages = [
            {
                "page": i + 1,
                "text_tr": f"Metin {i+1} burada bir hikaye var.",
                "image_prompt_en": f"A child in scene {i+1}. Warm lighting. Curious expression.",
                "negative_prompt_en": "text, watermark",
            }
            for i in range(7)
        ]
        repaired, repairs = repair_pages(pages, bp, 10)
        self.assertEqual(len(repaired), 10)
        self.assertTrue(any("eksik sayfa" in r for r in repairs))
        # Padded pages should have content from blueprint
        self.assertIn("Scene goal 8", repaired[7]["text_tr"])

    def test_empty_text_tr_filled(self):
        bp = self._make_blueprint(3)
        pages = [
            {"page": 1, "text_tr": "", "image_prompt_en": "A long enough image prompt for testing.", "negative_prompt_en": "text"},
            {"page": 2, "text_tr": "Normal metin burada bir hikaye anlatılıyor.", "image_prompt_en": "scene two prompt with enough length.", "negative_prompt_en": "text"},
            {"page": 3, "text_tr": "   ", "image_prompt_en": "scene three prompt with enough detail here.", "negative_prompt_en": "text"},
        ]
        repaired, repairs = repair_pages(pages, bp, 3)
        self.assertTrue(len(repaired[0]["text_tr"]) > 0)
        self.assertTrue(len(repaired[2]["text_tr"]) > 0)
        self.assertTrue(any("s1: text_tr" in r for r in repairs))

    def test_empty_image_prompt_filled(self):
        bp = self._make_blueprint(2)
        pages = [
            {"page": 1, "text_tr": "Uzun bir metin burada var yeterli.", "image_prompt_en": "", "negative_prompt_en": "text"},
            {"page": 2, "text_tr": "Bir diğer uzun metin burada yeterli.", "image_prompt_en": "Good prompt with enough detail.", "negative_prompt_en": "text"},
        ]
        repaired, repairs = repair_pages(pages, bp, 2)
        self.assertTrue(len(repaired[0]["image_prompt_en"]) > 10)
        self.assertTrue(any("s1: image_prompt_en" in r for r in repairs))

    def test_excess_pages_trimmed(self):
        bp = self._make_blueprint(5)
        pages = [
            {
                "page": i + 1,
                "text_tr": f"Text {i+1} yeterli uzunlukta olmalı.",
                "image_prompt_en": f"Image prompt {i+1} long enough for test.",
                "negative_prompt_en": "neg",
            }
            for i in range(8)
        ]
        repaired, repairs = repair_pages(pages, bp, 5)
        self.assertEqual(len(repaired), 5)


# =============================================================================
# AIServiceError structured fields
# =============================================================================


class TestAIServiceErrorFields(unittest.TestCase):

    def test_reason_code_and_trace_id(self):
        from app.core.exceptions import AIServiceError

        exc = AIServiceError(
            "Gemini",
            "Test error",
            reason_code="BLUEPRINT_PARSE_FAIL",
            trace_id="abc123",
        )
        self.assertEqual(exc.reason_code, "BLUEPRINT_PARSE_FAIL")
        self.assertEqual(exc.trace_id, "abc123")
        self.assertIn("BLUEPRINT_PARSE_FAIL", exc.detail)
        self.assertIn("abc123", exc.detail)

    def test_auto_generated_trace_id(self):
        from app.core.exceptions import AIServiceError

        exc = AIServiceError("Gemini", "Test")
        self.assertTrue(len(exc.trace_id) == 12)

    def test_default_reason_code(self):
        from app.core.exceptions import AIServiceError

        exc = AIServiceError("Gemini")
        self.assertEqual(exc.reason_code, "AI_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
