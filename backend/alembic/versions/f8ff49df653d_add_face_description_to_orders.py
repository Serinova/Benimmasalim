"""add_face_description_to_orders

Revision ID: f8ff49df653d
Revises: 6f19fb98f68c
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f8ff49df653d'
down_revision: Union[str, None] = '6f19fb98f68c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add face_description column to orders table
    # This stores the forensic face analysis for AI image generation
    op.add_column(
        'orders',
        sa.Column('face_description', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('orders', 'face_description')
