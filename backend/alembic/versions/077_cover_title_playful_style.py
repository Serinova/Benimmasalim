"""Update COVER_TEMPLATE: playful bouncy multicolor bubble letter style for title.

Revision ID: 077_cover_title_playful_style
Revises: 076_fix_cover_template_title_design
Create Date: 2026-02-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "077_cover_title_playful_style"
down_revision: str = "076_fix_cover_template_title_design"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. BOOK TITLE: Render the EXACT text "{story_title}" in the top 12-15% of the image (sky/open area). Style: fun playful children''s book lettering — wobbly/bouncy letters, bright multicolor fills (red/yellow/blue/green per letter), thick white outline + dark drop shadow, puffy 3D bubble letter look. Title must NOT overlap the child. Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)


def downgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. BOOK TITLE: Render the exact text "{story_title}" as large decorative storybook lettering in the top 12-15% of the image (sky/clear area only). Bold outlined letters, dark stroke for readability, warm golden or white fill, slight arc. Title must NOT overlap the child. Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)
