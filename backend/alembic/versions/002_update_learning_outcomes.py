"""Update learning_outcomes table with ai_prompt and display_order

Revision ID: 002
Revises: 001
Create Date: 2026-01-30

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to learning_outcomes
    op.add_column('learning_outcomes', sa.Column('ai_prompt', sa.Text(), nullable=True))
    op.add_column('learning_outcomes', sa.Column('category_label', sa.String(100), nullable=True))
    op.add_column('learning_outcomes', sa.Column('display_order', sa.Integer(), server_default='0', nullable=False))

    # Create index for ordering
    op.create_index('idx_outcomes_order', 'learning_outcomes', ['category', 'display_order'])


def downgrade() -> None:
    op.drop_index('idx_outcomes_order', table_name='learning_outcomes')
    op.drop_column('learning_outcomes', 'display_order')
    op.drop_column('learning_outcomes', 'category_label')
    op.drop_column('learning_outcomes', 'ai_prompt')
