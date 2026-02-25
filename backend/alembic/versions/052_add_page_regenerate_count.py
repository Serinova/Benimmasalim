"""Add page_regenerate_count to story_previews.

Tracks how many times the customer has regenerated page images
on the confirmation page (max 3 allowed).

Revision ID: 052_page_regenerate_count
Revises: 051_product_page_count_constraint
Create Date: 2026-02-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "052_page_regenerate_count"
down_revision: str = "051_product_page_count_constraint"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("page_regenerate_count", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "page_regenerate_count")
