"""
Çatalhöyük'ün Çatı Yolu — Zaman Yolculuğu, Macera, Indiana Jones Tarzı
==================================================================================
- Kitap adı: [Çocuk adı]'ın Çatı Yolu: Çatalhöyük (alt başlık yok)
- Zaman yolculuğu ile 9000 yıllık Neolitik köye gidiş ve duman krizini (küçük yangın) çözme macerası
- Yerler: höyük, kerpiç evler, damdan geçiş labirentleri, ocaklar, toprak kaplar
- Kıyafet: Neolitik arkeolog tarzı, kız ve erkek için zorunlu ve her sayfada aynı tutarlı (kıyafet kilidi)
- Companion: Köy Köpeği (default) + 3 ek seçenek (Neolitik Keçi, Step Kartalı, Yabani Kedi)

Scenario Master M2 İyileştirmeleri (2026-03-12):
  - Companion visual lock çatışması giderildi (scenario_bible ↔ _COMPANION_MAP uyumu)
  - Companion seçenek sayısı 1 → 4'e çıkarıldı
  - story_prompt_tr'ye DOĞRU/YANLIŞ örnekleri + companion tutarlılık uyarısı eklendi
  - Kültürel mekan sayısı 8 → 10'a çıkarıldı (obsidyen atölyesi, tahıl depolama)
  - Script DB verisiyle senkronize edildi
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(override=True)

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (AI DIRECTOR - PASS 2)
# ============================================================================

CATALHOYUK_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child holding a glowing earthy ancient amulet with spiral carvings pulsing warm amber light. "
    "Ancient 9000-year-old Catalhoyuk Neolithic settlement spreading behind — clustered mud-brick houses with flat rooftops, wooden ladder entrances, cracked sun-dried clay walls with faded ochre wall paintings. "
    "A glowing turquoise time-rift crack splitting the dramatic evening sky above the settlement, volumetric dust motes swirling in the warm steppe wind. "
    "Low-angle hero shot: child 30% foreground, vast ancient archaeological site 70%. "
    "Prehistoric palette: warm mud brown, deep ochre, burnt terracotta, amber amulet glow, turquoise rift light."
)

CATALHOYUK_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Setting elements (choose based on scene description): "
    "MUSEUM: modern museum interior, glass display cases, soft lighting. "
    "ROOFTOPS: ancient mud-brick houses, flat roofs, wooden ladders, no streets, smoky air. "
    "INTERIOR: dark earthy room, clay pots, glowing hearth, faded ochre wall paintings, smoke. "
    "Shot variety (alternate each page — never repeat same angle twice in a row): "
    "[CLOSE-UP: glowing earthy ancient amulet / child's determined face / throwing clay] "
    "[MEDIUM: child interacting with villagers / climbing a wooden ladder / waist-up action] "
    "[WIDE: epic panorama of ancient 9000-year-old Catalhoyuk Neolithic settlement / jumping between mudbrick roofs] "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. "
    "Child 30-40% of frame. No eye contact. "
    "Earthy colors: mud brown, ochre, terracotta, amber amulet glow, turquoise rift light."
)

# ============================================================================
# OUTFIT — Neolitik Arkeolog Kıyafet Kilidi (Sabit ve Zorunlu)
# ============================================================================

OUTFIT_GIRL = (
    "a striking crimson linen tunic over a long-sleeved cream shirt, "
    "tailored charcoal-grey climbing pants, rugged desert boots, "
    "a braided leather belt with small pouches, "
    "and a glowing ancient stone amulet around the neck. "
    "NO other clothing. EXACTLY the same outfit on every page — "
    "same crimson tunic, same amulet, same climbing pants. "
    "No outfit changes. NO skirts or shorts. "
    "Same child character, consistent face and hair across all pages."
)

OUTFIT_BOY = (
    "a striking burnt-orange linen tunic over a long-sleeved dark shirt, "
    "tailored charcoal-grey climbing pants, rugged desert boots, "
    "a braided leather belt with small pouches, "
    "and a glowing ancient stone amulet around the neck. "
    "NO other clothing. EXACTLY the same outfit on every page — "
    "same orange tunic, same amulet, same climbing pants. "
    "No outfit changes. NO short shorts. "
    "Same child character, consistent face and hair across all pages."
)

# ============================================================================
# STORY BLUEPRINT — Zaman Yolculuğu ve Çatı Macerası (PURE AUTHOR - PASS 1)
# ============================================================================

CATALHOYUK_STORY_PROMPT_TR = """
# ÇATALHÖYÜK'ÜN ÇATI YOLU: NEOLİTİK MACERA

