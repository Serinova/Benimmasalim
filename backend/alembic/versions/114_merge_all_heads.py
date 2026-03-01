"""114_merge_all_heads

Revision ID: 114_merge_all_heads
Revises: 4b33877ce841, 113_fix_custom_inputs_options_format
Create Date: 2026-03-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '114_merge_all_heads'
down_revision: Union[str, None] = ('4b33877ce841', '113_fix_custom_inputs_options_format')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
