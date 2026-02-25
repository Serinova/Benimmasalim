"""Add story_previews table

Revision ID: 007
Revises: 006
Create Date: 2025-01-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = '007'
down_revision: str | None = '006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'story_previews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),

        # Confirmation
        sa.Column('confirmation_token', sa.String(64), unique=True, nullable=False),
        sa.Column('status', sa.String(20), default='PENDING', nullable=False),

        # Parent info
        sa.Column('parent_name', sa.String(255), nullable=False),
        sa.Column('parent_email', sa.String(255), nullable=False),
        sa.Column('parent_phone', sa.String(50)),

        # Child info
        sa.Column('child_name', sa.String(255), nullable=False),
        sa.Column('child_age', sa.Integer, nullable=False),
        sa.Column('child_gender', sa.String(20)),

        # Product info
        sa.Column('product_id', UUID(as_uuid=True)),
        sa.Column('product_name', sa.String(255)),
        sa.Column('product_price', sa.Numeric(10, 2)),

        # Story content
        sa.Column('story_title', sa.String(500), nullable=False),
        sa.Column('story_pages', JSONB, nullable=False),

        # Options
        sa.Column('scenario_name', sa.String(255)),
        sa.Column('visual_style_name', sa.String(255)),
        sa.Column('learning_outcomes', JSONB),

        # Images
        sa.Column('page_images', JSONB),

        # Timestamps
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),

        # Admin
        sa.Column('admin_notes', sa.Text),
    )

    # Indexes
    op.create_index('idx_story_previews_token', 'story_previews', ['confirmation_token'])
    op.create_index('idx_story_previews_status', 'story_previews', ['status'])
    op.create_index('idx_story_previews_email', 'story_previews', ['parent_email'])


def downgrade() -> None:
    op.drop_index('idx_story_previews_email', 'story_previews')
    op.drop_index('idx_story_previews_status', 'story_previews')
    op.drop_index('idx_story_previews_token', 'story_previews')
    op.drop_table('story_previews')
