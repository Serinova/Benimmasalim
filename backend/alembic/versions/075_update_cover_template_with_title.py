"""Update COVER_TEMPLATE in prompt_templates to include story_title and remove text ban.

Revision ID: 075_update_cover_template_with_title
Revises: 074_set_cover_title_source_gemini
Create Date: 2026-02-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "075_update_cover_template_with_title"
down_revision: str = "074_set_cover_title_source_gemini"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. TITLE TEXT: Write the book title "{story_title}" in large, decorative, child-friendly storybook typography at the top 25-30% of the image. Use a bold, colorful font that fits the illustration style. The text must be clearly readable and visually integrated into the scene (not a plain label). Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE prompt_templates
        SET content_en = 'A young child wearing {clothing_description}. {scene_description}. CRITICAL COVER LAYOUT: Leave massive empty negative space / clear sky at the top 30% of the image for the book title. Do not draw important elements or the child''s head at the very top. CRITICAL: Do NOT include ANY text, titles, letters, words, or typography anywhere in the image.'
        WHERE key = 'COVER_TEMPLATE'
    """)
