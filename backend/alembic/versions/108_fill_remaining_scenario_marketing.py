"""Fill remaining partially-empty scenario marketing fields.

Fills Kudüs, Oyuncak Dünyası, and Masal Dünyası scenarios
that still have partial marketing data missing.

Revision ID: 108_fill_remaining_scenario_marketing
Revises: 107_fill_scenario_marketing_fields
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "108_fill_remaining_scenario_marketing"
down_revision = "107_fill_scenario_marketing_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ─────────────────────────────────────────────────────────────────
    # Kudüs Eski Şehir Macerası
    # (already has tagline, age_range, marketing_badge)
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_features = '["UNESCO Dünya Mirası surlar ve antik şehir", "5.000 yıllık taş sokak zaman yolculuğu", "Sihirli baharat çarşısı keşfi", "Altın rengi Kudüs taşının ışığı", "Kültürlerin ve dinlerin mozaiği", "Heyecanlı arkeolojik keşifler"]'::jsonb
            WHERE name ILIKE '%Kudüs%'
        """),
    )

    # ─────────────────────────────────────────────────────────────────
    # Oyuncak Dünyası Macerası
    # (already has tagline, age_range, marketing_badge)
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                estimated_duration = '15-20 dakika okuma',
                rating = 5.0,
                marketing_features = '["Dev pelüş ayılarla büyülü macera", "Tahta blok kaleleri keşfet", "Gökkuşağı bilye yollarında süzül", "Kurşun asker geçit töreni", "Gece yarısı oyuncakların sırrı", "Sevgi ve dostluğun gücü"]'::jsonb
            WHERE name ILIKE '%Oyuncak%'
        """),
    )

    # ─────────────────────────────────────────────────────────────────
    # Masal Dünyası Macerası
    # (already has tagline, age_range, marketing_badge)
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                estimated_duration = '15-20 dakika okuma',
                rating = 5.0,
                marketing_features = '["Cesur Şövalye ve Bilge Ejderha", "Cüce Ustalar ve Deniz Kızı", "Karışan hikâyeleri düzelt", "Kendi masalını yaz macerası", "Hayal gücü ve yaratıcılık", "Büyülü masal dünyasına yolculuk"]'::jsonb
            WHERE name ILIKE '%Masal Dünyası%'
        """),
    )


def downgrade() -> None:
    pass
