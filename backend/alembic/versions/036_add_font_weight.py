"""Add font_weight to page_templates.

Revision ID: 036_font_weight
Revises: 035_cover_title_preset
Create Date: 2026-02-12
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "036_font_weight"
down_revision: str | None = "035_cover_title_preset"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "page_templates",
        sa.Column("font_weight", sa.String(20), server_default="normal", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("page_templates", "font_weight")
