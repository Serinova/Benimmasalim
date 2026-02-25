"""Fix Yerebatan Sarnici null description.

The Yerebatan Sarnici scenario had description=NULL in production.

Revision ID: 055_fix_yerebatan_description
Revises: 054_rebuild_prompt_templates
Create Date: 2026-02-20
"""
from collections.abc import Sequence

from alembic import op

revision: str = "055_fix_yerebatan_description"
down_revision: str = "054_rebuild_prompt_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

YEREBATAN_DESCRIPTION = (
    "İstanbul'un gizemli yeraltı sarayında, yüzlerce antik mermer sütun ve efsanevi "
    "Medusa başları arasında büyülü bir macera! Bizans döneminden kalma bu muhteşem "
    "sarnıçta, kehribar ışıklarla aydınlanan sütunların su yüzeyindeki yansımalarını "
    "keşfet ve tarihin derinliklerine dal!"
)


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE scenarios
        SET description = '{YEREBATAN_DESCRIPTION.replace("'", "''")}'
        WHERE name ILIKE '%Yerebatan%'
          AND (description IS NULL OR description = '')
        """
    )


def downgrade() -> None:
    pass
