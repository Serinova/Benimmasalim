"""Seed style_negative_en from get_style_negative_default(prompt_modifier).

Mevcut visual_styles kayıtlarına stil bazlı varsayılan negatifleri yazar.
Admin panelde görünür ve düzenlenebilir; kodda style_negative_en boşsa yine get_style_negative_default kullanılır.

Revision ID: 027_style_neg_defaults
Revises: 026_ai_director
Create Date: 2026-02-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.prompt_engine.constants import get_style_negative_default

revision: str = "027_style_neg_defaults"
down_revision: str = "026_ai_director"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, prompt_modifier FROM visual_styles"))
    rows = result.fetchall()
    for row in rows:
        modifier = row[1] or ""
        neg = get_style_negative_default(modifier)
        conn.execute(
            sa.text("UPDATE visual_styles SET style_negative_en = :neg WHERE id = :id"),
            {"neg": neg, "id": row[0]},
        )


def downgrade() -> None:
    op.execute(
        sa.text("UPDATE visual_styles SET style_negative_en = NULL")
    )
