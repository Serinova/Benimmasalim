"""Add text stroke fields to page_templates.

Allows adding outline/border around text for better visibility.

Revision ID: 018_text_stroke
Revises: 017_try_before_buy
Create Date: 2026-02-04

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "018_text_stroke"
down_revision: str = "017_try_before_buy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add text stroke columns to page_templates."""
    op.add_column(
        "page_templates",
        sa.Column("text_stroke_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "page_templates",
        sa.Column("text_stroke_color", sa.String(20), nullable=False, server_default="#000000"),
    )
    op.add_column(
        "page_templates",
        sa.Column("text_stroke_width", sa.Float(), nullable=False, server_default="1.0"),
    )


def downgrade() -> None:
    """Remove text stroke columns."""
    op.drop_column("page_templates", "text_stroke_width")
    op.drop_column("page_templates", "text_stroke_color")
    op.drop_column("page_templates", "text_stroke_enabled")
