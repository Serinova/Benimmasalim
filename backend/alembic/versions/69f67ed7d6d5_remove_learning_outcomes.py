"""remove_learning_outcomes

Revision ID: 69f67ed7d6d5
Revises: 0a008597cf26
Create Date: 2026-03-12 09:22:58.350155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69f67ed7d6d5'
down_revision: Union[str, None] = '0a008597cf26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('story_previews', 'learning_outcomes')
    op.drop_table('learning_outcomes')


def downgrade() -> None:
    op.create_table(
        'learning_outcomes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('category_label', sa.String(length=100), nullable=False),
        sa.Column('ai_prompt', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('story_previews', sa.Column('learning_outcomes', sa.JSON(), nullable=True))
