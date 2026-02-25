"""update_umre_marketing_fields

Revision ID: a22af3bbaa39
Revises: 21de6d6830a4
Create Date: 2026-02-25 19:36:11.770274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a22af3bbaa39'
down_revision: Union[str, None] = '21de6d6830a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add marketing fields to Umre scenario."""
    import json
    
    conn = op.get_bind()
    
    marketing_features = json.dumps([
        "Kabe ve Mescid-i Haram ziyareti",
        "Safa-Marwa ve Zemzem suyu",
        "Medine ve yeşil kubbe",
        "Nur Dağı ve Arafat",
        "Saygı ve tevazu değerleri",
        "Ailece manevi bağ"
    ])
    
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                marketing_badge = :marketing_badge,
                age_range = :age_range,
                tagline = :tagline,
                marketing_features = :marketing_features,
                estimated_duration = :estimated_duration,
                marketing_price_label = :marketing_price_label,
                rating = :rating
            WHERE name ILIKE '%Umre%'
        """),
        {
            "marketing_badge": "Manevi Yolculuk",
            "age_range": "7-10 yaş",
            "tagline": "Kutsal topraklarda unutulmaz bir manevi deneyim",
            "marketing_features": marketing_features,
            "estimated_duration": "20-25 dakika okuma",
            "marketing_price_label": "299 TL'den başlayan fiyatlarla",
            "rating": 5.0,
        }
    )
    print("✓ Umre Yolculuğu senaryosu marketing alanları güncellendi")


def downgrade() -> None:
    """Remove marketing fields from Umre scenario."""
    conn = op.get_bind()
    
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                marketing_badge = NULL,
                age_range = NULL,
                tagline = NULL,
                marketing_features = NULL,
                estimated_duration = NULL,
                marketing_price_label = NULL,
                rating = NULL
            WHERE name ILIKE '%Umre%'
        """)
    )
