"""Add text background gradient fields to page_templates.

Metin arkası gölge/gradient rengini, opaklığını ve açık/kapalı durumunu
admin panelden yönetmeye olanak tanır.

Revision ID: 033_text_bg_gradient
Revises: 032_display_name
Create Date: 2026-02-10

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "033_text_bg_gradient"
down_revision: str = "032_display_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add text background gradient columns to page_templates."""
    op.add_column(
        "page_templates",
        sa.Column("text_bg_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "page_templates",
        sa.Column("text_bg_color", sa.String(20), nullable=False, server_default="#000000"),
    )
    op.add_column(
        "page_templates",
        sa.Column("text_bg_opacity", sa.Integer(), nullable=False, server_default="180"),
    )
    op.add_column(
        "page_templates",
        sa.Column("text_bg_shape", sa.String(30), nullable=False, server_default="soft_vignette"),
    )
    op.add_column(
        "page_templates",
        sa.Column("text_bg_blur", sa.Integer(), nullable=False, server_default="30"),
    )


def downgrade() -> None:
    """Remove text background gradient columns."""
    op.drop_column("page_templates", "text_bg_blur")
    op.drop_column("page_templates", "text_bg_shape")
    op.drop_column("page_templates", "text_bg_opacity")
    op.drop_column("page_templates", "text_bg_color")
    op.drop_column("page_templates", "text_bg_enabled")
