"""
Masal Dünyası Macerası — Meşhur masal ve çizgi film kahramanlarıyla macera
==========================================================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Outfit: EXACTLY lock phrase
- Blueprint hikaye (bölüm bölüm, dopamin döngüsü)
- Çocuk TEK BAŞINA (aile yok)
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

FAIRY_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Enchanted fairy tale kingdom: glowing mushroom forest, crystal castle towers, "
    "rainbow bridge over sparkling river, flying books with golden pages. "
    "Soft magical glow, storybook illustration style. "
    "Wide shot: child 30%, fairy tale world 70%. "
    "Dreamy, enchanted atmosphere."
)

FAIRY_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Mushroom forest: giant glowing caps, fairy lights / "
    "Crystal castle: glass towers, floating stairs / "
    "Enchanted library: flying books, golden ink / "
    "Dragon meadow: friendly baby dragons, flower fields / "
    "Rainbow bridge: sparkling arch over river]. "
    "Soft pastels: lavender, rose gold, mint, pearl white."
)

# ============================================================================
# OUTFIT DEFINITIONS
# ============================================================================

OUTFIT_GIRL = (
    "shimmering lilac purple dress with golden star patterns along the hem, "
    "white tights, soft gold ballet flats with small bow, "
    "thin silver headband with tiny crystal star, small velvet purple satchel. "
    "EXACTLY the same outfit on every page — same lilac dress, same gold flats, same silver headband."
)

OUTFIT_BOY = (
    "deep emerald green velvet vest over crisp white cotton shirt with rolled sleeves, "
    "dark brown corduroy pants, polished brown leather boots with brass buckles, "
    "small brown leather messenger bag across body. "
    "EXACTLY the same outfit on every page — same green vest, same white shirt, same brown boots."
)

# ============================================================================
# STORY BLUEPRINT
# ============================================================================

FAIRY_STORY_PROMPT_TR = """
# MASAL DÜNYASI MACERASI — HİKÂYELERİN KALBİNDE

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir fantastik macera. {child_name}, eski bir masal kitabını
açınca sayfaların içine çekilir ve kendini Masal Dünyası'nda bulur.
Rehberi: Hikâye Perisi (kitaptan çıkan, parlayan, bilge bir peri —
tüm masalları bilen, küçük, kanatları kitap sayfalarından yapılmış).

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, masal özeti DEĞİL
- Her bölümde çocuk AKTİF katılımcı (izleyici değil)
- Endişe → Eylem → Başarı döngüsü
- Yardımcı karakter: Hikâye Perisi (kitap kanatlı, bilge)
- Çocuk TEK BAŞINA macerada (aile yok). Anne-baba-aile karakteri KULLANMA.
- Korku/şiddet YOK
- Telif haklı karakterler KULLANMA (Disney, Marvel vb.)
- Bunun yerine arketip kahramanlar kullan: Cesur Şövalye, Bilge Ejderha,
  Uçan Halı Prensi, Deniz Kızı, Cüce Ustalar, Dev Ama İyi Kalpli
- Her masal dünyasında çocuk bir SORUNU çözer

---

### BÖLÜM 1 — GİRİŞ: KİTABIN İÇİNE DÜŞÜŞ (Sayfa 1-4)
{child_name} eski bir kitapçıda parlayan bir masal kitabı buluyor.
Kitabı açınca sayfalar rüzgârla dönmeye başlıyor, harfler havada
uçuşuyor! Bir ışık çocuğu içine çekiyor. Hikâye Perisi: "Hoş geldin!
Masal Dünyası'nın hikâyeleri karışmış. Düzeltmemiz lazım!"
- S1: Eski kitapçı, tozlu raflar, parlayan kitap
- S2: Kitap açılıyor — harfler havada uçuşuyor!
- S3: Işık çocuğu içine çekiyor — Masal Dünyası! ✓ İLK HEYECAN
- S4: Hikâye Perisi: "Hikâyeler karışmış!" — görev başlıyor
**Değer**: Merak, okuma sevgisi

---

