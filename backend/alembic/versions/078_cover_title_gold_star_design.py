"""Update COVER_TEMPLATE: artistic gold embossed 3D letters with star embellishments.

Revision ID: 078_cover_title_gold_star_design
Revises: 077_cover_title_playful_style
Create Date: 2026-02-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "078_cover_title_gold_star_design"
down_revision: str = "077_cover_title_playful_style"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. BOOK TITLE DESIGN: Render the EXACT text "{story_title}" centered in the top 10-14% of the image (open sky area). Style: large 3D embossed letters with warm amber-to-gold gradient fill, bright specular highlight streak on each letter, thick dark-brown beveled outline, soft warm drop-shadow for floating 3D effect. Scatter 6-10 small golden five-pointed stars of varying sizes around the title. Title must NOT overlap the child. Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)


def downgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. BOOK TITLE: Render the EXACT text "{story_title}" in the top 12-15% of the image (sky/open area). Style: fun playful children''s book lettering — wobbly/bouncy letters, bright multicolor fills (red/yellow/blue/green per letter), thick white outline + dark drop shadow, puffy 3D bubble letter look. Title must NOT overlap the child. Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)
