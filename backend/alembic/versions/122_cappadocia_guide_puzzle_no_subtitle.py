"""Kapadokya: rehberli gezi, puzzle/zorluk, başlık sadece 'Kapadokya Macerası', custom_inputs kaldır.

Revision ID: 122_cappadocia_guide
Revises: 121_umre_short_kafile
Create Date: 2026-03-05
"""

from alembic import op
from sqlalchemy.sql import text

revision = "122_cappadocia_guide"
down_revision = "121_umre_short_kafile"
branch_labels = None
depends_on = None

NEW_NAME = "Kapadokya Macerası"
NEW_DESCRIPTION = (
    "Rehber ile Kapadokya gezisi. Çocuk maceraya atılır, sır ve bulmaca çözer, "
    "peri bacaları, yeraltı şehri, kaya kiliseler ve balon turunda zorluklarla "
    "karşılaşır ve hepsini aşar. Kitap adı: [Çocuk adı]'ın Kapadokya Macerası."
)

NEW_STORY_PROMPT_TR = r"""
# KAPADOKYA MACERASI

## YAPI: {child_name} REHBER İLE KAPADOKYA GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Kapadokya Macerası" olmalı. Alt başlık (Doğa Mucizesi Keşfi vb.) EKLEME.

**PERİ BACALARI (gerçekçi):** Volkanik tüf — Erciyes, Hasan Dağı, Güllüdağ'dan lav ve kül. Milyonlarca yıl rüzgar ve yağmurun aşındırmasıyla koni biçimli şekiller, şapka taşları. Ürgüp, Göreme vadisi. Büyülü varlık/peri YOK; doğa ve tarih var.

**KURGU:** Rehber (insan, yetişkin — yüzü detaylı tarif etme) çocuğu Kapadokya'nın kültürel ve doğal yerlerinde gezdiriyor. Çocuk AKTİF: yol bulma, küçük bulmaca/ipucu çözme, karanlık veya dar yerde cesaret toplama, yorulup devam etme. Zorluklar gerçekçi. Her zorluğu AŞAR. Sihir, peri, ışıklı varlık YOK.

---

### Bölüm 1 — Varış, rehber, peri bacaları (Sayfa 1-4)
- {child_name} Kapadokya'ya geliyor. Tur rehberi ile tanışıyor. Göreme vadisi, peri bacaları.
- Rehber peri bacalarının nasıl oluştuğunu anlatıyor: volkanik tüf (Erciyes, Hasan Dağı), rüzgar ve yağmurla aşınma. Çocuk merakla dinliyor.
- İlk zorluk: Peri bacaları arasında yol ayrımında hangi yöne gideceğini bulması gerekiyor (rehber ipucu veriyor). Çocuk çözüyor, yol buluyor. İlk başarı.

### Bölüm 2 — Yeraltı şehri (Sayfa 5-9)
- Yeraltı şehrine giriş. Dar tüneller, katlar. Rehber tarihi anlatıyor (binlerce yıl önce insanlar burada yaşamış).
- Zorluk: Karanlık bir geçitte rehber "çıkışı bul" diye küçük görev veriyor (taşlardaki işaretler). {child_name} ipuçlarını birleştiriyor, çıkışı buluyor. Cesaret ve çözüm.
- Odalar: mutfak, havalandırma. Tarih bilinci.

### Bölüm 3 — Kaya kiliseler, freskler (Sayfa 10-13)
- Göreme Açık Hava Müzesi. Kayaya oyulmuş kiliseler, eski resimler. Rehber kısaca anlatıyor.
- Küçük bulmaca: Rehber duvardaki bir sembolü bulmasını istiyor; çocuk arar, bulur. Keşif sevinci.
- Yoruluyor ama devam ediyor. "Biraz daha!" diye kendini motive ediyor.

### Bölüm 4 — Balon turu (Sayfa 14-17)
- Sabah erken sıcak hava balonu turu. Rehber ve grup ile. Yükseliş, gökyüzünden peri bacaları ve vadiler.
- Hafif zorluk: İlk başta yükseklik heyecanı; nefes alıp sakinleşiyor, manzaraya odaklanıyor. Üstesinden gelme.
- İniş, güvenli. "Yaptım!" gururu.

### Bölüm 5 — Pembe vadi, son zorluk (Sayfa 18-20)
- Pembe Vadi'de yürüyüş. Gün batımına doğru kayalar pembe, turuncu. Rehber doğanın renklerini anlatıyor.
- Son meydan okuma: Uzun yürüyüşte "bitene kadar devam" — ayakları ağrıyor ama rehber teşvik ediyor, {child_name} bitiriyor. Sebat.
- Tepeden Kapadokya manzarası. "Her zorluğu aştım." tatmini.

### Bölüm 6 — Kapanış (Sayfa 21-22)
- Gezinin sonu. Rehber tebrik ediyor: "Zorlukları aştın, sırları çözdün."
- {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış.

---

## KURALLAR
- Sihir, peri, ışıklı varlık YOK. Rehber = gerçek insan (yüz detayı verme).
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: Göreme, peri bacaları, yeraltı şehri, kaya kiliseler, Pembe vadi, balon.
- Korku/şiddet yok; gerilim hafif ve hep aşılır.
- Kitap adı SADECE "[Çocuk adı]'ın Kapadokya Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE scenarios
            SET name = :name,
                description = :description,
                story_prompt_tr = :prompt,
                custom_inputs_schema = '[]'::jsonb
            WHERE theme_key = 'cappadocia'
               OR name ILIKE '%Kapadokya%'
        """),
        {
            "name": NEW_NAME,
            "description": NEW_DESCRIPTION,
            "prompt": NEW_STORY_PROMPT_TR.strip(),
        },
    )


def downgrade() -> None:
    pass
