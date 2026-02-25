"""Add lead_user_id to story_previews for Concierge Support.

This is critical for the business model - we capture contact info
at the BEGINNING of the flow so we can call users if they drop off
or if AI generation fails.

Revision ID: 016_lead_user_id
Revises: add_cultural_elements
Create Date: 2026-02-04

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "016_lead_user_id"
down_revision: str = "add_cultural_elements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add lead_user_id column to story_previews table."""
    op.add_column(
        "story_previews",
        sa.Column("lead_user_id", UUID(as_uuid=True), nullable=True),
    )
    # Add index for faster lookups
    op.create_index(
        "ix_story_previews_lead_user_id",
        "story_previews",
        ["lead_user_id"],
    )


def downgrade() -> None:
    """Remove lead_user_id column from story_previews table."""
    op.drop_index("ix_story_previews_lead_user_id", table_name="story_previews")
    op.drop_column("story_previews", "lead_user_id")
