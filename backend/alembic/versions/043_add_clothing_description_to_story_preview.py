"""Add clothing_description column to story_previews.

Stores the child's outfit description so remaining-pages generation
can reuse it consistently without fragile regex extraction.

Revision ID: 043_clothing_description
Revises: 042_generation_progress
Create Date: 2026-02-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "043_clothing_description"
down_revision: str = "042_generation_progress"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("clothing_description", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "clothing_description")
