"""Add Try Before You Buy fields to story_previews.

Implements staged generation:
- Phase 1: Generate full story + 3 preview images
- Phase 2: After payment, generate remaining 13 images

Revision ID: 017_try_before_buy
Revises: 016_lead_user_id
Create Date: 2026-02-04

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "017_try_before_buy"
down_revision: str = "016_lead_user_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Try Before You Buy columns."""
    # Preview mode flag
    op.add_column(
        "story_previews",
        sa.Column("is_preview_mode", sa.Boolean(), nullable=True, server_default="true"),
    )
    
    # CRITICAL: Cache of all generated prompts from Gemini
    op.add_column(
        "story_previews",
        sa.Column("generated_prompts_cache", JSONB(), nullable=True),
    )
    
    # Preview images (first 3)
    op.add_column(
        "story_previews",
        sa.Column("preview_images", JSONB(), nullable=True),
    )
    
    # Abandonment tracking
    op.add_column(
        "story_previews",
        sa.Column("preview_shown_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("abandoned_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Admin follow-up tracking
    op.add_column(
        "story_previews",
        sa.Column("followed_up_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("followed_up_by", sa.String(255), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("follow_up_notes", sa.Text(), nullable=True),
    )
    
    # Payment tracking
    op.add_column(
        "story_previews",
        sa.Column("payment_initiated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("payment_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("payment_reference", sa.String(255), nullable=True),
    )
    
    # Index for abandoned trials query
    op.create_index(
        "ix_story_previews_abandoned",
        "story_previews",
        ["status", "preview_shown_at"],
        postgresql_where=sa.text("status = 'PREVIEW_GENERATED' OR status = 'ABANDONED_TRIAL'"),
    )


def downgrade() -> None:
    """Remove Try Before You Buy columns."""
    op.drop_index("ix_story_previews_abandoned", table_name="story_previews")
    
    op.drop_column("story_previews", "payment_reference")
    op.drop_column("story_previews", "payment_completed_at")
    op.drop_column("story_previews", "payment_initiated_at")
    op.drop_column("story_previews", "follow_up_notes")
    op.drop_column("story_previews", "followed_up_by")
    op.drop_column("story_previews", "followed_up_at")
    op.drop_column("story_previews", "abandoned_at")
    op.drop_column("story_previews", "preview_shown_at")
    op.drop_column("story_previews", "preview_images")
    op.drop_column("story_previews", "generated_prompts_cache")
    op.drop_column("story_previews", "is_preview_mode")