## YAPI: {child_name} Indiana Jones tarzı kıyafetleriyle bir müzede eski bir tılsım/amulet bularak zaman yolculuğu yapar ve 9000 yıllık Neolitik Çatalhöyük köyünde gerçek bir duman (küçük yangın) krizini çözer. Heyecan, labirent gibi çatılarda yol bulma, zeka ve adrenalin içerir. Korkutucu veya kanlı DEĞİL, risk var ama güvenli tonda anlatılmalı.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Çatı Yolu: Çatalhöyük" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. 
- Dili akıcı, ritimli ve 5-10 yaş aralığında merak uyandırıcı olmalıdır. 
- Bilgi yığını yapma; Çatalhöyük detaylarını (damdan giriş, sokaksızlık, bitişik evler) maceranın içinde doğal bir zorluk/mekan gibi kullan.
- Her sayfa veya bölüm sonunda hafif bir merak (cliffhanger) hissi bırak.

---

### Bölüm 1 — Gizemli Tılsım (Sayfa 1-3)
- Sayfa 1: {child_name} müzedeki (Ziyaretçi Merkezi) ziyaretini bitirirken köşede, unutulmuş tozlu bir kutunun içinde toprağa bulanmış tuhaf bir taş amulet bulur. "Bunu kim unutmuş olabilir?" diyerek meraklanır.
- Sayfa 2: Amuletin üzerindeki tozu siler silmez üzerinde spiral ve ok benzeri eski semboller belirir. Taş aniden avucunda hafifçe ısınır. {child_name} kalp atışlarını duyarak taşı çantasına koyar.
- Sayfa 3: Çatalhöyük kazı alanında gezerken rüzgar aniden toz kaldırır; çantasının içinden incecik bir 'tık tık' sesi gelmektedir. Amuletteki semboller, sanki yerdeki şekillerle eşleşip ona gizli bir yol gösteriyor gibidir.

### Bölüm 2 — Zaman Geçidi (Sayfa 4-6)
- Sayfa 4: Kerpiç evlerin aslına uygun kopyalarının (rekonstrüksiyon) olduğu bölümde, bir ev duvarında minik bir niş (oyuk) fark eder. Oyuğun şekli çantasındaki taşın şekliyle birebir aynıdır. {child_name} nefesini tutar.
- Sayfa 5: Tereddütle amuleti nişe yerleştirir. O anda müthiş bir toz dansı başlar, havayı keskin bir "Vıın!" sesi kaplar ve çevredeki ışıklar bir anda söner. Değişen şey zemin değildir, sanki bizzat zamandır...
- Sayfa 6: Gözlerini açtığında karşısında 9000 yıl öncesinin gerçek Neolitik Çatalhöyük'ü vardır: sımsıkı bitişik toprak renkli evler, çatılarda çalışan insanlar ve havada yoğun bir ocak dumanı kokusu. "Burası... çok eski!" diye fısıldar şok içinde.

### Bölüm 3 — Çatı Labirenti ve Kriz (Sayfa 7-9)
- Sayfa 7: Çatılardan birinden Neolitik çağda yaşayan bir çocuğun panik dolu bağırışı duyulur: "Duman! Bir evin içi duman doluyor!" Köyde küçük bir ateş kontrolden çıkmıştır.
- Sayfa 8: {child_name} hızla merdiveni tırmanıp çatılara fırlar. Ancak sokak yoktur! Evlerin çatılarından atlayarak ilerlemek zorundadır ve labirent gibi dizilmiş bu köyde yön bulmak bir bulmacaya dönüşür.
- Sayfa 9: Amuletindeki sembollerin, çatı geçişlerine önceden çizilmiş eski yön işaretleriyle eşleştiğini fark eder (spiral = sağ, düz çizgi = ileri). Antik bulmacayı okuyarak dumanın kaynağına doğru koşmaya başlar.

