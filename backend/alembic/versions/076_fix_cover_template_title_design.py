"""Fix COVER_TEMPLATE: better title design instructions, exact text copy, top 12-15% placement.

Revision ID: 076_fix_cover_template_title_design
Revises: 075_update_cover_template_with_title
Create Date: 2026-02-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "076_fix_cover_template_title_design"
down_revision: str = "075_update_cover_template_with_title"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. BOOK TITLE: Render the exact text "{story_title}" as large decorative storybook lettering in the top 12-15% of the image (sky/clear area only). Bold outlined letters, dark stroke for readability, warm golden or white fill, slight arc. Title must NOT overlap the child. Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)


def downgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. TITLE TEXT: Write the book title "{story_title}" in large, decorative, child-friendly storybook typography at the top 25-30% of the image. Use a bold, colorful font that fits the illustration style. The text must be clearly readable and visually integrated into the scene (not a plain label). Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)
