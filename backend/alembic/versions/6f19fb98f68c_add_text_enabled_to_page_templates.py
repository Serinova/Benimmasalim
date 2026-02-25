"""add_text_enabled_to_page_templates

Revision ID: 6f19fb98f68c
Revises: 4ed0b5e4ede9
Create Date: 2026-02-02 02:40:26.030709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6f19fb98f68c'
down_revision: Union[str, None] = '4ed0b5e4ede9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add text_enabled column to page_templates
    # Default to True for existing templates (text is shown)
    op.add_column(
        'page_templates',
        sa.Column('text_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
    # Remove server_default after column is created
    op.alter_column('page_templates', 'text_enabled', server_default=None)


def downgrade() -> None:
    op.drop_column('page_templates', 'text_enabled')
