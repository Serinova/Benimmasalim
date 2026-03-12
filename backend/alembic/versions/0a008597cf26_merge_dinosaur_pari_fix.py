"""merge_dinosaur_pari_fix

Revision ID: 0a008597cf26
Revises: d5e6f7a8b9c0, 6d3e85fd8843
Create Date: 2026-03-11 16:21:13.844537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a008597cf26'
down_revision: Union[str, None] = ('d5e6f7a8b9c0', '6d3e85fd8843')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
