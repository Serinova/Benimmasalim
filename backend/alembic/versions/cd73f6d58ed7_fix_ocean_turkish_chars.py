"""fix_ocean_turkish_chars

Revision ID: cd73f6d58ed7
Revises: 40b1fd5e552b
Create Date: 2026-02-25 22:38:37.397468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd73f6d58ed7'
down_revision: Union[str, None] = '40b1fd5e552b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix Turkish characters in ocean scenario marketing fields."""
    conn = op.get_bind()
    
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                marketing_badge = 'Okyanus Keşfi',
                age_range = '5-10 yaş'
            WHERE theme_key = 'ocean_depths'
        """)
    )
    print("✓ Okyanus scenario Turkish characters fixed")


def downgrade() -> None:
    pass
