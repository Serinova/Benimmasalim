"""Add display_name to visual_styles.

Kullanıcıya gösterilecek isim; boşsa name kullanılır. İsim değişince dahili eşleme bozulmaz.

Revision ID: 032_display_name
Revises: 031_visual_style_overrides
Create Date: 2026-02-09

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "032_display_name"
down_revision: str = "028_soft_pastel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "visual_styles",
        sa.Column("display_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("visual_styles", "display_name")
