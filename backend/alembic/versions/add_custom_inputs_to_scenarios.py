"""Add custom_inputs_schema to scenarios

Revision ID: add_custom_inputs
Revises: 
Create Date: 2024-01-31

This migration adds the custom_inputs_schema JSONB column to the scenarios table.
This enables admins to define custom input fields per scenario that users can fill out.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_custom_inputs'
down_revision = '013_add_progress'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add custom_inputs_schema column
    op.add_column(
        'scenarios',
        sa.Column(
            'custom_inputs_schema',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Dynamic input fields defined by admin for this scenario'
        )
    )
    
    # Add ai_prompt_template if it doesn't exist
    # (This might already exist from initial schema)
    try:
        op.add_column(
            'scenarios',
            sa.Column(
                'ai_prompt_template',
                sa.Text(),
                nullable=True,
                comment='Template for AI story text generation (Gemini)'
            )
        )
    except Exception:
        pass  # Column might already exist


def downgrade() -> None:
    op.drop_column('scenarios', 'custom_inputs_schema')
    # Don't drop ai_prompt_template as it might have been there before
