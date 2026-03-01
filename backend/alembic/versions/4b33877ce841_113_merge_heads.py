"""113_merge_heads

Revision ID: 4b33877ce841
Revises: 109_invoice_serial_counter, 112_app_settings_and_product_vat
Create Date: 2026-03-01 18:25:46.801228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b33877ce841'
down_revision: Union[str, None] = ('109_invoice_serial_counter', '112_app_settings_and_product_vat')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
