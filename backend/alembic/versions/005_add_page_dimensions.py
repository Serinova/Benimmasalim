"""Add physical dimensions to page templates

Revision ID: 005
Revises: 004
Create Date: 2025-01-30
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: str | None = '004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add physical dimension columns to page_templates
    op.add_column('page_templates', sa.Column('page_width_mm', sa.Float(), nullable=True, server_default='210.0'))
    op.add_column('page_templates', sa.Column('page_height_mm', sa.Float(), nullable=True, server_default='297.0'))
    op.add_column('page_templates', sa.Column('bleed_mm', sa.Float(), nullable=True, server_default='3.0'))

    # Update existing records with default values based on page_type
    op.execute("""
        UPDATE page_templates 
        SET page_width_mm = 297, page_height_mm = 210, bleed_mm = 3.0 
        WHERE page_type = 'inner'
    """)
    op.execute("""
        UPDATE page_templates 
        SET page_width_mm = 326, page_height_mm = 246, bleed_mm = 3.0 
        WHERE page_type = 'cover'
    """)
    op.execute("""
        UPDATE page_templates 
        SET page_width_mm = 311, page_height_mm = 246, bleed_mm = 3.0 
        WHERE page_type = 'back'
    """)


def downgrade() -> None:
    op.drop_column('page_templates', 'bleed_mm')
    op.drop_column('page_templates', 'page_height_mm')
    op.drop_column('page_templates', 'page_width_mm')
