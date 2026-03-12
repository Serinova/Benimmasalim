"""Stil çözümleme testleri — her stil doğru konfigürasyona gitmeli."""


from app.prompt.style_config import STYLES, resolve_style


class TestStyleResolution:
    """Stil modifier string'den doğru StyleConfig döndüğünü doğrular."""

    def test_empty_returns_default(self):
        s = resolve_style("")
        assert s.key == "default"

    def test_none_returns_default(self):
        s = resolve_style("")
        assert s.key == "default"

    def test_pixar_keywords(self):
        for kw in ["Pixar 3D CGI", "Disney style", "cizgi film", "cinematic 3d"]:
            s = resolve_style(kw)
            assert s.key == "pixar", f"'{kw}' should resolve to pixar"

    def test_watercolor_keywords(self):
        for kw in ["watercolor painting", "sulu boya", "suluboya", "watercolour"]:
            s = resolve_style(kw)
            assert s.key == "watercolor", f"'{kw}' should resolve to watercolor"

    def test_anime_keywords(self):
        for kw in ["Studio Ghibli", "anime style", "cel-shading"]:
            s = resolve_style(kw)
            assert s.key == "anime", f"'{kw}' should resolve to anime"

    def test_soft_pastel_keywords(self):
        for kw in ["soft pastel", "Yumuşak Pastel", "cosy illustration", "warm pastel"]:
            s = resolve_style(kw)
            assert s.key == "soft_pastel", f"'{kw}' should resolve to soft_pastel"

    def test_adventure_digital_keywords(self):
        for kw in ["adventure digital", "digital painting", "macera", "painterly"]:
            s = resolve_style(kw)
            assert s.key == "adventure_digital", f"'{kw}' should resolve to adventure_digital"

    def test_2d_storybook_returns_default(self):
        s = resolve_style("2D Children's Book illustration")
        assert s.key == "default"

    def test_negation_stripping(self):
        s = resolve_style("NOT watercolor, 2D children's book")
        assert s.key == "default"

    def test_all_styles_have_required_fields(self):
        for key, style in STYLES.items():
            assert style.key == key
            assert style.anchor, f"{key} missing anchor"
            assert style.leading_prefix, f"{key} missing leading_prefix"
            assert style.style_block, f"{key} missing style_block"
            assert style.negative, f"{key} missing negative"
            assert style.inner_prefix, f"{key} missing inner_prefix"
            assert style.inner_suffix, f"{key} missing inner_suffix"
            assert style.cover_prefix, f"{key} missing cover_prefix"
            assert style.cover_suffix, f"{key} missing cover_suffix"


class TestPuLIDConfig:
    """Her stilin PuLID parametrelerini doğrular."""

    def test_pixar_start_step_0(self):
        s = resolve_style("pixar")
        assert s.start_step == 0

    def test_anime_start_step_0(self):
        s = resolve_style("anime")
        assert s.start_step == 0

    def test_watercolor_custom_cfg(self):
        s = resolve_style("watercolor")
        assert s.true_cfg == 1.3

    def test_anime_custom_cfg(self):
        s = resolve_style("anime")
        assert s.true_cfg == 1.1
