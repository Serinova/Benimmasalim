"""Update inner page templates to white cloud text background.

Switches text overlay from dark gradient (black, soft_vignette) to
white cloud for better readability on varied image backgrounds.

Revision ID: 104_white_cloud_bg
Revises: 103_add_billing_data_to_story_previews
Create Date: 2026-02-28

"""
from collections.abc import Sequence

from alembic import op

revision: str = "104_white_cloud_bg"
down_revision: str = "103_add_billing_data_to_story_previews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update existing inner page templates to white cloud text background."""
    op.execute("""
        UPDATE page_templates
        SET text_bg_color = '#FFFFFF',
            text_bg_opacity = 230,
            text_bg_shape = 'cloud',
            text_bg_blur = 50,
            font_color = '#2D2D2D',
            text_stroke_enabled = false,
            text_stroke_color = '#FFFFFF',
            text_stroke_width = 1.0
        WHERE page_type = 'inner'
    """)


def downgrade() -> None:
    """Revert to dark gradient text background."""
    op.execute("""
        UPDATE page_templates
        SET text_bg_color = '#000000',
            text_bg_opacity = 180,
            text_bg_shape = 'soft_vignette',
            text_bg_blur = 30,
            font_color = '#333333',
            text_stroke_enabled = true,
            text_stroke_color = '#000000',
            text_stroke_width = 2.0
        WHERE page_type = 'inner'
    """)
