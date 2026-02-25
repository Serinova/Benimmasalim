"""Add back_cover_image_url and cover_spread_image_url to orders table.

Revision ID: 080_add_cover_spread_fields_to_orders
Revises: 079_cover_title_centered_glow
Create Date: 2026-02-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "080_add_cover_spread_fields_to_orders"
down_revision: str = "079_cover_title_centered_glow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("back_cover_image_url", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("cover_spread_image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "cover_spread_image_url")
    op.drop_column("orders", "back_cover_image_url")