### BÖLÜM 2 — MANTAR ORMANI: CÜCELERİN ATÖLYES İ (Sayfa 5-8)
Dev parlayan mantarların altında Cüce Ustalar yaşıyor. Ama atölyeleri
karışmış — aletler yanlış yerlerde, tarifler kayıp! Çocuk onlara
yardım ederek atölyeyi düzenliyor. Cüceler teşekkür olarak sihirli
bir anahtar veriyor.
- S5: Dev mantar ormanı — parlak, renkli
- S6: Cüce Ustalar — "Atölyemiz karışmış!" ✓ ENDİŞE
- S7: Aletleri doğru yere koyma, tarifleri eşleştirme
- S8: Atölye düzenlendi! Sihirli anahtar ödülü ✓ BAŞARI
**Değer**: Düzen, yardımlaşma, el becerisi

---

### BÖLÜM 3 — KRİSTAL KALE: CESUR ŞÖVALYE (Sayfa 9-12)
Kristal kuleleri olan görkemli kale. Cesur Şövalye zırhını kaybetmiş,
kendine güveni yok. "Zırhım olmadan cesur olamam!" Çocuk ona cesaretin
içten geldiğini gösteriyor — birlikte bir bulmacayı çözüyorlar.
- S9: Kristal kale — cam kuleler, yüzen merdivenler
- S10: Cesur Şövalye zırhsız, üzgün ✓ ENDİŞE
- S11: "Cesaret zırhta değil, kalpte!" — birlikte bulmaca
- S12: Şövalye cesaret buluyor! İkinci anahtar ✓ BAŞARI
**Değer**: Özgüven, cesaret, iç güç

---

### BÖLÜM 4 — EJDERHA ÇAYIRI: BİLGE EJDERHA (Sayfa 13-16)
Çiçekli çayırda küçük, sevimli ejderhalar yaşıyor. Bilge Ejderha
(yaşlı, gözlüklü, kitap okuyan) çocuğa bir bilmece soruyor:
"Herkes taşır ama kimse göremez. Nedir?" Cevap: HİKÂYE!
Her insanın içinde bir hikâye var.
- S13: Çiçekli çayır — bebek ejderhalar oynuyor
- S14: Bilge Ejderha — gözlüklü, kitap okuyor ✓ HAYRANLIK
- S15: Bilmece — "Herkes taşır ama kimse göremez?" ✓ MERAK ZİRVESİ
- S16: "HİKÂYE!" — üçüncü anahtar ✓ BAŞARI
**Değer**: Bilgelik, hikâye anlatma, hayal gücü

---

### BÖLÜM 5 — GÖKKUŞAĞI KÖPRÜSÜ: DENİZ KIZI (Sayfa 17-19)
Parlayan gökkuşağı köprüsü bir nehrin üzerinde. Nehirde Deniz Kızı
şarkı söylüyor ama sesi çıkmıyor — sihri bozulmuş. Çocuk üç
anahtarı birleştirerek Deniz Kızı'nın sesini geri getiriyor.
Muhteşem şarkı tüm Masal Dünyası'nda yankılanıyor!
- S17: Gökkuşağı köprüsü — parlak, büyülü
- S18: Deniz Kızı sessiz, üzgün ✓ ENDİŞE
- S19: Üç anahtar birleşiyor — şarkı geri geliyor! ✓ BÜYÜ ZİRVESİ
**Değer**: Yardım, müzik, empati

---

### BÖLÜM 6 — UÇAN KİTAPLAR KÜTÜPHANESİ: HİKÂYELER DÜZELİYOR (Sayfa 20-21)
Devasa kütüphane — kitaplar havada uçuyor, sayfalar kendiliğinden
yazılıyor. Hikâye Perisi: "Şarkı tüm hikâyeleri uyandırdı! Ama
son bir şey eksik — SENİN hikâyen." Çocuk kendi hikâyesini anlatıyor
ve kitaba yazılıyor!
- S20: Uçan kitaplar kütüphanesi — görkemli, büyülü
- S21: "SENİN hikâyen!" — çocuğun hikâyesi kitaba yazılıyor ✓ DORUK
**Değer**: Özgünlük, kendini ifade, yaratıcılık

---

