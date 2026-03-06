"""
Sümela Macerası — Zaman Yolculuğu, Gizem, Indiana Jones Tarzı
=========================================================================================
- Kitap adı: [Çocuk adı]'ın Kayıp Mührü: Sümela (alt başlık yok)
- Gizemli bir madalyonla manastırın geçmişine (zaman yolculuğu) gidip kayıp el yazmasını kurtarma macerası
- Yerler: Altındere Vadisi, orman, şelale, taş basamaklar, kayaya oyulmuş gizli geçitler
- Kıyafet: Indiana Jones tarzı gezgin kıyafeti, kız ve erkek için zorunlu ve her sayfada aynı tutarlı (kıyafet kilidi)
- Kültürel hassasiyet: dini figür YOK, atmosferik taş mimari odaklı, nötr/gizemli
- Kurguyu bozabilecek kullanıcı seçenekleri yok (custom_inputs boş)
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (AI DIRECTOR - PASS 2)
# ============================================================================

SUMELA_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Sumela Monastery carved into a sheer vertical cliff face at 1200m altitude, ancient Byzantine stone arches and terraces clinging to weathered grey rock. "
    "Lush misty Altindere Valley pine forest blanketing the mountainside below, volumetric fog drifting through the treetops. "
    "Child holding an ancient bronze amulet/medallion with warm golden glow, epic cinematic light trails emanating from the artifact. "
    "Dramatic low-angle shot: child 30% foreground, towering monastery cliff and misty mountains 70%. "
    "Moody adventure palette: deep forest greens, slate grey rock, warm bronze glow, ethereal white mist."
)

SUMELA_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Sumela Monastery interiors, stone stairs, misty forest mountains, cliffside architecture, fresco walls, candlelight, ancient monastery vibe]. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera. "
    "Avoid: photorealistic, pasted face, collage, duplicate child, extra people (unless required by scene), text, watermark, logo, blurry, low quality. {STYLE}"
)

# ============================================================================
# OUTFIT — Indiana Jones Tarzı Kıyafet Kilidi (Sabit ve Zorunlu)
# ============================================================================

OUTFIT_GIRL = (
    "khaki explorer shirt, fitted brown leather vest, tan cargo shorts, sturdy brown boots, "
    "small satchel crossbody bag, classic fedora hat, subtle woven bracelet charm. "
    "EXACTLY the same outfit on every page — same khaki shirt, same fedora hat, same brown vest. "
    "Same child character, same outfit, consistent face and hair across all pages."
)

OUTFIT_BOY = (
    "khaki explorer shirt, brown leather vest, tan cargo shorts, sturdy brown boots, "
    "small satchel crossbody bag, classic fedora hat. "
    "EXACTLY the same outfit on every page — same khaki shirt, same fedora hat, same brown vest. "
    "Same child character, same outfit, consistent face and hair across all pages."
)

# ============================================================================
# STORY BLUEPRINT — Gizem ve Bulmaca Temalı Zaman Yolculuğu (PURE AUTHOR - PASS 1)
# ============================================================================

SUMELA_STORY_PROMPT_TR = """
# SÜMELA'NIN KAYIP MÜHRÜ: GİZEMLİ MACERA

## YAPI: {child_name} Indiana Jones tarzı kıyafetleriyle, bulduğu eski bir madalyon/amulet aracılığıyla Sümela Manastırı'nın geçmişine zaman yolculuğu yapar ve kayıp bir el yazmasını/kitabı kurtarmak için zeka dolu bir bulmaca serüvenine atılır. Heyecanlı, gizem dolu, takip hissi veren ama korkutucu/şiddet içermeyen, rüzgar ve sise dayalı atmosferik bir kurgu sür.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Kayıp Mührü: Sümela" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, ritimli ve 5-10 yaş aralığında merak uyandırıcı olmalıdır. 
- Her sayfada küçük bir merak kırıntısı (cliffhanger/gerilim ipucu) bırak.
- Bilgi yığını yapma; manastırın dik yamacı, taşı, rüzgarı, dar koridorları zorluk öğesi olsun.
- KÜLTÜREL HASSASİYET: Dini/politik bir tartışmaya veya ibadet detayına asla girme. Haç, ikon vb. detaylara odaklanma. Mekanı etkileyici, antik bir taştan labirent (mimari gizem) gibi tarafsız ver.

---

