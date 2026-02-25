"""Force order_pages.pipeline_version default and data to v3.

Revision ID: 050_force_order_page_pipeline_v3
Revises: 049_order_page_v3
Create Date: 2026-02-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "050_force_order_page_pipeline_v3"
down_revision: str = "049_order_page_v3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE order_pages
            SET pipeline_version = 'v3'
            WHERE pipeline_version IS NULL OR lower(pipeline_version) != 'v3'
            """
        )
    )
    op.alter_column(
        "order_pages",
        "pipeline_version",
        existing_type=sa.String(length=10),
        server_default="v3",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "order_pages",
        "pipeline_version",
        existing_type=sa.String(length=10),
        server_default="v2",
        existing_nullable=False,
    )
