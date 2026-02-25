"""Add cultural elements and theme settings to scenarios

Revision ID: add_cultural_elements
Revises: add_custom_inputs
Create Date: 2025-01-31

This migration adds cultural enhancement columns to the scenarios table:
- location_constraints: Required location elements for all scenes
- cultural_elements: JSONB for cultural background elements
- theme_key: Theme identifier for scenario categorization
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_cultural_elements'
down_revision = 'add_custom_inputs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add location_constraints column
    op.add_column(
        'scenarios',
        sa.Column(
            'location_constraints',
            sa.Text(),
            nullable=True,
            comment='Required location elements that must appear in every scene'
        )
    )
    
    # Add cultural_elements JSONB column
    op.add_column(
        'scenarios',
        sa.Column(
            'cultural_elements',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Cultural background elements for themed bokeh backgrounds'
        )
    )
    
    # Add theme_key column
    op.add_column(
        'scenarios',
        sa.Column(
            'theme_key',
            sa.String(100),
            nullable=True,
            comment='Theme identifier for automatic clothing and background selection'
        )
    )
    
    # Add index for theme_key lookups
    op.create_index(
        'idx_scenarios_theme_key',
        'scenarios',
        ['theme_key'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_scenarios_theme_key', table_name='scenarios')
    op.drop_column('scenarios', 'theme_key')
    op.drop_column('scenarios', 'cultural_elements')
    op.drop_column('scenarios', 'location_constraints')