### Bölüm 4 — Dumana Müdahale (Sayfa 10-13)
- Sayfa 10: Doğru çatıyı bulur fakat evin tek giriş deliği olan dar kapaktan dışarıya göz yaşartan bir duman çıkmaktadır. Geri çekilir, içinden "Bir yolunu bulmalıyım!" diye geçirir.
- Sayfa 11: Çatının kenarında dizili toprak kil testileri ve kurumuş keten bezleri gözüne çarpar. Amacı dumanı azaltıp aşağıda, dumanın içinde kalmış olan önemli bir erzağı (yiyecek sepetini) kurtarmaktır.
- Sayfa 12: Islak bezi yüzüne sararak nefes almayı kolaylaştırır ve yanındaki yetişkin bir köylüden işaretlerle yardım ister. Ancak o an yaşlılardan biri çantasındaki amuleti fark edip "O işaret kutsal!" diye bağırır.
- Sayfa 13: Yanlış anlaşıldığını fark eder, bazıları onu durdurmak ister. {child_name} hızla amuletindeki işaretleri gösterip taş devrinin basit el kol hareketleriyle "Size yardım etmeye geldim!" demek istercesine göğsüne vurur.

### Bölüm 5 — Zekice Çözüm (Sayfa 14-17)
- Sayfa 14: Damdan aşağı evin içine süzülür. Dumanın kaynağını tespit eder: Ortadaki büyük ocak devrilmiş, korlar kurumuş sazlardan örülü hasıra sıçramıştır. Susuzluktan dolayı suyu harcamadan, zemindeki kili-toprağı kullanarak ateşi boğma fikri aklına gelir.
- Sayfa 15: Yetişkin köylüyle omuz omuza verip üstüne toprak/kil atarak korları tamamen söndürürler. Fakat yeni bir sorun baş göstermiştir; içeride sıkışan duman yandaki bağlantılı odaya doğru akıyordur!
- Sayfa 16: Odanın üst köşesinde kapalı bir havalandırma deliği olduğunu tahmin eder çünkü amuletindeki yıldızvari sembol "açıklık" anlamına gelmektedir. 
- Sayfa 17: İşaret sayesinde çatıdaki gizli, küçük bir ahşap kapağı bulup kaldırırlar. Büyük bir hava akışı sağlanır ve içerideki duman hızla gökyüzüne dağılarak herkesi ferahlatır.

### Bölüm 6 — İz Bırakmak ve Dönüş (Sayfa 18-21)
- Sayfa 18: Çatalhöyük sakinleri sevinç içindedir; bu gizemli küçük yabancıya kil kaselerde soğuk su ikram eder ve minnetle bakarlar. Usta bir köylü, "Bu yaptığını unutmayacağız" dercesine tebessüm eder.
- Sayfa 19: Sanatkar biri oracıktaki kil tablete onu hatırlamak için boyasıyla ufak bir fedora (şapka) silueti çizer. Kahramanımız hiç beklemediği bir şekilde 9000 yıl öncesine kendi imzasını atmıştır.
- Sayfa 20: Tam o an boynundaki amulet yeniden kor gibi ısınmaya ve tanıdık mavi ışığını saçmaya başlar: "Dönüş zamanı!". Yeni arkadaşları ayrılmasını istemez ancak zamanı daralmaktadır. Çatıdan koşarak uzaklaşır.
- Sayfa 21: Evlerin arasındaki gizli duvar nişini bulur, amuleti çevirdiği gibi bembeyaz boyuttan geçerek sessiz, turistik günümüze düşer. Avucunu açtığında küçük, yanık bir kil boncukla göz göze gelir. Acaba bu eski taş daha hangi kapıları açacaktır?

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 21 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child jumping between mudbrick roofs", "Child throwing clay dirt to put out hearth").
- Anne, baba, kardeş gibi aile üyesi KULLANMA. Çocuk bu maceraya tek başına çıkar, yardımcı karakter ve köylüler dışında başka tanıdık kişi yok.

⚠️ DOĞRU/YANLIŞ YAZI ÖRNEKLERİ:
❌ YANLIŞ: "{child_name} Çatalhöyük'ü gezdi. Kerpiç evlerin çatısına çıktı. Neolitik kapları gördü. Sonra duvar resimlerini inceledi."
✅ DOĞRU: "{child_name} çatıdan çatıya atlayarak dumanın kaynağını aradı. Derken bir kapak gördü — altından göz yaşartan bir duman yükseliyordu!"

⚠️ TUTARLILIK KURALLARI:
🗝️ ÖNEMLİ OBJE: Antik Tılsım (Amulet) = glowing earthy ancient stone amulet with spiral carvings. TÜM SAYFALARDA AYNI görünüm. DEĞİŞTİRME.
👗 KIYAFET: {clothing_description} tüm sayfalarda DEĞİŞMEZ. Kıyafet değişimi YASAK.

