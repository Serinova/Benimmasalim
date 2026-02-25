"""Add cover_title_preset to page_templates.

3 preset: minimal (stroke only), classic (stroke+shadow), premium (stroke+shadow+banner)

Revision ID: 035_cover_title_preset
Revises: 034_cover_title
Create Date: 2026-02-12

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "035_cover_title_preset"
down_revision: str | None = "034_cover_title"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "page_templates",
        sa.Column("cover_title_preset", sa.String(20), server_default="premium", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("page_templates", "cover_title_preset")
