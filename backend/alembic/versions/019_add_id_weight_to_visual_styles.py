"""Add id_weight to visual_styles.

PuLID id_weight: face consistency vs style strength (0.15-0.70).

Revision ID: 019_id_weight
Revises: 018_text_stroke
Create Date: 2026-02-05

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "019_id_weight"
down_revision: str = "018_text_stroke"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "visual_styles",
        sa.Column("id_weight", sa.Float(), nullable=False, server_default="0.35"),
    )


def downgrade() -> None:
    op.drop_column("visual_styles", "id_weight")