### Bölüm 1 — Gizemli Madalyon (Sayfa 1-3)
- Sayfa 1: Ziyaretçi merkezindeki hediyelik eşya dükkanının "kayıp eşya" kutusunda, {child_name} eski, ağır bir bronz madalyon bulur. Elini attığı an madalyon derinden, sanki bir kalp atışı gibi "tık" diye atar.
- Sayfa 2: Tozunu sildiğinde üzerinde parlayan üç sembol görür: kanatlarını açmış bir kartal, antik bir anahtar ve gizemli bir spiral. "Bunu sahibine mi vermeliyim?" diye düşünerek taşı çantasına saklar.
- Sayfa 3: Sümela Manastırı'na uzanan dik taş yola adım attığında rüzgar sertleşir ve beyaz sis etrafını sarar. Çantasındaki madalyondan incecik ama ısrarcı bir çınlama sesi yükselmektedir.

### Bölüm 2 — Zaman Kapısı (Sayfa 4-6)
- Sayfa 4: Sümela'nın içine girdiğinde, kimsenin dikkat etmediği silik bir duvar resminin (fresk) yanında küçük, yuvarlak ve tuhaf bir oyuk fark eder. Oyuğun şekli çantasındaki madalyonla baştan sona aynıdır!
- Sayfa 5: Nefesini tutar ve madalyonu oyuğa yerleştirir. Vadideki rüzgar bir anda kesilir, ardından sağır edici bir "Vuuuş!" sesiyle manastırın taşları arasından sızan göz kamaştırıcı bir ışık seli patlar.
- Sayfa 6: Işık dağılıp gözlerini açtığında turistler yoktur; manastırın eski, geçmiş dönemindedir. Etrafta mum ışıklarında telaşla dolanan insanlar vardır. Biri umutsuzca feryat eder: "Kayıp el yazması yok olursa tüm bilgimiz biter!"

### Bölüm 3 — İpuçlarının Peşinde (Sayfa 7-10)
- Sayfa 7: {child_name} hiç tereddüt etmeden yardıma karar verir. Madalyonundaki ilk ipucunu kullanır: spiral işareti. Gözleri duvarları tararken taş köşedeki aynı spiral oymayı bulur.
- Sayfa 8: Spiral oymayı izlediğinde kimsenin bilmediği, taş merdivenlere açılan karanlık ve dar bir koridora girer. Koridorda esen rüzgar sanki ona fısıltıyla yön gösteriyor gibidir.
- Sayfa 9: Karşısına üzerinde üç sembol bulunan ağır bir kapı çıkar: kartal, anahtar ve spiral. Doğru sırayı bulamazsa kapının ebediyen kilitlenebileceği korkutucu bir sessizlik "klik" sesiyle uyarısını yapar.
- Sayfa 10: Etrafı dikkatlice inceler: duvarda yüksekte bir kartal motifi, tam ortada spiral çiziği, aşağıda ise anahtar izi vardır. "Yüksekte uçan, ortada dönen, aşağıyı açan..." diyerek sıralamayı başarıyla çözer.

### Bölüm 4 — Gizemli Takip (Sayfa 11-14)
- Sayfa 11: Kapı büyük bir gıcırtıyla açılır ve gizli bir depo odasına girer; raflarda yüzlerce kap dizilidir, zeminde ise çok eski bir mühür izi parlar. Ama aranan gizemli el yazması burada değildir!
- Sayfa 12: Dikkatle dinlerken, damlaların ritmik olarak aktığı ufak bir taş oluk fark eder. "Su... bu ses başka bir yere, daha derine gidiyor olmalı!" diyerek su izini takip eder.
- Sayfa 13: İlerledikçe loş ortamda sis yoğunlaşır; ensesinde belli belirsiz ve sadece gölgeden ibaret ürkütücü olmayan ama gizemli birinin onu takip ettiği hissine kapılır. Hızlı adımlarla çatlak taşların üzerinden atlar.
- Sayfa 14: Karşısına korkunç uçurumu gören, iki kayayı bağlayan köprü benzeri çok dar bir geçit çıkar. Çantasının kayışından destek alıp rüzgara karşı amansız bir adrenalinle o daracık dengede adım adım geçer.

