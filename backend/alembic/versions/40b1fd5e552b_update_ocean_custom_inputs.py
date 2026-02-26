"""update_ocean_custom_inputs

Revision ID: 40b1fd5e552b
Revises: 6d3f1cc0f9da
Create Date: 2026-02-25 22:23:16.212689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40b1fd5e552b'
down_revision: Union[str, None] = '6d3f1cc0f9da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update Okyanus Derinlikleri custom_inputs_schema."""
    from scripts.update_ocean_adventure_scenario import OCEAN_CUSTOM_INPUTS
    import json
    
    conn = op.get_bind()
    
    custom_inputs_json = json.dumps(OCEAN_CUSTOM_INPUTS)
    
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                custom_inputs_schema = CAST(:custom_inputs AS jsonb)
            WHERE theme_key = 'ocean_depths'
        """),
        {
            "custom_inputs": custom_inputs_json
        }
    )
    print("OK: Okyanus Derinlikleri custom_inputs_schema guncellendi")


def downgrade() -> None:
    """Remove custom_inputs_schema for ocean scenario."""
    conn = op.get_bind()
    
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                custom_inputs_schema = NULL
            WHERE theme_key = 'ocean_depths'
        """)
    )
