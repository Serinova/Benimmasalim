"""Add marketing fields to scenarios table.

Revision ID: 085_add_scenario_marketing_fields
Revises: 084_cover_title_elegant_integrated
Create Date: 2026-02-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "085_add_scenario_marketing_fields"
down_revision: str = "084_cover_title_elegant_integrated"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("scenarios", sa.Column("marketing_video_url", sa.Text(), nullable=True))
    op.add_column(
        "scenarios",
        sa.Column("marketing_gallery", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "scenarios", sa.Column("marketing_price_label", sa.String(100), nullable=True)
    )
    op.add_column(
        "scenarios",
        sa.Column("marketing_features", postgresql.JSONB(), nullable=True),
    )
    op.add_column("scenarios", sa.Column("marketing_badge", sa.String(100), nullable=True))
    op.add_column("scenarios", sa.Column("age_range", sa.String(50), nullable=True))
    op.add_column("scenarios", sa.Column("estimated_duration", sa.String(50), nullable=True))
    op.add_column("scenarios", sa.Column("tagline", sa.String(255), nullable=True))
    op.add_column("scenarios", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column(
        "scenarios",
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("scenarios", "review_count")
    op.drop_column("scenarios", "rating")
    op.drop_column("scenarios", "tagline")
    op.drop_column("scenarios", "estimated_duration")
    op.drop_column("scenarios", "age_range")
    op.drop_column("scenarios", "marketing_badge")
    op.drop_column("scenarios", "marketing_features")
    op.drop_column("scenarios", "marketing_price_label")
    op.drop_column("scenarios", "marketing_gallery")
    op.drop_column("scenarios", "marketing_video_url")
