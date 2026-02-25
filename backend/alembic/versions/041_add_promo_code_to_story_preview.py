"""Add promo code tracking fields to story_previews table.

Stores which promo code was used for each order so we can track
usage and display discount info in admin panel.

Revision ID: 041_promo_story_preview
Revises: 040_fix_style_prompts
Create Date: 2026-02-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "041_promo_story_preview"
down_revision: str = "039_dedication_page"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("promo_code_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("promo_code_text", sa.String(50), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("promo_discount_type", sa.String(20), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("promo_discount_value", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("discount_applied_amount", sa.Numeric(10, 2), nullable=True),
    )
    op.create_foreign_key(
        "fk_story_previews_promo_code_id",
        "story_previews",
        "promo_codes",
        ["promo_code_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_story_previews_promo_code_id", "story_previews", type_="foreignkey")
    op.drop_column("story_previews", "discount_applied_amount")
    op.drop_column("story_previews", "promo_discount_value")
    op.drop_column("story_previews", "promo_discount_type")
    op.drop_column("story_previews", "promo_code_text")
    op.drop_column("story_previews", "promo_code_id")
