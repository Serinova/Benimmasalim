"""Fill missing scenario marketing fields and fix price labels.

All scenarios are linked to A4 YATAY product (base_price = 1250 TL).
Price label should reflect actual product price, not hardcoded 299 TL.

Revision ID: 107_fill_scenario_marketing_fields
Revises: 106
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "107_fill_scenario_marketing_fields"
down_revision = "106_text_valign"
branch_labels = None
depends_on = None

# Correct price label from the linked product (A4 YATAY, base_price=1250)
PRICE_LABEL = "1.250 TL'den başlayan fiyatlarla"


def upgrade() -> None:
    conn = op.get_bind()

    # ─────────────────────────────────────────────────────────────────
    # 1. Scenarios that already have data but WRONG price label (299 TL)
    #    Fix: Umre, Güneş Sistemi, Okyanus
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text(
            "UPDATE scenarios SET marketing_price_label = :label "
            "WHERE marketing_price_label LIKE '%299 TL%'"
        ),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 2. Kapadokya Macerası
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'Peri bacaları ve sıcak hava balonlarıyla unutulmaz bir Anadolu macerası',
                age_range = '5-10 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'Türkiye Macerası',
                marketing_price_label = :label,
                marketing_features = '["Peri bacaları ve volkanik oluşumlar", "Renkli sıcak hava balonları", "Gizemli yeraltı şehirleri", "Yerli kültür ve gelenekler", "Doğa ve çevre bilinci", "Kapadokya''nın eşsiz manzaraları"]'::jsonb
            WHERE name ILIKE '%Kapadokya%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 3. Yerebatan Sarnıcı
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'İstanbul''un gizemli yeraltı sarayında Bizans''tan kalma büyülü macera',
                age_range = '6-10 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'İstanbul Macerası',
                marketing_price_label = :label,
                marketing_features = '["Yüzlerce antik mermer sütun", "Efsanevi Medusa başları", "Kehribar ışıklı Bizans sırrı", "Tarihî İstanbul atmosferi", "Arkeolojik keşif macerası", "Su altı yansımaları ve gizem"]'::jsonb
            WHERE name ILIKE '%Yerebatan%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 4. Göbeklitepe Macerası
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'Dünyanın en eski tapınağında 12.000 yıllık gizemi çöz',
                age_range = '6-11 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'Arkeoloji Macerası',
                marketing_price_label = :label,
                marketing_features = '["Dev dikilitaşlar ve hayvan kabartmaları", "12.000 yıllık antik sırlar", "Arkeolojik kazı macerası", "Şanlıurfa''nın büyülü toprakları", "Tarih öncesi uygarlık keşfi", "Merak ve bilim sevgisi"]'::jsonb
            WHERE name ILIKE '%Göbeklitepe%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 5. Efes Antik Kent Macerası
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'Antik dünyanın en görkemli şehrinde 2.000 yıllık macera',
                age_range = '6-11 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'Antik Çağ',
                marketing_price_label = :label,
                marketing_features = '["Celsus Kütüphanesi ve bilgelik heykelleri", "Canlanan antik mozaikler", "Roma döneminden kalma anıtlar", "Ege''nin büyülü sahil kültürü", "Tarihsel arkeolojik keşif", "Büyük antik tiyatrada sahne"]'::jsonb
            WHERE name ILIKE '%Efes%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 6. Çatalhöyük Neolitik Kenti Macerası
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'İnsanlığın ilk şehrinde 9.000 yıllık Neolitik macera',
                age_range = '6-11 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'Tarih Öncesi',
                marketing_price_label = :label,
                marketing_features = '["Çatıdan girilen antik evler", "Canlanan Neolitik duvar resimleri", "Ana Tanrıça''nın sırları", "Obsidyen aynalar ve arkeoloji", "İnsanlığın ilk şehir yaşamı", "Konya Ovası''nda zaman yolculuğu"]'::jsonb
            WHERE name ILIKE '%Çatalhöyük%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 7. Sümela Manastırı Macerası
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'Karadeniz''in sisli ormanlarında kayalara oyulmuş gizemli manastır',
                age_range = '6-11 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'Karadeniz Macerası',
                marketing_price_label = :label,
                marketing_features = '["1.200 metre yükseklikte kayalık manastır", "Canlanan antik freskler", "Fısıldayan kutsal kaynak suyu", "Sis içinden beliren gizemli geyik", "Altındere Vadisi ormanları", "Bizans döneminden kalma ikonalar"]'::jsonb
            WHERE name ILIKE '%Sümela%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 8. Sultanahmet Camii Macerası
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'İstanbul''un kalbinde 20.000 mavi İznik çinisinde büyülü macera',
                age_range = '5-10 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'İstanbul Macerası',
                marketing_price_label = :label,
                marketing_features = '["20.000 mavi İznik çinisi", "Vitraylardan süzülen renkli ışıklar", "Canlanan lale desenleri", "400 yıllık çini ustasının sırrı", "Sultanahmet Meydanı''nın tarihi", "Sanat ve mimarî harikası"]'::jsonb
            WHERE name ILIKE '%Sultanahmet%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 9. Galata Kulesi Macerası
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = '700 yıllık kulenin tepesinden İstanbul''a zaman yolculuğu',
                age_range = '6-11 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'İstanbul Macerası',
                marketing_price_label = :label,
                marketing_features = '["67 metre yükseklikten 360° İstanbul panoraması", "Hezârfen''in uçuş sırrını keşfet", "Spiral merdivende zaman yolculuğu", "Galata''nın büyülü sokakları", "Osmanlı ve Bizans tarihi", "Cesaret ve özgüven macerası"]'::jsonb
            WHERE name ILIKE '%Galata%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 10. Amazon Ormanları Keşfediyorum
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = 'Dünyanın en zengin ekosisteminde renkli hayvanlarla büyülü keşif',
                age_range = '5-10 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'Doğa Macerası',
                marketing_price_label = :label,
                marketing_features = '["Renkli Amazon papağanları ve kuşlar", "Pembe nehir yunusları (boto)", "Ağaç tembellerini yakından gör", "Dev kapok ağaçlarında tırmanma", "Biyolojik çeşitlilik keşfi", "Çevre ve doğa koruma bilinci"]'::jsonb
            WHERE name ILIKE '%Amazon%'
        """),
        {"label": PRICE_LABEL},
    )

    # ─────────────────────────────────────────────────────────────────
    # 11. Dinozorlar Macerası: Zaman Yolculuğu
    # ─────────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                tagline = '65 milyon yıl öncesine git, DEVASA dinozorlarla dostluk kur',
                age_range = '5-10 yaş',
                estimated_duration = '20-25 dakika okuma',
                rating = 5.0,
                marketing_badge = 'Zaman Yolculuğu',
                marketing_price_label = :label,
                marketing_features = '["T-Rex ile dostluk ve macera", "Pteranodon ile gökyüzünde uçuş", "Brachiosaurus sırtında yolculuk", "65 milyon yıl öncesi dünyası", "Paleontoloji ve hayvan bilgisi", "Epik zaman makinesi aventürü"]'::jsonb
            WHERE name ILIKE '%Dinozor%'
        """),
        {"label": PRICE_LABEL},
    )


def downgrade() -> None:
    # Revert price labels back to null (can't easily revert content fills)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE scenarios SET marketing_price_label = NULL "
            "WHERE marketing_price_label = :label"
        ),
        {"label": PRICE_LABEL},
    )
