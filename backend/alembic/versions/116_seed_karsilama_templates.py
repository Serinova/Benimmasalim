"""Seed: dedication PageTemplate + default_intro_text AppSetting.

Revision ID: 116_seed_karsilama_templates
Revises: 115_invoice_story_preview_id
"""

from __future__ import annotations

import uuid
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "116_seed_karsilama_templates"
down_revision: Union[str, None] = "115_invoice_story_preview_id"
branch_labels = None
depends_on = None

_DEDICATION_TEXT = (
    "Sevgili {child_name}, bu kitap senin için özel olarak hazırlandı.\n\n"
    "Her sayfasında merakın, gülüşün ve hayallerin var.\n\n"
    "Okudukça yeni dünyalar keşfetmen ve her satırda kendini "
    "biraz daha güçlü hissetmen dileğiyle…"
)

_DEFAULT_INTRO_TEXT = (
    "{story_title} macerasına hoş geldin, sevgili {child_name}!\n\n"
    "Bu özel yolculukta seni harika sürprizler bekliyor. "
    "Her sayfayı çevirirken gözlerin parlasın, hayal gücün kanatlanasın!"
)


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Upsert dedication PageTemplate
    existing = conn.execute(
        sa.text("SELECT id FROM page_templates WHERE page_type = 'dedication' LIMIT 1")
    ).fetchone()

    now = sa.func.now()
    if existing:
        conn.execute(
            sa.text(
                "UPDATE page_templates SET "
                "  dedication_default_text = :txt, "
                "  name = :name, "
                "  updated_at = NOW() "
                "WHERE id = :id"
            ),
            {"txt": _DEDICATION_TEXT, "name": "Varsayılan Karşılama", "id": str(existing[0])},
        )
    else:
        conn.execute(
            sa.text(
                "INSERT INTO page_templates "
                "(id, name, page_type, page_width_mm, page_height_mm, bleed_mm, "
                " image_width_percent, image_height_percent, image_x_percent, image_y_percent, "
                " image_aspect_ratio, text_enabled, "
                " text_width_percent, text_height_percent, text_x_percent, text_y_percent, "
                " text_position, text_vertical_align, font_family, font_size_pt, font_color, "
                " font_weight, text_align, line_height, background_color, "
                " text_stroke_enabled, text_stroke_color, text_stroke_width, "
                " text_bg_enabled, text_bg_color, text_bg_opacity, text_bg_shape, text_bg_blur, "
                " text_bg_extend_top, text_bg_extend_bottom, text_bg_extend_sides, text_bg_intensity, "
                " cover_title_source, cover_title_enabled, cover_title_font_family, "
                " cover_title_font_size_pt, cover_title_font_color, cover_title_arc_intensity, "
                " cover_title_shadow_enabled, cover_title_shadow_color, cover_title_shadow_offset, "
                " cover_title_stroke_width, cover_title_stroke_color, cover_title_y_percent, "
                " cover_title_preset, cover_title_effect, cover_title_letter_spacing, "
                " margin_top_mm, margin_bottom_mm, margin_left_mm, margin_right_mm, "
                " is_active, dedication_default_text, created_at, updated_at) "
                "VALUES "
                "(:id, :name, 'dedication', 297, 210, 3, "
                " 0, 0, 0, 0, "
                " '16:9', true, "
                " 80, 70, 10, 15, "
                " 'overlay', 'center', 'Nunito', 18, '#2D2D2D', "
                " 'normal', 'center', 1.7, '#FDF6EC', "
                " false, '#FFFFFF', 1, "
                " false, '#FFFFFF', 200, 'rectangle', 0, "
                " 0, 0, 0, 100, "
                " 'gemini', false, 'Lobster', "
                " 48, '#FFD700', 0, "
                " false, '#000000', 0, "
                " 0, '#8B6914', 5, "
                " 'premium', 'none', 0, "
                " 10, 10, 10, 10, "
                " true, :txt, NOW(), NOW())"
            ),
            {"id": str(uuid.uuid4()), "name": "Varsayılan Karşılama", "txt": _DEDICATION_TEXT},
        )

    # 2) Upsert default_intro_text AppSetting
    existing_setting = conn.execute(
        sa.text("SELECT key FROM app_settings WHERE key = 'default_intro_text' LIMIT 1")
    ).fetchone()

    if existing_setting:
        conn.execute(
            sa.text("UPDATE app_settings SET value = :val, updated_at = NOW() WHERE key = 'default_intro_text'"),
            {"val": _DEFAULT_INTRO_TEXT},
        )
    else:
        conn.execute(
            sa.text("INSERT INTO app_settings (key, value, updated_at) VALUES ('default_intro_text', :val, NOW())"),
            {"val": _DEFAULT_INTRO_TEXT},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM page_templates WHERE page_type = 'dedication'"))
    conn.execute(sa.text("DELETE FROM app_settings WHERE key = 'default_intro_text'"))
