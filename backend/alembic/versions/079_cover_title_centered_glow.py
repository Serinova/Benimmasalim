"""Update COVER_TEMPLATE: centered title, golden glow, no overlap with child.

Revision ID: 079_cover_title_centered_glow
Revises: 078_cover_title_gold_star_design
Create Date: 2026-02-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "079_cover_title_centered_glow"
down_revision: str = "078_cover_title_gold_star_design"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. BOOK TITLE DESIGN: Render the EXACT text [{story_title}] letter by letter, HORIZONTALLY CENTERED, split into 2 centered lines if long, placed entirely in the top 14% of the image (open sky area). Style: large 3D embossed letters, warm amber-to-gold gradient fill, sharp specular highlight on each letter, thick dark-brown beveled outline, soft golden glow behind title block, warm drop-shadow. Scatter 6-10 small golden stars around the title. Title must NEVER touch or overlap the child''s head or body. Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)


def downgrade() -> None:
    op.execute(r"""
        UPDATE prompt_templates
        SET content_en = 'A young {child_gender} with {hair_description}, wearing {clothing_description}. {scene_description}. BOOK TITLE DESIGN: Render the EXACT text "{story_title}" centered in the top 10-14% of the image (open sky area). Style: large 3D embossed letters with warm amber-to-gold gradient fill, bright specular highlight streak on each letter, thick dark-brown beveled outline, soft warm drop-shadow for floating 3D effect. Scatter 6-10 small golden five-pointed stars of varying sizes around the title. Title must NOT overlap the child. Do NOT add any other text, watermarks, or signatures.'
        WHERE key = 'COVER_TEMPLATE'
    """)
