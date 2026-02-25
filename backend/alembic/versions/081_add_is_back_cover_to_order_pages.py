"""Add is_back_cover column to order_pages table.

Revision ID: 081_add_is_back_cover_to_order_pages
Revises: 080_add_cover_spread_fields_to_orders
Create Date: 2026-02-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "081_add_is_back_cover_to_order_pages"
down_revision: str = "080_add_cover_spread_fields_to_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "order_pages",
        sa.Column("is_back_cover", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("order_pages", "is_back_cover")
