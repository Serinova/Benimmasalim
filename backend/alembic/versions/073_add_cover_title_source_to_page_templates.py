"""Add cover_title_source column to page_templates.

Revision ID: 073_add_cover_title_source_to_page_templates
Revises: 072_fix_prompt_templates
Create Date: 2026-02-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "073_add_cover_title_source_to_page_templates"
down_revision: str = "072_fix_prompt_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "page_templates",
        sa.Column(
            "cover_title_source",
            sa.String(20),
            nullable=False,
            server_default="overlay",
        ),
    )


def downgrade() -> None:
    op.drop_column("page_templates", "cover_title_source")
