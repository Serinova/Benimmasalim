"""Efes Antik Kenti: rehberli gezi, puzzle/zorluk, başlık '[Ad]'ın Efes Antik Kenti', custom_inputs kaldır.

Revision ID: 123_efes_antik
Revises: 122_cappadocia_guide
Create Date: 2026-03-05

"""
from alembic import op
from sqlalchemy.sql import text

revision = "123_efes_antik"
down_revision = "122_cappadocia_guide"
branch_labels = None
depends_on = None

NEW_NAME = "Efes Antik Kenti"
NEW_DESCRIPTION = (
    "Rehber ile Efes Antik Kenti gezisi. Celsus Kütüphanesi, Büyük Tiyatro, "
    "Curetes Caddesi, teras evler, Artemis kalıntıları. Çocuk zorlukları aşar, "
    "bulmaca çözer. Kitap adı: [Çocuk adı]'ın Efes Antik Kenti."
)

NEW_STORY_PROMPT_TR = r"""
# EFES ANTİK KENTİ

## YAPI: {child_name} REHBER İLE EFES ANTİK KENTİ GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Efes Antik Kenti" olmalı. Alt başlık EKLEME.

**KURGU:** Rehber (insan, yetişkin — yüzü detaylı tarif etme) çocuğu Efes'in antik yapılarında gezdiriyor. Çocuk AKTİF: yol bulma, rehberin verdiği küçük görevler (sütun sayısı bulma, haritada işaret bulma, çıkışı bulma), yorulup devam etme. Zorluklar gerçekçi. Her zorluğu AŞAR. Sihir, fantastik varlık YOK.

**YERLER (gerçek):** Celsus Kütüphanesi (12.000 kitap, iki katlı cephe), Büyük Tiyatro (25.000 kişi, akustik), Curetes Caddesi (mermer sütunlu cadde), teras evler (mozaik, fresk), Artemis Tapınağı kalıntıları (Dünya'nın 7 Harikasından biri). İzmir Selçuk, UNESCO Dünya Mirası.

---

### Bölüm 1 — Varış, rehber, ilk izlenim (Sayfa 1-4)
- {child_name} Efes Antik Kenti'ne geliyor (Selçuk). Tur rehberi ile tanışıyor. Mermer sütunlar, antik yollar.
- Rehber kısaca anlatıyor: 3000 yıllık kent, Roma ve Yunan uygarlığı. Çocuk merakla dinliyor.
- İlk zorluk: Girişte yol ikiye ayrılıyor; rehber haritada noktayı gösteriyor, çocuk doğru yolu seçiyor. İlk başarı.

### Bölüm 2 — Celsus Kütüphanesi (Sayfa 5-8)
- Celsus Kütüphanesi önüne varılıyor. İki katlı cephe, sütunlar, heykeller. Rehber: 12.000 parşömen, antik bilim merkezi.
- Küçük görev: Rehber cephedeki heykellerden birinin adını bulmasını istiyor (ipucu veriyor). Çocuk bakar, bulur. Keşif sevinci.
- "Burada binlerce yıl önce insanlar kitap okuyormuş!" Tarih bilinci.

### Bölüm 3 — Büyük Tiyatro (Sayfa 9-12)
- Büyük Tiyatro'ya çıkılıyor. 25.000 kişilik, dağa oyulmuş. Rehber akustik mucizesini anlatıyor.
- Zorluk: Basamaklarda rehber "en üst sıraya kadar say" diyor; çocuk yoruluyor ama sayıyor, tamamlıyor. Sebat.
- Sahneden en üste ses ulaşıyor — deniyorlar. Hayranlık.

### Bölüm 4 — Curetes Caddesi, mermer sokaklar (Sayfa 13-16)
- Curetes Caddesi: mermer döşeme, yüksek sütunlar. Rehber Roma ihtişamını anlatıyor.
- Küçük bulmaca: Cadde sonunda rehber "üç sütunlu kapıyı bul" diyor; çocuk yürüyor, buluyor. Başarı.
- Heykeller, mozaik kalıntıları. "2000 yıl önce buradaydı!" duygusu.

### Bölüm 5 — Teras evler, mozaikler (Sayfa 17-19)
- Teras evlere giriliyor (veya dışarıdan anlatılıyor). Mozaikler, freskler. Rehber Roma yaşamını anlatıyor.
- Yoruluyor ama devam ediyor. "Biraz daha!" Rehber teşvik ediyor. Bitiriyor. Sebat.

### Bölüm 6 — Artemis Tapınağı kalıntıları, kapanış (Sayfa 20-22)
- Artemis Tapınağı kalıntılarına uğranıyor (Dünya'nın 7 Harikasından biri). Rehber kısaca anlatıyor.
- Gezinin sonu. Rehber tebrik ediyor: "Zorlukları aştın, antik kenti keşfettin."
- {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış.

---

## KURALLAR
- Rehber = gerçek insan (yüz detayı verme). Sihir, peri, konuşan hayvan YOK.
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: Celsus, Büyük Tiyatro, Curetes Caddesi, teras evler, Artemis kalıntıları.
- Korku/şiddet yok; gerilim hafif (yorulma, yön bulma) ve hep aşılır.
- Kitap adı SADECE "[Çocuk adı]'ın Efes Antik Kenti". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""

# Seyahatin ruhuna özgü kıyafet — kız ve erkek tutarlı (antik kent gezisi, Ege güneşi)
OUTFIT_GIRL = (
    "soft lavender purple cotton t-shirt with small sun emblem, "
    "light blue denim shorts reaching knees, white canvas sneakers, "
    "wide-brim white sun hat with lavender ribbon, small white crossbody bag. "
    "EXACTLY the same outfit on every page — same lavender shirt, same blue shorts, same white hat."
)
OUTFIT_BOY = (
    "sky blue cotton t-shirt with small Greek column emblem, "
    "sand-colored cotton chino shorts, white canvas sneakers with blue stripes, "
    "white baseball cap, small beige canvas backpack on back. "
    "EXACTLY the same outfit on every page — same blue shirt, same sand shorts, same white cap."
)


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE scenarios
            SET name = :name,
                description = :description,
                story_prompt_tr = :prompt,
                custom_inputs_schema = '[]'::jsonb,
                outfit_girl = :outfit_girl,
                outfit_boy = :outfit_boy
            WHERE theme_key = 'ephesus'
               OR theme_key = 'ephesus_ancient_city'
               OR name ILIKE '%Efes%'
        """),
        {
            "name": NEW_NAME,
            "description": NEW_DESCRIPTION,
            "prompt": NEW_STORY_PROMPT_TR.strip(),
            "outfit_girl": OUTFIT_GIRL,
            "outfit_boy": OUTFIT_BOY,
        },
    )


def downgrade() -> None:
    pass