### BÖLÜM 7 — FİNAL: KİTAPTAN DÖNÜŞ (Sayfa 22)
Kitabın sayfaları tekrar dönmeye başlıyor. Çocuk kitapçıya geri
dönüyor. Elinde masal kitabı — ama artık içinde çocuğun kendi
hikâyesi de var! Hikâye Perisi kitabın kapağından göz kırpıyor.
- S22: Kitapçıya dönüş, kitap elde, gülümseme ✓ TATMİN DORUĞU
**Değer**: Okuma sevgisi, hayal gücü, hikâyenin gücü

---

## DOPAMİN ZİRVELERİ:
1. S3: Kitabın içine çekilme
2. S8: Cüce atölyesi düzenlendi — sihirli anahtar
3. S12: Şövalye cesaret buldu — ikinci anahtar
4. S15: Bilge Ejderha bilmecesi
5. S19: Deniz Kızı'nın şarkısı geri geldi
6. S21: Çocuğun kendi hikâyesi kitaba yazıldı
7. S22: Peri göz kırpıyor — büyü gerçekti!

## GÜVENLİK KURALLARI:
- Korku/şiddet YOK (kötü karakter YOK, ejderhalar SEVİMLİ)
- Telif haklı karakter KULLANMA
- Çocuk TEK BAŞINA (aile yok)
- Pozitif, büyülü, hayal gücü odaklı atmosfer

Hikayeyi {page_count} sayfaya yaz. Her sayfa 2-4 cümle (40-80 kelime).
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

FAIRY_CULTURAL_ELEMENTS = {
    "location": "Magical Fairy Tale World (fantasy realm inside a book)",
    "story_archetypes": [
        "Brave Knight (lost armor, finds inner courage)",
        "Wise Dragon (old, bespectacled, riddle-loving)",
        "Dwarf Craftsmen (workshop, tools, recipes)",
        "Mermaid (singing, enchanted voice)",
        "Story Fairy (book-winged, wise guide)",
        "Flying Books (sentient, golden pages)",
    ],
    "atmosphere": "Enchanted, dreamy, warm, storybook illustration, magical glow",
    "color_palette": "lavender, rose gold, mint green, pearl white, soft gold, crystal blue",
    "values": ["Reading", "Imagination", "Courage", "Self-expression", "Empathy"],
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

FAIRY_CUSTOM_INPUTS = [
    {
        "key": "favorite_character",
        "label": "En Sevdiği Masal Kahramanı",
        "type": "select",
        "options": ["Cesur Şövalye", "Bilge Ejderha", "Deniz Kızı", "Cüce Ustalar", "Hikâye Perisi"],
        "default": "Bilge Ejderha",
        "required": False,
        "help_text": "Hikayede çocuğun en çok vakit geçireceği karakter",
    },
    {
        "key": "fairy_mission",
        "label": "Masal Görevi",
        "type": "select",
        "options": ["Karışan Hikâyeleri Düzelt", "Kayıp Şarkıyı Bul", "Kristal Kaleyi Koru", "Ejderha Bilmecesini Çöz"],
        "default": "Karışan Hikâyeleri Düzelt",
        "required": False,
        "help_text": "Hikayenin ana macera görevi",
    },
]

# ============================================================================
# DATABASE FUNCTION
# ============================================================================


async def create_fairy_tale_scenario():
    """Masal Dünyası senaryosunu oluşturur veya günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "fairy_tale_world")
                | (Scenario.name.ilike("%Masal D%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Masal Dünyası Macerası"
        scenario.thumbnail_url = ""
        scenario.description = (
            "Eski bir masal kitabının içine çekilip büyülü bir dünyada maceraya atıl! "
            "Cesur Şövalye, Bilge Ejderha, Cüce Ustalar ve Deniz Kızı ile birlikte "
            "karışan hikâyeleri düzelt ve kendi hikâyeni yaz!"
        )
        scenario.theme_key = "fairy_tale_world"
        scenario.cover_prompt_template = FAIRY_COVER_PROMPT
        scenario.page_prompt_template = FAIRY_PAGE_PROMPT
        scenario.story_prompt_tr = FAIRY_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = FAIRY_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = FAIRY_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Büyülü Macera"
        scenario.age_range = "4-8"
        scenario.tagline = "Hikâyelerin kalbine yolculuk!"
        scenario.is_active = True
        scenario.display_order = 18

        await db.commit()
        print(f"Masal Dünyası scenario created/updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_fairy_tale_scenario())