⛔ İÇERİK YASAKLARI:
- Anne, baba, aile üyesi YASAK
- Dini/siyasi referans YASAK
- Gezi rehberi formatı YASAK ("...gördü. Sonra ...gitti." YASAK)
- Korkutucu/şiddet ağırlıklı sahneler YASAK — tehlike hissedilir ama hemen çözülür
"""

# ============================================================================
# LOCATION CONSTRAINTS (Kademe Haritası & Kamera Açıları)
# ============================================================================

CATALHOYUK_LOCATION_CONSTRAINTS = (
    "Setting alternates vastly every few pages. "
    "Kademe haritası ve Kamera kullanımları: "
    "Pages 1-3: Modern natural history museum interior. (Medium Shot) "
    "Pages 4-6: Swirling time-portal effect. (Close-up) "
    "Pages 7-9: Rooftops of Catalhoyuk (flat mudbrick roofs, no streets). (Wide Shot) "
    "Pages 10-17: Dark, smoky, earthy indoor hearth rooms under the roofs. (Low angle action shot) "
    "Pages 18-21: Sunset rooftops leading back to the bright museum. (Wide Shot) "
)

# ============================================================================
# CULTURAL ELEMENTS — 10 Kültürel Mekan (iyileştirildi: 8 → 10)
# ============================================================================

CATALHOYUK_CULTURAL_ELEMENTS = {
    "location": "Çatalhöyük, Çumra, Konya, Turkey",
    "historic_site": "Çatalhöyük, 9000 years old (7100-5700 BC)",
    "unesco": "UNESCO World Heritage Site",
    "period": "Neolithic Age",
    "colors": "Earthy mud brown, deep ochre, burnt terracotta, amber glow, time-rift turquoise",
    "primary": [
        "Mud-brick clustered houses",
        "Rooftop pathways, wooden ladder access",
        "Ancient clay pots, hearths",
        "Glowing stone amulet with spiral carvings",
        "Small sandy-brown village dog",
        "Sun-dried adobe brick walls",
    ],
    "secondary": [
        "Faded ochre wall paintings (bull motifs)",
        "Woven reed baskets",
        "Modern museum display cases",
        "Ancient bone tools and obsidian arrowheads",
        "Obsidian workshop with volcanic glass shards",
        "Communal grain storage pits with clay-sealed tops",
    ],
    "major_elements": [
        "Mud-brick houses, rooftop pathways, ladder access (no streets or doors)",
        "Wall paintings, hearths, clay pots, woven baskets",
        "Ancient village community, smoke vents",
        "Earthy textures, mud, clay, ochre elements",
        "Obsidian workshop — craftsmen shaping volcanic glass into tools and mirrors",
        "Grain storage area — large clay-sealed pits storing wheat and barley",
    ],
    "atmosphere": "Action-packed, mysterious, time-travel, Neolithic discovery",
    "values": ["Courage", "Problem Solving", "Community Help", "Historical awareness"],
    "sensitivity_rules": [
        "NO aggressive animal encounters or violent fires",
        "No modern slang from ancient villagers",
        "Child remains safe throughout the journey, danger is overcome quickly",
    ],
}

# ============================================================================
# SCENARIO BIBLE — Companion, Obje, Lokasyon Paketi
# ============================================================================

CATALHOYUK_SCENARIO_BIBLE = {
    "magic_item": {
        "name": "Antik Tılsım (Amulet)",
        "behavior": "Tehlike anında hızlı titrer/parlar, yön gösterir, sakin anlarda hafifçe ışıldar.",
        "visual_lock": "a glowing earthy ancient stone amulet with spiral carvings pulsing warm amber light",
        "appears_on_pages": "all",
    },
    "tone_rules": [
        "Indiana Jones tarzı macera — hızlı, aksiyonlu, nefes kesici",
        "Korkutucu sahneler YASAK, duman/tehlike hissi var ama kurtuluş hemen gelir",
        "Didaktik değil, olay örgüsüyle eğitsel değerleri yaşat",
        "Bu bir turistik gezi değil, aksiyon odaklı hikaye",
    ],
    "cultural_facts": [
        "Çatalhöyük 9000 yıllık (MÖ 7100-5700) Neolitik yerleşim",
        "Sokak yok — evlere çatılardan ahşap merdivenle girilir",
        "Kerpiç evler birbirine bitişik, çatılar yaya yolu olarak kullanılır",
        "Duvar resimleri (boğa motifleri), obsidyen aletler, kil kaplar",
        "UNESCO Dünya Mirası listesinde",
        "Obsidyen atölyeleri — volkanik cam aletler ve aynalar üretilirdi",
        "Topluluk tahıl depoları — buğday ve arpa büyük kil kaplarda saklanırdı",
    ],
    "side_character": {
        "name": "Köy Köpeği",
        "species": "dog",
        "personality": "Meraklı, sadık, cesur ama yangından korkar. Havlayarak yol gösterir.",
        "visual_lock": "a small playful sandy-brown village dog with floppy ears and a short tail",
        "absent_reason": "S.10-15 arası evin içine girmeye cesaret edemez, çatıda bekler.",
        "appears_on_pages": [5, 6, 7, 8, 9, 16, 18, 19, 20],
    },
}

# ============================================================================
# CUSTOM INPUTS — Companion Seçenekleri (4 seçenek)
# ============================================================================

CATALHOYUK_CUSTOM_INPUTS: list[dict] = [
    {
        "key": "animal_friend",
        "type": "select",
        "label": "Yol Arkadaşı Hayvan",
        "default": "Köpek",
        "options": [
            {"label": "Neolitik Köy Köpeği", "value": "Köpek"},
            {"label": "Neolitik Keçi Yavrusu", "value": "Neolitik Keçi"},
            {"label": "Step Kartalı", "value": "Step Kartalı"},
            {"label": "Yabani Kedi", "value": "Yabani Kedi"},
        ],
    }
]

# ============================================================================
# DATABASE UPDATE
# ============================================================================


async def update_catalhoyuk_scenario():
    """Çatalhöyük senaryosunu Scenario Master iyileştirmeleriyle günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "catalhoyuk")
                | (Scenario.theme_key == "catalhoyuk_neolithic_city")
                | (Scenario.name.ilike("%Çatalhöyük%"))
                | (Scenario.name.ilike("%Catalhoyuk%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Çatalhöyük'ün Çatı Yolu", is_active=True)
            scenario.theme_key = "catalhoyuk"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Çatalhöyük'ün Çatı Yolu"
        scenario.description = (
            "Indiana Jones tarzı bir prehistorik macera! Bulduğu antik amulet ile "
            "9000 yıllık Neolitik Çatalhöyük'e ışınlanan çocuğun, sokaksız çatı labirentlerinde "
            "yol bularak duman krizini (küçük yangın) çözmesini anlatan heyecanlı bir serüven."
        )
        scenario.theme_key = "catalhoyuk"
        
        # Kapaklar ve Promptlar
        scenario.cover_prompt_template = CATALHOYUK_COVER_PROMPT
        scenario.page_prompt_template = CATALHOYUK_PAGE_PROMPT
        scenario.story_prompt_tr = CATALHOYUK_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Lokasyon Kısıtlamaları
        scenario.location_constraints = CATALHOYUK_LOCATION_CONSTRAINTS
        
        # Kültürel, Bible & Pazarlama Verileri
        scenario.cultural_elements = CATALHOYUK_CULTURAL_ELEMENTS
        scenario.scenario_bible = CATALHOYUK_SCENARIO_BIBLE
        scenario.custom_inputs_schema = CATALHOYUK_CUSTOM_INPUTS
        scenario.marketing_badge = "Zaman Yolculuğu"
        scenario.age_range = "5-10"
        scenario.tagline = "Amuletin izinden 9000 yıl öncesine ışınlan!"
        scenario.is_active = True

        await db.commit()

        # Doğrulama raporu
        print(f"✅ Çatalhöyük'ün Çatı Yolu güncellendi: {scenario.id}")
        print(f"  - story_prompt_tr: {len(CATALHOYUK_STORY_PROMPT_TR)} karakter")
        print(f"  - cover_prompt: {len(CATALHOYUK_COVER_PROMPT)} karakter")
        print(f"  - page_prompt: {len(CATALHOYUK_PAGE_PROMPT)} karakter")
        print(f"  - location_constraints: {len(CATALHOYUK_LOCATION_CONSTRAINTS)} karakter")
        print(f"  - cultural_elements: {len(json.dumps(CATALHOYUK_CULTURAL_ELEMENTS))} karakter")
        print(f"  - scenario_bible: {len(json.dumps(CATALHOYUK_SCENARIO_BIBLE))} karakter")
        print(f"  - custom_inputs: {len(CATALHOYUK_CUSTOM_INPUTS)} alan, "
              f"{len(CATALHOYUK_CUSTOM_INPUTS[0]['options'])} companion seçeneği")
        print(f"  - outfit_girl: {len(OUTFIT_GIRL)} karakter")
        print(f"  - outfit_boy: {len(OUTFIT_BOY)} karakter")


if __name__ == "__main__":
    asyncio.run(update_catalhoyuk_scenario())
