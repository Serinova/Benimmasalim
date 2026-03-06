"""Kudüs: rehberli gezi, puzzle/zorluk, başlık '[Ad]'ın Kudüs Macerası', custom_inputs kaldır.

Revision ID: 127_kudus_guide
Revises: 126_galata_guide
Create Date: 2026-03-05

"""
from alembic import op
from sqlalchemy.sql import text

revision = "127_kudus_guide"
down_revision = "126_galata_guide"
branch_labels = None
depends_on = None

NEW_NAME = "Kudüs Macerası"
NEW_DESCRIPTION = (
    "Rehber ile Kudüs Eski Şehir gezisi. Surlar, taş sokaklar, çarşı, "
    "dört mahalle, panoramik manzara. Çocuk zorlukları aşar, bulmaca çözer. "
    "Kitap adı: [Çocuk adı]'ın Kudüs Macerası."
)

NEW_STORY_PROMPT_TR = r"""
# KUDÜS MACERASI

## YAPI: {child_name} REHBER İLE KUDÜS ESKİ ŞEHİR GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Kudüs Macerası" olmalı. Alt başlık (Eski Şehir Macerası vb.) EKLEME.

**KURGU:** Rehber (tur rehberi, yetişkin insan — yüzü detaylı tarif etme) çocuğu Eski Şehir'de gezdiriyor. Çocuk AKTİF: yol bulma, rehberin verdiği küçük görevler (haritada Şam Kapısı'nı bul, çarşıda belirli bir baharatı bul, dört mahalleden birinin yolunu bul), yorulup devam etme. Zorluklar gerçekçi. Her zorluğu AŞAR. Sihir, konuşan hayvan (Bilge Kedi vb.) YOK.

**KÜLTÜREL HASSASİYET:** 3 dine EŞİT saygı. Dini ritüel/ibadet sahnesi YOK. Peygamber veya dini figür görseli YOK. Odak: MİMARİ (surlar, kubbe, taş işçiliği), ÇARŞI (baharat, zanaat), ARKEOLOJİ, HOŞGÖRÜ. Yapılar "tarihî anıt ve mimari şaheser" olarak anlatılır. Siyasi mesaj YOK.

**YERLER (gerçek):** Kudüs Eski Şehir, UNESCO Dünya Mirası. Şam Kapısı, Osmanlı surları (16. yüzyıl). Altın rengi Kudüs taşı, dar taş sokaklar, kemerli geçitler. Kubbetüs-Sahra (dışarıdan mimari — kubbe, çiniler). Kapalı çarşı: baharat, bakır, el sanatları. Dört mahalle: farklı mimari ve atmosfer. Surların üstü: panoramik manzara.

---

### Bölüm 1 — Varış, Şam Kapısı (Sayfa 1-4)
- {child_name} Kudüs Eski Şehir'e geliyor. Tur rehberi ile tanışıyor. Şam Kapısı, dev taş surlar.
- Rehber kısaca anlatıyor: "Bu surların ardında 5000 yıllık tarih var." Çocuk merakla dinliyor.
- İlk zorluk: Haritada Şam Kapısı'nı bul — rehber ipucu veriyor, çocuk kapıyı gösteriyor. İlk başarı.
- Altın rengi Kudüs taşı güneşte parlıyor. "Ne kadar güzel!" Hayranlık.

### Bölüm 2 — Taş sokaklar, Kubbetüs-Sahra manzarası (Sayfa 5-8)
- Dar sokaklarda yürüyüş. Kemerli geçitler, taş binalar. Rehber: "İleride altın kubbe görünecek — tarihî bir yapı."
- Yüksek bir noktadan Kubbetüs-Sahra (dışarıdan) görünüyor — altın kubbe, mavi çiniler. Mimari olarak anlat; ibadet/ritüel YOK.
- Küçük görev: Rehber "Bu sokakta kaç kemer var, sayalım" diyor. Çocuk sayıyor. Keşif sevinci.

### Bölüm 3 — Çarşı: baharat ve zanaat (Sayfa 9-12)
- Kapalı çarıya giriş. Baharat tezgahları, bakır fenerler, el işi dükkanları. Rehber kokuları ve renkleri anlatıyor.
- Zorluk: Rehber "Zerdeçalı bul — hangi tezgah?" diyor. Çocuk dolaşıyor, buluyor. Başarı.
- Bir mozaik veya seramik atölyesi (isteğe bağlı) — "Taşları birleştiriyorlar!" Kültürel zenginlik.

### Bölüm 4 — Dört mahalle (Sayfa 13-16)
- Rehber: "Eski Şehir dört mahalleden oluşur, her biri kendine özgü." Sokaklar arasında geziyorlar.
- Küçük bulmaca: Rehber "Şimdi surlara doğru gideceğiz — hangi yön?" Haritaya bakıp çocuk yönü buluyor. Sebat.
- Farklı mimari detaylar, aynı altın taş. "Farklılıklar zenginliktir!" Mesaj (din adı vermeden).

### Bölüm 5 — Surlar, panoramik manzara (Sayfa 17-19)
- Surların üstüne çıkılıyor (veya sur yolunda). Eski Şehir ayakların altında — kubbeler, taş çatılar. Rehber tarihi anlatıyor.
- Yoruluyor; rehber "Biraz dinlenelim, manzarayı sevelim" diyor. Çocuk nefes alıyor, devam ediyor. Cesaret.
- "Bu şehir insanlığın ortak hazinesi." UNESCO perspektifi.

### Bölüm 6 — Kapanış (Sayfa 20-22)
- Şam Kapısı'na doğru dönüş. Rehber tebrik ediyor: "Zorlukları aştın, Kudüs'ü keşfettin."
- {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış. Hoşgörü ve barış vurgusu (soyut, siyasi olmadan).

---

## KURALLAR
- Rehber = gerçek insan (yüz detayı verme). Sihir, Bilge Kedi veya konuşan hayvan YOK.
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: Şam Kapısı, surlar, taş sokaklar, Kubbetüs-Sahra (sadece dış mimari), çarşı, dört mahalle, sur panoraması.
- Dini ritüel/ibadet sahnesi YOK. Peygamber/dini figür görseli YOK. 3 dine eşit saygı.
- Kitap adı SADECE "[Çocuk adı]'ın Kudüs Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""

OUTFIT_GIRL = (
    "soft ivory white cotton long-sleeve modest dress reaching ankles, "
    "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
    "fabric drapes softly over shoulders and chest (modern proper hijab wrap, NOT a loose veil, NOT fabric on top of head only), "
    "comfortable light beige flat sandals, small white cotton drawstring bag. "
    "EXACTLY the same outfit on every page — same ivory dress, same properly wrapped white hijab, same beige sandals."
)
OUTFIT_BOY = (
    "clean white cotton knee-length kurta tunic shirt, "
    "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
    "comfortable tan leather sandals, small white cotton drawstring bag. "
    "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
)

COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Ancient Jerusalem Old City walls, golden Dome of the Rock in distance. "
    "Narrow cobblestone streets, golden Jerusalem stone. "
    "Wide shot: child 25%, historic architecture 75%. Peaceful, UNESCO site."
)
PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Walls: Ottoman golden limestone / Dome of Rock: golden dome, blue tiles / "
    "Souq: spices, copper lanterns, crafts / Alleys: narrow cobblestone, arched / "
    "Four Quarters: diverse architecture / Jerusalem stone: warm golden glow]. "
    "Golden light, peaceful, historic. NO religious ritual, architecture and culture only."
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
                outfit_boy = :outfit_boy,
                cover_prompt_template = :cover_prompt,
                page_prompt_template = :page_prompt
            WHERE theme_key = 'kudus'
               OR theme_key = 'jerusalem_old_city'
               OR name ILIKE '%Kudüs%'
               OR name ILIKE '%Kudus%'
               OR name ILIKE '%Jerusalem%'
        """),
        {
            "name": NEW_NAME,
            "description": NEW_DESCRIPTION,
            "prompt": NEW_STORY_PROMPT_TR.strip(),
            "outfit_girl": OUTFIT_GIRL,
            "outfit_boy": OUTFIT_BOY,
            "cover_prompt": COVER_PROMPT,
            "page_prompt": PAGE_PROMPT,
        },
    )


def downgrade() -> None:
    pass
