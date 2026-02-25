"""Add book templates and AI configuration tables.

Revision ID: 004
Revises: 003
Create Date: 2026-01-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: str | None = '003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Book Templates table
    op.create_table(
        'book_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('page_width_mm', sa.Float, default=210.0),
        sa.Column('page_height_mm', sa.Float, default=210.0),
        sa.Column('bleed_mm', sa.Float, default=3.0),
        sa.Column('image_dpi', sa.Integer, default=300),
        sa.Column('image_format', sa.String(10), default='PNG'),
        sa.Column('default_page_count', sa.Integer, default=16),
        sa.Column('min_page_count', sa.Integer, default=12),
        sa.Column('max_page_count', sa.Integer, default=32),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Page Templates table
    op.create_table(
        'page_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('page_type', sa.String(20), default='inner'),
        sa.Column('image_width_percent', sa.Float, default=100.0),
        sa.Column('image_height_percent', sa.Float, default=70.0),
        sa.Column('image_x_percent', sa.Float, default=0.0),
        sa.Column('image_y_percent', sa.Float, default=0.0),
        sa.Column('image_aspect_ratio', sa.String(10), default='1:1'),
        sa.Column('text_width_percent', sa.Float, default=90.0),
        sa.Column('text_height_percent', sa.Float, default=25.0),
        sa.Column('text_x_percent', sa.Float, default=5.0),
        sa.Column('text_y_percent', sa.Float, default=72.0),
        sa.Column('text_position', sa.String(20), default='bottom'),
        sa.Column('font_family', sa.String(100), default='Nunito'),
        sa.Column('font_size_pt', sa.Integer, default=14),
        sa.Column('font_color', sa.String(20), default='#333333'),
        sa.Column('text_align', sa.String(20), default='center'),
        sa.Column('line_height', sa.Float, default=1.5),
        sa.Column('background_color', sa.String(20), default='#FFFFFF'),
        sa.Column('margin_top_mm', sa.Float, default=10.0),
        sa.Column('margin_bottom_mm', sa.Float, default=10.0),
        sa.Column('margin_left_mm', sa.Float, default=10.0),
        sa.Column('margin_right_mm', sa.Float, default=10.0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('extra_styles', postgresql.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # AI Generation Config table
    op.create_table(
        'ai_generation_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('image_provider', sa.String(50), default='gemini_flash'),
        sa.Column('image_model', sa.String(100), default='gemini-2.0-flash-exp-image-generation'),
        sa.Column('image_width', sa.Integer, default=1024),
        sa.Column('image_height', sa.Integer, default=1024),
        sa.Column('image_quality', sa.String(20), default='high'),
        sa.Column('style_prefix', sa.Text),
        sa.Column('style_suffix', sa.Text),
        sa.Column('negative_prompt', sa.Text),
        sa.Column('story_provider', sa.String(50), default='gemini'),
        sa.Column('story_model', sa.String(100), default='gemini-2.0-flash'),
        sa.Column('story_temperature', sa.Float, default=0.7),
        sa.Column('story_max_tokens', sa.Integer, default=8192),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_book_templates_active', 'book_templates', ['is_active'])
    op.create_index('idx_page_templates_type', 'page_templates', ['page_type', 'is_active'])
    op.create_index('idx_ai_configs_active', 'ai_generation_configs', ['is_active', 'is_default'])


def downgrade() -> None:
    op.drop_table('ai_generation_configs')
    op.drop_table('page_templates')
    op.drop_table('book_templates')
