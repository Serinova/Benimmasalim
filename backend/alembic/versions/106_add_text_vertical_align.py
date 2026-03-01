"""Add text_vertical_align to page_templates.

Allows admin to control whether text aligns to top, center, or bottom
of the text box area.

Revision ID: 106_text_valign
Revises: 105_cloud_extend
Create Date: 2026-02-28
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "106_text_valign"
down_revision: str = "105_cloud_extend"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "page_templates",
        sa.Column("text_vertical_align", sa.String(20), nullable=False, server_default="bottom"),
    )
    # Mevcut inner sayfaları "bottom" yap (kısa metin aşağı hizalansın)
    op.execute("""
        UPDATE page_templates SET text_vertical_align = 'bottom'
        WHERE page_type = 'inner'
    """)


def downgrade() -> None:
    op.drop_column("page_templates", "text_vertical_align")
