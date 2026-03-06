"""Sümela: rehberli gezi, puzzle/zorluk, başlık '[Ad]'ın Sümela Macerası', custom_inputs kaldır.

Revision ID: 125_sumela_guide
Revises: 124_catalhoyuk_guide
Create Date: 2026-03-05

"""
from alembic import op
from sqlalchemy.sql import text

revision = "125_sumela_guide"
down_revision = "124_catalhoyuk_guide"
branch_labels = None
depends_on = None

NEW_NAME = "Sümela Macerası"
NEW_DESCRIPTION = (
    "Rehber ile Sümela ve Altındere Vadisi gezisi. Orman, şelale, taş basamaklar, "
    "kayaya oyulmuş manastır. Çocuk zorlukları aşar, bulmaca çözer. "
    "Kitap adı: [Çocuk adı]'ın Sümela Macerası."
)

NEW_STORY_PROMPT_TR = r"""
# SÜMELA MACERASI

## YAPI: {child_name} REHBER İLE SÜMELA MANASTIRI VE ALTINDERE VADİSİ GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Sümela Macerası" olmalı. Alt başlık (Dağ Keşfi vb.) EKLEME.

**KURGU:** Rehber (tur rehberi veya milli park rehberi, yetişkin insan — yüzü detaylı tarif etme) çocuğu Altındere Vadisi'nden başlayıp Sümela Manastırı'na kadar götürüyor. Çocuk AKTİF: yol bulma, rehberin verdiği küçük görevler (haritada şelaleyi bul, taş basamakları say, manastır terasını bul), yorulup devam etme. Zorluklar gerçekçi (yükseklik, yorgunluk). Her zorluğu AŞAR. Sihir, fantastik varlık YOK.

**KÜLTÜREL HASSASİYET (KUDÜS STANDARDI):** Dini figür tasviri YOK (İsa, Meryem, azizler). İbadet detayı YOK. Odak: TARİHİ MİMARİ (kayaya oyulmuş yapı, taş kemerler) ve DOĞA (orman, şelale, dağ). Freskler uzaktan sanat olarak — figür detayı verme.

**YERLER (gerçek):** Trabzon, Maçka — Altındere Vadisi Milli Parkı. Yeşil orman, çam ağaçları, şelale. Taş patika, dik taş basamaklar. Sümela Manastırı: 1200m yükseklikte kayalığa oyulmuş, Bizans dönemi taş mimarisi (MS 4. yüzyıl). Kemerler, odalar, teras — sadece mimari ve manzara.

---

### Bölüm 1 — Varış, Altındere Vadisi (Sayfa 1-4)
- {child_name} Altındere Vadisi'ne geliyor (Trabzon, Maçka). Tur rehberi ile tanışıyor. Yeşil orman, dağ havası.
- Rehber kısaca anlatıyor: "Yukarıda kayalara oyulmuş tarihi bir yapı var, oraya yürüyeceğiz." Çocuk merakla dinliyor.
- İlk zorluk: Patika ikiye ayrılıyor; rehber haritada "şelale yönü"nü gösteriyor, çocuk doğru yolu seçiyor. İlk başarı.

### Bölüm 2 — Orman yürüyüşü, şelale (Sayfa 5-8)
- Ormanda yürüyüş. Çam ağaçları, kuş sesleri, serin hava. Rehber doğayı anlatıyor.
- Küçük görev: Rehber "Şelalenin sesini duyduk, hangi yönden geliyor?" diyor. Çocuk dinliyor, yönü buluyor. Şelaleyi görüyor. Keşif sevinci.
- Şelale manzarası, su sesi. "Ne güzel!" Doğa bilinci.

### Bölüm 3 — Taş basamaklar, tırmanış (Sayfa 9-12)
- Taş basamaklar başlıyor. Dik yokuş, yükseklik artıyor. Rehber: "Adım adım, güvenli gidelim."
- Zorluk: Bacaklar yoruluyor; çocuk "Biraz dinlenelim" diyor, rehber onaylıyor. Dinlenip tekrar yürüyor. Sebat.
- Her dönemde manzara genişliyor. "Neredeyse oradayız!" Cesaret.

### Bölüm 4 — Manastıra ulaşma, teras (Sayfa 13-16)
- Kayaya oyulmuş yapı görünüyor. Rehber: "1600 yıllık taş işçiliği, kapı yoktu burada evler kayaya oyulmuş."
- Küçük bulmaca: Rehber "Terası bulalım — nerede en iyi manzara var?" Çocuk etrafa bakıyor, terası/seyir noktasını buluyor. Başarı.
- Taş kemerler, odalar (içeride dini figür tasviri YOK — sadece mimari). "İnanılmaz yükseklikte!" Hayranlık.

### Bölüm 5 — 1200m manzara, dağ panoraması (Sayfa 17-19)
- Terastan vadi manzarası. Yeşil orman aşağıda, bulutlar yakın. Rehber rakımı anlatıyor: 1200m.
- Yoruluyor ama rehber "Son bir bakış, sonra inişe geçeceğiz" diyor. Çocuk manzarayı içine çekiyor. Tatmin.
- "Her zorluğu aştım, buraya kadar geldim!" Duygusal özet.

### Bölüm 6 — İniş, kapanış (Sayfa 20-22)
- İnişe başlama. Rehber dikkatli adım atmayı hatırlatıyor. Çocuk güvenle iniyor.
- Vadide son yürüyüş. Rehber tebrik ediyor: "Zorlukları aştın, Sümela'yı keşfettin."
- {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış.

---

## KURALLAR
- Rehber = gerçek insan (yüz detayı verme). Sihir, konuşan hayvan YOK.
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: Altındere Vadisi, orman, şelale, taş basamaklar, Sümela (mimari ve doğa).
- Dini figür (İsa, Meryem, aziz) tasviri YOK. Freskler uzaktan, figür detayı verme.
- Korku/tehlike yok; tırmanış rehberli ve güvenli.
- Kitap adı SADECE "[Çocuk adı]'ın Sümela Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""

OUTFIT_GIRL = (
    "dark emerald green waterproof rain jacket with hood, "
    "over cream white long-sleeve thermal shirt, dark navy blue hiking leggings, "
    "dark brown waterproof hiking boots with green laces, small olive green backpack. "
    "EXACTLY the same outfit on every page — same green jacket, same navy leggings, same brown boots."
)
OUTFIT_BOY = (
    "dark teal blue waterproof rain jacket with hood, "
    "over light gray long-sleeve thermal shirt, dark charcoal hiking pants, "
    "dark brown waterproof hiking boots with teal laces, small dark gray backpack. "
    "EXACTLY the same outfit on every page — same teal jacket, same charcoal pants, same brown boots."
)

COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Sumela Monastery carved into steep cliff face at 1200m in background. "
    "Lush green Altındere Valley forest, mist, mountain atmosphere. "
    "Wide shot: child 25%, monastery and nature 75%. Epic, adventurous."
)

PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Monastery: carved into cliff (1200m), stone arches / "
    "Cliff: steep rock face / Forest: green Altındere Valley, pine trees / "
    "Waterfalls: cascading water, mist / Path: stone steps climbing]. "
    "Nature colors: green, gray rock, white mist. NO religious figures, architecture and nature only."
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
            WHERE theme_key = 'sumela'
               OR theme_key = 'sumela_monastery_trabzon'
               OR name ILIKE '%Sümela%'
               OR name ILIKE '%Sumela%'
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
