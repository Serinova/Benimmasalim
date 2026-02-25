"""Clear long style_negative_en so negatif prompt sadece constants + cap'ten gelir.

Uzun style_negative_en (tekrarlı boy/chibi/eyes vb.) kaldırılıyor; build_negative_prompt
zaten base + strict + style_specific ile 50 terim sınırı uyguluyor.

Revision ID: 025_clear_style_neg
Revises: 024_sync_templates
Create Date: 2026-02-08

"""
from collections.abc import Sequence

from alembic import op

revision: str = "025_clear_style_neg"
down_revision: str = "022_manifest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 200 karakterden uzun style_negative_en = tekrarlı liste; temizle (kod constants kullanır).
MAX_STYLE_NEGATIVE_LEN = 200


def upgrade() -> None:
    op.execute(
        "UPDATE visual_styles SET style_negative_en = NULL "
        "WHERE style_negative_en IS NOT NULL AND LENGTH(style_negative_en) > " + str(MAX_STYLE_NEGATIVE_LEN)
    )


def downgrade() -> None:
    pass  # Geri alınamaz; eski uzun değerler kaybolur.
