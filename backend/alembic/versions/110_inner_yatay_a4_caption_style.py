"""Set İç Sayfa YATAY A4 caption-style text overlay (gradient + white text).

Hikaye üzerine metin: altta gradient (siyah %55 → şeffaf), beyaz yazı, gölge.
CSS eşlemesi: caption absolute bottom, padding 18px 22px, color #fff,
text-shadow, .caption::before linear-gradient(to top, rgba(0,0,0,.55), transparent).

Revision ID: 110_inner_yatay_caption
Revises: 109_sync_scenario_page_from_product
Create Date: 2026-03-01

"""
from collections.abc import Sequence

from alembic import op

revision: str = "110_inner_yatay_caption"
down_revision: str = "109_sync_scenario_page_from_product"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # İç Sayfa YATAY A4 / A4 Yatay Ic Sayfa: caption tarzı metin ayarları
    # - Metin altta (position bottom), padding benzeri: text_x 3%, width 94%
    # - Beyaz yazı (#fff), hafif gölge için stroke
    # - Arka plan: altta koyu gradient (linear-gradient to top, black .55 → 0), blur 0
    op.execute("""
        UPDATE page_templates
        SET
            text_position = 'bottom',
            text_vertical_align = 'bottom',
            text_x_percent = 3.0,
            text_width_percent = 94.0,
            text_y_percent = 72.0,
            text_height_percent = 25.0,
            font_color = '#FFFFFF',
            text_stroke_enabled = true,
            text_stroke_color = '#000000',
            text_stroke_width = 1.2,
            text_bg_enabled = true,
            text_bg_color = '#000000',
            text_bg_opacity = 140,
            text_bg_shape = 'soft_vignette',
            text_bg_blur = 0,
            text_bg_extend_top = 80,
            text_bg_extend_bottom = 20,
            text_bg_extend_sides = 5,
            text_bg_intensity = 100
        WHERE page_type = 'inner'
          AND (name ILIKE '%YATAY A4%' OR name ILIKE '%Yatay%' OR name ILIKE '%yatay%')
    """)


def downgrade() -> None:
    # Varsayılan beyaz bulut stiline geri al
    op.execute("""
        UPDATE page_templates
        SET
            text_x_percent = 5.0,
            text_width_percent = 90.0,
            text_y_percent = 72.0,
            text_height_percent = 25.0,
            font_color = '#2D2D2D',
            text_stroke_enabled = false,
            text_stroke_color = '#FFFFFF',
            text_stroke_width = 1.0,
            text_bg_enabled = true,
            text_bg_color = '#FFFFFF',
            text_bg_opacity = 230,
            text_bg_shape = 'cloud',
            text_bg_blur = 50,
            text_bg_extend_top = 60,
            text_bg_extend_bottom = 15,
            text_bg_extend_sides = 10,
            text_bg_intensity = 100
        WHERE page_type = 'inner'
          AND (name ILIKE '%YATAY A4%' OR name ILIKE '%Yatay%' OR name ILIKE '%yatay%')
    """)
