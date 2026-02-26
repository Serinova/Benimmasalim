"""add coloring book fields to story preview

Revision ID: ae6a0f427999
Revises: 093
Create Date: 2026-02-26 14:40:12.118096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ae6a0f427999'
down_revision: Union[str, None] = '093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add coloring book fields to story_previews if they don't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('story_previews')]
    
    if 'coloring_pdf_url' not in columns:
        op.add_column('story_previews', sa.Column('coloring_pdf_url', sa.Text(), nullable=True))
    
    if 'has_coloring_book' not in columns:
        op.add_column('story_previews', sa.Column('has_coloring_book', sa.Boolean(), server_default='false', nullable=False))
    else:
        # Ensure it's not null if it exists
        op.execute("UPDATE story_previews SET has_coloring_book = false WHERE has_coloring_book IS NULL")
        op.alter_column('story_previews', 'has_coloring_book', nullable=False, server_default='false')

def downgrade() -> None:
    op.drop_column('story_previews', 'coloring_pdf_url')
    op.drop_column('story_previews', 'has_coloring_book')
