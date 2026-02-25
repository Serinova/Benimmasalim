"""Add cover_title_effect and cover_title_letter_spacing.

Revision ID: 037_cover_effect
Revises: 036_font_weight
Create Date: 2026-02-12
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "037_cover_effect"
down_revision: str | None = "036_font_weight"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "page_templates",
        sa.Column("cover_title_effect", sa.String(30), server_default="gold_shine", nullable=False),
    )
    op.add_column(
        "page_templates",
        sa.Column("cover_title_letter_spacing", sa.Integer, server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("page_templates", "cover_title_letter_spacing")
    op.drop_column("page_templates", "cover_title_effect")
