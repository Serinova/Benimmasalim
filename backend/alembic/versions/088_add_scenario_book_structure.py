"""Add book structure fields to scenarios for marketing display.

Revision ID: 088_add_scenario_book_structure
Revises: 087_add_scenario_product_link
Create Date: 2026-02-25

Adds:
- story_page_count: AI-generated story pages (e.g. 22)
- cover_count: front + back covers (default 2)
- greeting_page_count: karşılama pages (default 2)
- back_info_page_count: back info page (default 1)

total_page_count is a computed property (not stored).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "088_add_scenario_book_structure"
down_revision: str | None = "087_add_scenario_product_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column("story_page_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("cover_count", sa.Integer(), nullable=True, server_default="2"),
    )
    op.add_column(
        "scenarios",
        sa.Column("greeting_page_count", sa.Integer(), nullable=True, server_default="2"),
    )
    op.add_column(
        "scenarios",
        sa.Column("back_info_page_count", sa.Integer(), nullable=True, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("scenarios", "story_page_count")
    op.drop_column("scenarios", "cover_count")
    op.drop_column("scenarios", "greeting_page_count")
    op.drop_column("scenarios", "back_info_page_count")
