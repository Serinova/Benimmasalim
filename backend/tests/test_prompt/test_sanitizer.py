"""Sanitizer testleri."""


from app.prompt.sanitizer import normalize_clothing, normalize_location, sanitize, truncate_safe


class TestNormalizeClothing:
    def test_turkish_to_english(self):
        result = normalize_clothing("kırmızı tişört ve mavi pantolon")
        assert "red" in result
        assert "t-shirt" in result
        assert "blue" in result
        assert "pants" in result

    def test_empty_string(self):
        assert normalize_clothing("") == ""

    def test_already_english(self):
        result = normalize_clothing("red t-shirt and blue jeans")
        assert result == "red t-shirt and blue jeans"


class TestNormalizeLocation:
    def test_kapadokya_to_cappadocia(self):
        result = normalize_location("Child standing in Kapadokya")
        assert "Cappadocia" in result
        assert "Kapadokya" not in result

    def test_already_english(self):
        result = normalize_location("Child in Cappadocia")
        assert "Cappadocia" in result


class TestTruncateSafe:
    def test_short_text_unchanged(self):
        text = "Hello world"
        assert truncate_safe(text, 100) == text

    def test_long_text_truncated(self):
        text = "A " * 500
        result = truncate_safe(text, 100)
        assert len(result) <= 100

    def test_2d_not_split(self):
        text = "A beautiful 2D " + "x" * 200
        result = truncate_safe(text, 20)
        assert not result.endswith("2")


class TestSanitize:
    def test_strips_cinematic(self):
        result = sanitize("A cinematic scene of a child")
        assert "cinematic" not in result.lower()

    def test_strips_bokeh(self):
        result = sanitize("Beautiful bokeh background")
        assert "bokeh" not in result.lower()

    def test_cover_keeps_cover_terms(self):
        result = sanitize("Children's book cover illustration", is_cover=True)
        assert "book cover" in result.lower()

    def test_inner_strips_cover_terms(self):
        result = sanitize("Children's book cover illustration", is_cover=False)
        assert "book cover" not in result.lower()
