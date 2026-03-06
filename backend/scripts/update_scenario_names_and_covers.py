"""
Senaryo İsim ve Kapak Promptu Güncellemesi
==========================================
Kitap başlığına uygun kısa senaryo isimleri + Umre kapak promptu düzeltmesi.

Çalıştırma:
    cd backend
    python -m scripts.update_scenario_names_and_covers
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# =============================================================================
# SENARYO İSİM GÜNCELLEMELERİ
# =============================================================================
# Format: (eski isim alt-string eşleşmesi, yeni isim)
# force_deterministic_title formatı: "{ÇocukAdı}'nın {SenaryoAdı}"
# Bu yüzden senaryo isimleri kısa ve temiz olmalı.

NAME_UPDATES: dict[str, str] = {
    # Eski substring (ilike) → Yeni isim
    "Umre Yolculuğu: Kutsal Topraklarda": "Umre Macerası",
    "Güneş Sistemi Macerası: Gezegen Kaşifleri": "Güneş Sistemi Macerası",
    "Okyanus Derinlikleri: Mavi Dev ile Macera": "Okyanus Macerası",
    "Kudüs Eski Şehir Macerası": "Kudüs Macerası",
    "Abu Simbel Tapınakları Macerası": "Abu Simbel Macerası",
    "Efes Antik Kent Macerası": "Efes Macerası",
    "Sultanahmet Camii Macerası": "Sultanahmet Macerası",
    "Çatalhöyük Neolitik Kenti Macerası": "Çatalhöyük Macerası",
    "Galata Kulesi Macerası": "Galata Macerası",
    "Sümela Manastırı Macerası": "Sümela Macerası",
    "Masal Dünyası Macerası": "Masal Dünyası",
    "Oyuncak Dünyası Macerası": "Oyuncak Dünyası",
    "Amazon Ormanları Keşfediyorum": "Amazon Macerası",
    "Dinozorlar Macerası: Zaman Yolculuğu": "Dinozorlarla Macerası",
    "Yerebatan Sarnıcı": "Yerebatan Macerası",
}

# =============================================================================
# UMRE KAPAK PROMPTU — Kabe önünde sahne (uçak yerine)
# =============================================================================

UMRE_COVER_PROMPT_NEW = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "The child stands in the white marble courtyard of Masjid al-Haram, "
    "directly facing the magnificent black Kaaba draped in golden Kiswah. "
    "Towering golden minarets and grand arched corridors frame the scene. "
    "Soft golden spiritual light bathes the courtyard. "
    "Wide shot: child 25%, grand Kaaba and mosque architecture 75%. "
    "NO Prophet/angel depictions."
)

# =============================================================================
# KUDÜS — İSLAMİ ODAKLI GÜNCELLEME
# =============================================================================

KUDUS_COVER_PROMPT_NEW = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "The child stands in the grand courtyard of Masjid al-Aqsa (Haram al-Sharif) "
    "with the magnificent golden Dome of the Rock (Qubbat al-Sakhra) gleaming behind. "
    "Ancient Ottoman stone arches, cypress trees, and warm Jerusalem limestone. "
    "Soft golden spiritual light fills the scene. "
    "Wide shot: child 25%, Masjid al-Aqsa and Dome of the Rock 75%. "
    "NO Prophet/angel depictions. Peaceful, reverent atmosphere."
)

KUDUS_PAGE_PROMPT_NEW = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Masjid al-Aqsa: grand silver-domed mosque / "
    "Dome of the Rock: golden dome, blue Ottoman tiles, octagonal shape / "
    "Haram al-Sharif courtyard: vast stone plaza, arched colonnades / "
    "Old City: narrow cobblestone alleys, golden Jerusalem stone / "
    "Souq bazaar: spices, copper lanterns, olive wood crafts / "
    "Ottoman walls: grand Damascus Gate entrance]. "
    "Warm golden light, spiritual, peaceful atmosphere."
)

KUDUS_STORY_PROMPT_TR_NEW = """
# KUDÜS MACERASı — PEYGAMBERLER ŞEHRİNDE MANEVİ YOLCULUK

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir manevi keşif macerası. {child_name}, Kudüs'te
bir Bilge Güvercin (Mescid-i Aksa avlusunda yaşayan, nesillerdir
bu kutsal toprakların tanığı kadim bir güvercin) ile birlikte
İslam'ın üçüncü kutsal mescidini ve peygamberler şehrini keşfeder.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, din dersi DEĞİL
- Bilgiler çocuğa uygun, basit ve merak uyandıran tarzda verilmeli
- Her bölümde çocuk AKTİF katılımcı
- Yardımcı karakter: Bilge Güvercin (Mescid-i Aksa'nın kadim güvercini)
- Peygamber görseli YOK (sadece hikaye anlatımı ile aktarılır)
- Korku/şiddet YOK
- Her sayfa İslami değer ve bilgi içermeli (mimari, tarih, manevi anlam)
- Mescid-i Aksa ve Kubbetüs-Sahra MERKEZ noktalar
- Selahaddin Eyyubi'nin adaleti ve cesareti vurgulanmalı

---

### BÖLÜM 1 — GİRİŞ: KUTSAL TOPRAKLARA VARIŞ (Sayfa 1-4)
{child_name} Kudüs surlarının önüne geliyor. Dev Osmanlı surları,
Şam Kapısı'nın muhteşem kemeri. Bilge Güvercin kapının üstünden
süzülüp iniyor. "Hoş geldin peygamberler şehrine! Burada
Hz. İbrahim, Hz. Davud, Hz. Süleyman ve Hz. İsa yürüdü.
Peygamber Efendimiz Hz. Muhammed (s.a.v) buraya geldi. Gel, göstereyim!"
- S1: Şam Kapısı'na varış, Osmanlı surlarının ihtişamı
- S2: Eski Şehir'e giriş — dar taş sokaklar, altın rengi Kudüs taşı
- S3: Bilge Güvercin ile tanışma — "Peygamberler şehrine hoş geldin!"
- S4: İlk bakış: Uzaktan Kubbetüs-Sahra'nın altın parıltısı ✓ İLK HAYRANLIK
**Değer**: Manevi merak, peygamberlere saygı

---

### BÖLÜM 2 — MESCİD-İ AKSA: İLK KİBLEMİZ (Sayfa 5-8)
Bilge Güvercin çocuğu Harem-i Şerif avlusuna götürüyor. Geniş
taş avlu, zeytin ağaçları, kemerli revaklar. Mescid-i Aksa'nın
gümüş kubbesi görünüyor! "Bu mescid Müslümanların ilk kıblesiydi!
Peygamber Efendimiz ve sahabeler önce buraya yönelerek namaz kıldılar."
İçeri giriyorlar — devasa sütunlar, muhteşem halılar, huzurlu ortam.
- S5: Harem-i Şerif avlusuna giriş — geniş taş meydan
- S6: Mescid-i Aksa'nın gümüş kubbesi — "İlk kiblemiz!" ✓ MANEVİ ZİRVE
- S7: İçeri giriş — dev sütunlar, kemerleri 1400 yıllık mimari
- S8: Bilge Güvercin anlatıyor — "Peygamber Efendimiz burada imamlık yaptı"
**Değer**: İlk kıble bilgisi, namaz sevgisi, İslami mimari

---

### BÖLÜM 3 — KUBBETÜS-SAHRA: MİRAÇ NOKTASI (Sayfa 9-12)
Altın Kubbe'ye doğru yürüyorlar! Kubbetüs-Sahra güneşte parlıyor —
sekizgen yapı, mavi Osmanlı çinileri, altın kubbe. Bilge Güvercin:
"İşte burası! Peygamber Efendimiz bir gece Mekke'den buraya
geldi — buna İsra denir. Sonra tam bu noktadan göklere yükseldi —
buna da Miraç denir. O gece beş vakit namaz hediye edildi!"
- S9: Kubbetüs-Sahra'ya yaklaşma — altın parıltı
- S10: Sekizgen yapı, mavi çiniler — "İnanılmaz güzel!" ✓ MİMARİ ZİRVE
- S11: İsra ve Miraç hikayesi — "Bu noktadan göklere yükseldi!"
- S12: Miraç'ın hediyesi: beş vakit namaz — "Ne güzel bir hediye!" ✓ MANEVİ DORUK
**Değer**: İsra ve Miraç bilgisi, namazın önemi, İslami mimari

---

### BÖLÜM 4 — SELAHADDİN EYYUBİ: ADALETİN KAHRAMANI (Sayfa 13-16)
Bilge Güvercin çocuğu surların yanındaki Selahaddin Eyyubi
anıtına götürüyor. "800 yıl önce kahraman Selahaddin Eyyubi
Kudüs'ü fethetti. Ama bilir misin ne yaptı? Kimseye zarar vermedi,
herkese adaletle davrandı, herkesin ibadet etmesine izin verdi!"
Çarşıda Selahaddin döneminden kalma Osmanlı mimarisi.
- S13: Selahaddin Eyyubi anıtı — "Adaletin kahramanı!"
- S14: Fetih hikayesi — "Kimseye zarar vermeden!"  ✓ ADALET ZİRVESİ
- S15: Osmanlı çarşısı — baharat, bakır fenerler, zeytinyağı sabunları
- S16: El sanatı öğrenme — zeytin ağacı tespih yapma ✓ BAŞARI HİSSİ
**Değer**: Adalet, merhamet, hoşgörü, İslami ahlak

---

### BÖLÜM 5 — ÇARŞI VE ZEYTİN DAĞI (Sayfa 17-19)
Baharat çarşısında dolaşıyorlar. Zerdeçal, zahter, sumak...
Sonra Zeytin Dağı'na çıkıyorlar — tüm Kudüs ayakların altında!
Bilge Güvercin: "Buradan Hz. Ömer şehre baktığında, kiliselere
ve insanlara saygı gösterdi. İslam'da adalet herkes içindir."
- S17: Baharat çarşısı — renkler ve kokular
- S18: Zeytin Dağı'na çıkış — panoramik Kudüs manzarası ✓ PANORAMA DORUĞU
- S19: Mescid-i Aksa ve Kubbetüs-Sahra yukarıdan — "Nefes kesici!"
**Değer**: İslami adalet, doğa güzelliği, tarih

---

### BÖLÜM 6 — BURAK MESCİDİ VE HATIRALARI (Sayfa 20-21)
Bilge Güvercin gizli bir geçitten Burak Mescidi'ne götürüyor.
"Peygamber Efendimiz İsra gecesi Burak'ını burada bağladı!"
Antik taş duvarlar, mumlerin titrek ışığı. Çocuk duvarların
taşlarına dokunuyor — "Binlerce yıllık tarih ellerimin altında!"
- S20: Burak Mescidi — "Peygamberimiz burada!" ✓ MANEVİ DORUK
- S21: Antik taşlara dokunma — tarihin tanığı olma
**Değer**: Peygamber sevgisi, tarih bilinci

---

### BÖLÜM 7 — FİNAL: DUALARIN ŞEHRİ (Sayfa 22)
Mescid-i Aksa avlusuna dönüş. Gün batımı, altın ışık.
Bilge Güvercin: "Bu şehir sana ne öğretti?"
Çocuk: "Peygamberlerimizin izinden yürüdüm. Adalet,
merhamet ve barışın ne kadar önemli olduğunu öğrendim."
Bilge Güvercin kubbe etrafında süzülüyor — huzur ve minnet.
- S22: Gün batımında Mescid-i Aksa — dua ve minnet ✓ TATMIN DORUĞU
**Değer**: Şükür, dua, İslami değerler

---

## GÜVENLİK KURALLARI:
- Peygamber görseli YOK (sadece hikaye anlatımı)
- Korku/şiddet/gore YOK
- Siyasi mesaj YOK
- Her bilgi çocuğa uygun, basit ve merak uyandıran
- İslami değerler: adalet, merhamet, ilim, sabır
- Mescid-i Aksa ve Kubbetüs-Sahra her bölümde mevcut
"""

KUDUS_CUSTOM_INPUTS_NEW = [
    {
        "key": "favorite_place",
        "label": "En Merak Ettiği Kutsal Mekan",
        "type": "select",
        "options": [
            "Mescid-i Aksa",
            "Kubbetüs-Sahra (Altın Kubbe)",
            "Burak Mescidi",
            "Selahaddin Eyyubi Anıtı",
            "Zeytin Dağı Manzarası",
        ],
        "default": "Mescid-i Aksa",
        "required": False,
        "help_text": "Hikayede en çok vakit geçireceği kutsal mekan",
    },
    {
        "key": "special_discovery",
        "label": "Öğrenmek İstediği Konu",
        "type": "select",
        "options": [
            "İsra ve Miraç Mucizesi",
            "Selahaddin Eyyubi'nin Adaleti",
            "Kudüs'ün Peygamberleri",
            "İslami Mimari ve Çiniler",
            "Osmanlı Dönemi Kudüs",
        ],
        "default": "İsra ve Miraç Mucizesi",
        "required": False,
        "help_text": "Hikayede çocuğun en çok ilham alacağı konu",
    },
]

KUDUS_CULTURAL_ELEMENTS_NEW = {
    "location": "Kudüs / Al-Quds — İslam'ın 3. Kutsal Şehri",
    "islamic_significance": (
        "Müslümanların ilk kıblesi. Mekke ve Medine'den sonra "
        "İslam'ın en kutsal 3. mescidi. İsra ve Miraç mucizesinin noktası."
    ),
    "key_sites": [
        "Mescid-i Aksa — İslam'ın 3. kutsal mescidi, gümüş kubbe",
        "Kubbetüs-Sahra — Miraç noktası, altın kubbe, mavi Osmanlı çinileri",
        "Burak Mescidi — İsra gecesi Burak'ın bağlandığı yer",
        "Harem-i Şerif — 144 dönümlük kutsal alan",
        "Şam Kapısı — Osmanlı surlarının muhteşem girişi",
        "Selahaddin Eyyubi Anıtı — İslam adaletinin sembolü",
        "Zeytin Dağı — Kudüs panoraması",
    ],
    "prophets": "Hz. İbrahim, Hz. Davud, Hz. Süleyman, Hz. İsa, Hz. Muhammed (s.a.v)",
    "islamic_values": ["Adalet", "Merhamet", "İlim", "Sabır", "Hoşgörü", "Namaz"],
    "architecture": [
        "Osmanlı surları (Kanuni Sultan Süleyman)",
        "Kubbetüs-Sahra: sekizgen, mavi çini, altın kubbe",
        "Mescid-i Aksa: dev sütunlar, gümüş kubbe",
        "Kemerli revaklar, zeytin ağaçları, Kudüs taşı",
    ],
    "atmosphere": "Manevi, huzurlu, altın ışık, tarihî",
    "color_palette": "Kudüs altın taşı, kubbe altını, çini mavisi, zeytin yeşili",
}


async def update_scenario_names_and_covers():
    """Senaryo isimlerini ve Umre kapak promptunu günceller."""

    print("\n" + "=" * 70)
    print("📝 SENARYO İSİM VE KAPAK PROMPTU GÜNCELLEMESİ")
    print("=" * 70)

    async with async_session_factory() as db:
        result = await db.execute(select(Scenario))
        scenarios = list(result.scalars().all())

        print(f"\n📊 Toplam {len(scenarios)} senaryo bulundu.\n")

        updated_names = 0
        updated_covers = 0

        for scenario in scenarios:
            old_name = scenario.name or ""

            # İsim güncellemesi
            for old_match, new_name in NAME_UPDATES.items():
                if old_match.lower() in old_name.lower() or old_name == old_match:
                    print(f"  📝 İsim: '{old_name}' → '{new_name}'")
                    scenario.name = new_name
                    updated_names += 1
                    break

            # Umre kapak promptu güncellemesi
            if "umre" in (scenario.theme_key or "").lower() or "umre" in (scenario.name or "").lower():
                print(f"  🕋 Umre kapak promptu güncelleniyor: {scenario.name}")
                scenario.cover_prompt_template = UMRE_COVER_PROMPT_NEW
                updated_covers += 1

            # Uzay kıyafetlerinde NASA → Türkiye bayrağı
            if "uzay" in (scenario.theme_key or "").lower() or "güneş" in (scenario.name or "").lower() or "space" in (scenario.theme_key or "").lower():
                print(f"  🚀 Uzay kıyafeti güncelleniyor (Türkiye bayrağı): {scenario.name}")
                scenario.outfit_girl = (
                    "bright white child space suit with red crescent-and-star Turkish flag patch on left shoulder, "
                    "blue mission patch on right shoulder, silver metallic utility belt with small gadget pouches, "
                    "white space boots with pink soles, clear bubble space helmet with pink frame "
                    "(helmet can be removed in indoor scenes), small silver star-shaped badge on chest. "
                    "EXACTLY the same outfit on every page — same white space suit with Turkish flag patch, same silver belt, same white boots. "
                    "NO American flag, NO NASA logo, NO USA patches."
                )
                scenario.outfit_boy = (
                    "bright white child space suit with red crescent-and-star Turkish flag patch on left shoulder, "
                    "blue mission patch on right shoulder, silver metallic utility belt with small gadget pouches, "
                    "white space boots with blue soles, clear bubble space helmet with blue frame "
                    "(helmet can be removed in indoor scenes), small gold rocket-shaped badge on chest. "
                    "EXACTLY the same outfit on every page — same white space suit with Turkish flag patch, same silver belt, same white boots. "
                    "NO American flag, NO NASA logo, NO USA patches."
                )
                updated_covers += 1

            # Kudüs senaryosu — İslami odaklı güncelleme
            if "kudus" in (scenario.theme_key or "").lower() or "kudüs" in (scenario.name or "").lower() or "jerusalem" in (scenario.theme_key or "").lower():
                print(f"  🕌 Kudüs senaryosu güncelleniyor (İslami odak): {scenario.name}")
                scenario.cover_prompt_template = KUDUS_COVER_PROMPT_NEW
                scenario.page_prompt_template = KUDUS_PAGE_PROMPT_NEW
                scenario.story_prompt_tr = KUDUS_STORY_PROMPT_TR_NEW
                scenario.custom_inputs_schema = KUDUS_CUSTOM_INPUTS_NEW
                scenario.cultural_elements = KUDUS_CULTURAL_ELEMENTS_NEW
                scenario.description = (
                    "Peygamberler şehri Kudüs'te manevi bir yolculuk! "
                    "Mescid-i Aksa, Kubbetüs-Sahra, İsra ve Miraç hikayesi. "
                    "İslam'ın üçüncü kutsal mescidinde ilham dolu bir macera."
                )
                scenario.marketing_badge = "Manevi Keşif"
                scenario.tagline = "Peygamberler şehrinde manevi bir yolculuk"
                updated_covers += 1

        await db.commit()

        print("\n" + "=" * 70)
        print(f"📊 SONUÇ:")
        print(f"   📝 İsim güncelleme: {updated_names}")
        print(f"   🕋 Kapak/senaryo: {updated_covers}")
        print("=" * 70)

        # Sonuçları listele
        print("\n📋 Güncel Senaryo İsimleri:")
        result2 = await db.execute(select(Scenario).order_by(Scenario.display_order))
        for s in result2.scalars().all():
            book_title_example = f"Ali'nin {s.name}"
            print(f"   {s.display_order:>2}. {s.name:<35} → Kitap: \"{book_title_example}\"")

        print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(update_scenario_names_and_covers())

