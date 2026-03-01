"""Invoice: add story_preview_id, make order_id nullable.

Adds support for trial-flow (StoryPreview-based) invoices where there is no
corresponding row in the orders table.

Revision ID: 115_invoice_story_preview_id
Revises: 114_merge_all_heads
Create Date: 2026-03-01
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "115_invoice_story_preview_id"
down_revision: Union[str, None] = "114_merge_all_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Make invoices.order_id nullable (trial invoices have no Order row)
    op.alter_column("invoices", "order_id", nullable=True)

    # 2. Add story_preview_id to invoices
    op.add_column(
        "invoices",
        sa.Column(
            "story_preview_id",
            UUID(as_uuid=True),
            sa.ForeignKey("story_previews.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_invoice_story_preview", "invoices", ["story_preview_id"], unique=True
    )

    # 3. Make invoice_download_tokens.order_id nullable (used only for logging)
    op.alter_column("invoice_download_tokens", "order_id", nullable=True)


def downgrade() -> None:
    op.alter_column("invoice_download_tokens", "order_id", nullable=False)
    op.drop_index("idx_invoice_story_preview", table_name="invoices")
    op.drop_column("invoices", "story_preview_id")
    op.alter_column("invoices", "order_id", nullable=False)
