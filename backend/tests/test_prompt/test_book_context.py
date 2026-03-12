"""BookContext oluşturma testleri."""


from app.prompt.book_context import BookContext


class TestBookContext:
    def test_build_default(self):
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
        )
        assert ctx.child_name == "Enes"
        assert ctx.child_age == 7
        assert ctx.style.key == "default"
        assert ctx.page_count == 16

    def test_build_with_style(self):
        ctx = BookContext.build(
            child_name="Ela",
            child_age=5,
            child_gender="kız",
            style_modifier="watercolor painting",
        )
        assert ctx.style.key == "watercolor"
        assert ctx.style.true_cfg == 1.3

    def test_build_with_id_weight_override(self):
        ctx = BookContext.build(
            child_name="Ali",
            child_age=6,
            child_gender="erkek",
            style_modifier="pixar",
            id_weight_override=0.8,
        )
        assert ctx.style.id_weight == 0.8
        assert ctx.style.key == "pixar"

    def test_build_with_location(self):
        ctx = BookContext.build(
            child_name="Zeynep",
            child_age=4,
            child_gender="kız",
            location_name="Cappadocia",
            location_elements=["fairy chimneys", "hot air balloons"],
        )
        assert ctx.location_name == "Cappadocia"
        assert len(ctx.location_elements) == 2