### Bölüm 5 — Bulmacanın Sonu (Sayfa 15-18)
- Sayfa 15: Geçidin sonundaki gizli odanın ortasında devasa eski bir tahta sandık durmaktadır. Sandığın kapağında büyük bir anahtar deliği vardır ancak etrafta bir anahtar gözükmez.
- Sayfa 16: Çantasındaki madalyonun "anahtar" sembolü güçlüce parlayınca {child_name} duvarda dikkat çekmeyen çıkıntıyı görür. O taşa var gücüyle bastırdığında taşın içinden zekice gizlenmiş gerçek anahtar çıkar.
- Sayfa 17: Sandığı büyük bir heyecanla açar; el yazması oradadır ama tüm sayfaları kopmuş ve sırası tamamen karışmıştır! Zaman akıp giderken acilen o sayfaları düzgün sıraya koyması gereken bir hız bulmacasına girişir.
- Sayfa 18: Sayfaların kenarlarındaki ufacık kartal ve spiral dizilimlerinden mantığı kavrar ve kitabı kusursuz sıraya dizer. Tamamlandığı anda el yazması hafifçe altın sarısı bir toz saçar.

### Bölüm 6 — Geri Dönüş (Sayfa 19-21)
- Sayfa 19: El yazmasını ait olduğu kişilere ulaştırdığında herkes büyük bir nefes alır; minnettar bir yazıcı, tarihe geçmesi için çocuğun eline küçük bir mühür izi basar. Kahraman artık görevini yapmış, dönme zamanının geldiğini hissetmiştir.
- Sayfa 20: Göğsündeki madalyon kor gibi ısınmaya ve tanıdık ışığını vermeye başlar: Dönüş kapısı açılmaktadır! Ancak dışarıdaki rüzgar fırtınaya dönüşmüş, kapı kapanmak üzeredir.
- Sayfa 21: Manastır boyunca koşarak gizli yuvayı bulur, madalyonun sembollerini tam yuvasında çevirince büyük bir flaş patlar. Sis dağılıp günümüze döndüğünde etrafında doar sadece turistler vardır; ama avucunda, binlerce yıl öncesinden kalan gerçek bir mühür izi yadigardır... "Bu mühür... bir gün yeniden parlayacak mı?"

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 21 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child leaping over cracked stone bridge", "Child turning ancient dial on a door").
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SUMELA_CULTURAL_ELEMENTS = {
    "location": "Sümela Manastırı, Altındere Vadisi, Maçka, Trabzon, Turkey",
    "historic_site": "Sumela Monastery, founded 386 AD (1600+ years), carved into cliff at 1200m",
    "natural_features": [
        "Altındere Valley forest, pine trees",
        "Stone path, steep stone steps, mist and rain",
        "Mountain peaks, deep valley drops",
    ],
    "architecture": "Byzantine rock-carved monastery — stone arches, terraces, hidden rooms, ancient labyrinths",
    "sensitivity_rules": [
        "NO religious figure depictions",
        "NO worship details",
        "Architecture and mystery focus",
    ],
    "atmosphere": "Adventurous, mysterious, hidden passages, time-travel, ancient monastery",
    "values": ["Courage", "Intelligence", "Puzzle Solving", "Discovery"],
}

# ============================================================================
# CUSTOM INPUTS — Kurguyu bozmayacak şekilde boş
# ============================================================================

SUMELA_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_sumela_scenario():
    """Sümela senaryosunu gizemli Zaman Yolculuğu kurgusuyla günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "sumela")
                | (Scenario.theme_key == "sumela_monastery_trabzon")
                | (Scenario.name.ilike("%Sümela%"))
                | (Scenario.name.ilike("%Sumela%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Sümela'nın Kayıp Mührü", is_active=True)
            scenario.theme_key = "sumela"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Sümela'nın Kayıp Mührü"
        scenario.description = (
            "Indiana Jones tarzı efsanevi bir manastır macerası! Gizemli bir madalyonla "
            "Sümela'nın geçmişine ışınlanan çocuğun, gizli geçitleri ve şifreleri "
            "aşarak kayıp el yazmasını bulma serüveni."
        )
        scenario.theme_key = "sumela"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = SUMELA_COVER_PROMPT
        scenario.page_prompt_template = SUMELA_PAGE_PROMPT
        scenario.story_prompt_tr = SUMELA_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = SUMELA_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = SUMELA_CUSTOM_INPUTS
        scenario.marketing_badge = "Gizemli Macera"
        scenario.age_range = "5-10"
        scenario.tagline = "Sırlarla dolu Sümela'nın şifrelerini çöz!"
        scenario.is_active = True

        await db.commit()
        print(f"Sumela 'Kayıp Mühür' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_sumela_scenario())
