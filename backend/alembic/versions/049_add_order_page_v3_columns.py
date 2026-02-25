"""Add V3 columns to order_pages: v3_composed, negative_prompt, pipeline_version.

Used by generate_book to pass skip_compose=True and precomposed_negative when
pages were composed by V3 pipeline.

Revision ID: 049_order_page_v3
Revises: 048_fix_id_weight
Create Date: 2026-02-17

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "049_order_page_v3"
down_revision: str = "048_fix_id_weight"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "order_pages",
        sa.Column("v3_composed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "order_pages",
        sa.Column("negative_prompt", sa.Text(), nullable=True),
    )
    op.add_column(
        "order_pages",
        sa.Column("pipeline_version", sa.String(10), server_default="v2", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("order_pages", "pipeline_version")
    op.drop_column("order_pages", "negative_prompt")
    op.drop_column("order_pages", "v3_composed")
