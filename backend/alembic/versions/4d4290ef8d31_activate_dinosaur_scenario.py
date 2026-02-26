"""activate_dinosaur_scenario

Revision ID: 4d4290ef8d31
Revises: e3875d2e31be
Create Date: 2026-02-25 18:56:49.268299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d4290ef8d31'
down_revision: Union[str, None] = 'e3875d2e31be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Activate Dinozorlar Macerası scenario."""
    conn = op.get_bind()
    
    # Activate the dinosaur scenario
    conn.execute(
        sa.text("""
            UPDATE scenarios 
            SET is_active = true,
                display_order = 13
            WHERE name ILIKE '%Dinozor%'
        """)
    )
    print("OK: Dinozorlar Macerasi senaryosu aktiflestirildi")


def downgrade() -> None:
    """Deactivate Dinozorlar Macerası scenario."""
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE scenarios SET is_active = false WHERE name ILIKE '%Dinozor%'")
    )
