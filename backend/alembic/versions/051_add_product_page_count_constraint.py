"""Add check_page_count_range constraint to products table.

Before adding the constraint, fix any existing rows that violate it
(default_page_count < 4 or > 64 or NULL) by setting them to 16.

Revision ID: 051_product_page_count_constraint
Revises: 050_force_order_page_pipeline_v3
Create Date: 2026-02-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "051_product_page_count_constraint"
down_revision: str = "050_force_order_page_pipeline_v3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SAFE_DEFAULT = 16


def upgrade() -> None:
    # Step 1: Fix any existing rows that would violate the new constraint
    op.execute(
        sa.text(
            f"""
            UPDATE products
            SET default_page_count = {SAFE_DEFAULT}
            WHERE default_page_count IS NULL
               OR default_page_count < 4
               OR default_page_count > 64
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            UPDATE products
            SET min_page_count = 4
            WHERE min_page_count IS NULL
               OR min_page_count < 4
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            UPDATE products
            SET max_page_count = 64
            WHERE max_page_count IS NULL
               OR max_page_count > 64
               OR max_page_count < 4
            """
        )
    )

    # Step 2: Add the CHECK constraint
    op.create_check_constraint(
        "check_page_count_range",
        "products",
        "default_page_count >= 4 AND default_page_count <= 64",
    )


def downgrade() -> None:
    op.drop_constraint("check_page_count_range", "products", type_="check")
