"""Set cover_title_source to 'overlay' for all page templates.

AI model now bans all text from images. Title must be rendered by PIL overlay.

Revision ID: 130_set_cover_title_source_overlay
Revises: 129_add_character_description_to_story_previews
Create Date: 2026-03-06
"""

from collections.abc import Sequence

from alembic import op

revision: str = "130_set_cover_title_source_overlay"
down_revision: str = "129_char_desc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Tüm template'leri overlay moduna geçir — PIL WordArt başlık render etsin
    op.execute("""
        UPDATE page_templates
        SET cover_title_source = 'overlay'
        WHERE cover_title_source = 'gemini'
           OR cover_title_source IS NULL
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE page_templates
        SET cover_title_source = 'gemini'
        WHERE cover_title_source = 'overlay'
    """)
