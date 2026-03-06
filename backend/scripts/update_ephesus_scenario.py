"""
Efes Antik Kenti — Zaman Yolculuğu, Macera, Indiana Jones Tarzı
==========================================================================
- Kitap adı: [Çocuk adı]'ın Zaman Kapısı: Efes (alt başlık yok)
- Zaman yolculuğu ile Antik Efes devrinde sorun (su kemeri) çözme macerası
- Celsus Kütüphanesi, Curetes Caddesi, Su Kemerleri
- Kıyafet: Indiana Jones tarzı gezgin kıyafeti, kız ve erkek için zorunlu ve her sayfada aynı tutarlı (kıyafet kilidi)
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

EPHESUS_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Magnificent Library of Celsus facade with tall weathered Corinthian columns, intricate carved marble reliefs, a glowing magical time-rift portal shimmering between the ancient pillars. "
    "Golden hour Aegean sunlight casting long warm shadows across sun-bleached marble, soft volumetric haze drifting through the columns, warm rim lighting on the child. "
    "Low-angle hero shot: child 25% foreground, towering 3000-year-old Greco-Roman architecture 75%. "
    "Rich warm palette: honey gold light, ivory marble, terracotta accents, deep azure sky. UNESCO atmosphere."
)

EPHESUS_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Ancient Ephesus ruins, bustling ancient Roman market, marble columns, ancient aqueducts, stone mechanisms]. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera."
)

# ============================================================================
# OUTFIT — Indiana Jones Tarzı Kıyafet Kilidi (Sabit ve Zorunlu)
# ============================================================================

OUTFIT_GIRL = (
    "khaki explorer shirt, fitted brown leather vest, tan cargo shorts, sturdy brown boots, "
    "small satchel crossbody bag, classic fedora hat, subtle woven bracelet charm. "
    "EXACTLY the same outfit on every page — same khaki shirt, same fedora hat, same brown vest."
)

OUTFIT_BOY = (
    "khaki explorer shirt, brown leather vest, tan cargo shorts, sturdy brown boots, "
    "small satchel crossbody bag, classic fedora hat. "
    "EXACTLY the same outfit on every page — same khaki shirt, same fedora hat, same brown vest."
)

# ============================================================================
# STORY BLUEPRINT — Zaman Yolculuğu ve Mühendislik Macerası (PURE AUTHOR - PASS 1)
# ============================================================================

EPHESUS_STORY_PROMPT_TR = """
# EFES'İN ZAMAN KAPISI: ANTİK MACERA

## YAPI: {child_name} Indiana Jones tarzı kıyafetleriyle Efes Antik Kenti'nde eski bir taşı bularak zaman yolculuğu yapar ve Roma dönemindeki Efes'te gerçek bir mekanik problemi (su kemeri) çözer. Heyecan, gizem, küçük kovalamacalar ve adrenalin içerir. Korkutucu veya kanlı DEĞİL, tempolu.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Zaman Kapısı: Efes" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. 
- Dili akıcı, ritimli ve 5-10 yaş aralığında merak uyandırıcı olmalıdır. 
- Bilgi yığını yapma; Efes'i yaşanılan maceranın epik donanımı olarak kullan.
- Her sayfa veya bölüm sonunda hafif bir merak (cliffhanger) hissi bırak.

---

### Bölüm 1 — Gizemli Keşif (Sayfa 1-3)
- Sayfa 1: {child_name} kütüphanede (veya harabelerde) gezerken çöpte tuhaf, çatlak ekranlı eski bir 'tablet/taş' görür. "Bunu kim atar ki?" diye düşünerek taşı dikkatle alır.
- Sayfa 2: Taşa dokununca hafif bir titreşim hisseder. Üzerinde anlaşılmaz antik semboller parlamaya başlar. Kalbi hızla atarak taşı hemen çantasına saklar.
- Sayfa 3: Efes Antik Kenti turu başlar. Sıcak Ege rüzgarı esmekte, mermer taş yollar ve dev sütunlar arasından yürünmektedir. Çantasındaki taş yeniden titremeye başlar.

### Bölüm 2 — Zaman Kapısı (Sayfa 4-6)
- Sayfa 4: Çocuğun dikkati Celsus Kütüphanesi yanındaki özel bir sütuna çekilir. Sütunun üzerinde tam elindeki taşın şekline uyan pürüzsüz bir boşluk fark eder. İçinde kararsızlık ve cesaret çarpışmaktadır.
- Sayfa 5: Cesaretini toplar ve gizemli taşı yuvasına yerleştirir. Aniden göz kamaştırıcı bir ışık patlaması olur, zemin sarsılır ve yankılanan bir "Vızz!" sesi duyulur. Gözlerini kapatır. (Kısa cliffhanger)
- Sayfa 6: Gözlerini açtığında turistler gitmiş; etrafta kalabalık bir antik Roma pazar yeri, tunik giymiş insanlar ve at arabaları vardır. Zaman tünelinden geçmiştir! Büyük bir şaşkınlıkla fısıldar: "Ben neredeyim?!"

### Bölüm 3 — Kuruyan Çeşmeler (Sayfa 7-9)
- Sayfa 7: Panik halindeki Romalı bir çırak koşarak gelir: "Su kemeri bozuldu! Şehrin çeşmeleri durdu!" diyerek etrafa bağırır. Maceranın ana problemi başlamıştır.
- Sayfa 8: {child_name} ustaları takip eder. Kurumuş taş kanallarını inceler. Elindeki tabletteki sembollerin, su kanalının üzerindeki usta işaretleriyle benzerliğini fark eder.
- Sayfa 9: Bir görevli "Yanlış taşı takarsak bütün sistem içeriden çöker!" der. Kahramanımız içgüdüsel olarak "Benim taşım bunu anlatıyor" hissine kapılır.

### Bölüm 4 — Antik Bulmaca ve Kovalamaca (Sayfa 10-13)
- Sayfa 10: Ana vanaya giden gizli kapakta ufak bir bulmaca vardır: 3 sütundaki sembolleri hizalaması gerekir. Zekasını konuşturup sembolleri titizlikle eşleştirir.
- Sayfa 11: Eşleşme olunca gizli bir bakım tüneli büyük bir gıcırtıyla açılır. Tünel fener ışıklarıyla kaplıdır. Ancak birden arkasında taşı isteyen şüpheli birilerinin ayak sesleri duyulur!
- Sayfa 12: Kovalama anı: Dar geçitte tavandan tozlar dökülür ve kapı yavaşça kapanmaktadır. {child_name} son anda çeviklikle altından kayarak geçer, çantası sallanır ve taş umutla parlar.
- Sayfa 13: Tünel dehlizinin sonunda paslı, sıkışmış devasa su vanası mekanizmasını bulur. Sistemi serbest bırakmak için o küçük ellerden çok daha fazla güç gerekmektedir.

### Bölüm 5 — Mühendislik ve Başarı (Sayfa 14-17)
- Sayfa 14: Antik bir usta peşinden yetişir ve "Bunu tek kişi çeviremez" der. Kahramanımız etraftaki kalaslar ve halatlarla hızlıca bir 'kaldıraç' planı kurar.
- Sayfa 15: Plan tıkır tıkır işler, vana döner ve "şşşş!" diye suların gürlemesi duyulur. Ancak o sırada yeni bir çatlak açılır; su yanlış kanala kaçmaktadır!
- Sayfa 16: Hızlı karar anı. Suyun akışını ana kanala yönlendirecek olan 'kilit taşı' eksiktir. Kendi çantasındaki taşı çıkarıp kanalın yuvasına tutar.
- Sayfa 17: Taşı yerine bir yapboz parçası gibi oturtur. Suyun akışı efsanevi bir şekilde düzelir. Yeryüzünden, meydandaki insanlardan büyük bir alkış kopar.

### Bölüm 6 — İz Bırakmak ve Günümüze Dönüş (Sayfa 18-21)
- Sayfa 18: Pazar yerine gürül gürül su gelir. Antik insanlar şaşkındır: "Bu küçük yabancı başardı!". Herkes minnettar bakışlarla onu izler.
- Sayfa 19: Romalı bir yazıcı bu anı kil tablete kazımak ister. Kahramanımız utangaçça gülerken yanlışlıkla orada günümüze de uzanacak küçük, gizli bir sembol (iz) bırakır.
- Sayfa 20: Çantasındaki taş tekrar hızla titreşmeye ve ışık saçmaya başlar: Geri dönme vakti! Arkasındaki gizemli adam onu yakalamak üzeredir, kapıya doğru hızla koşar (Sprint).
- Sayfa 21: Taşı sütundan çekip alır, her yer bembeyaz olur. Günümüze döndüğünde Efes yine turistik, sessiz halindedir. Ama avucunun içinde eski çağdan kalma küçük bir hatıra işareti kalmıştır. Derin bir merak uyanır: "Acaba taş bir gün yine titreyecek mi?"

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 21 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child sliding under a heavy stone door", "Child pulling a complex rope lever mechanism").
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

EPHESUS_CULTURAL_ELEMENTS = {
    "location": "Ephesus Ancient City, Selçuk, Izmir, Turkey",
    "unesco": "UNESCO World Heritage Site",
    "major_monuments": [
        "Celsus Library (12,000 scrolls, two-story facade)",
        "Great Theater (25,000 capacity, carved into hillside)",
        "Curetes Street (marble colonnaded street)",
        "Ancient Water Aqueducts and Fountains",
    ],
    "atmosphere": "Ancient, mysterious, action-packed, time-travel, Greco-Roman civilization",
    "values": ["Courage", "Problem Solving", "Engineering", "Historical awareness"],
}

# ============================================================================
# CUSTOM INPUTS — Kurguyu bozmayacak şekilde boş
# ============================================================================

EPHESUS_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_ephesus_scenario():
    """Efes Antik Kenti senaryosunu Zaman Kapısı kurgusuyla günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "ephesus")
                | (Scenario.theme_key == "ephesus_ancient_city")
                | (Scenario.name.ilike("%Efes%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Efes'in Zaman Kapısı", is_active=True)
            scenario.theme_key = "ephesus"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Efes'in Zaman Kapısı"
        scenario.description = (
            "Indiana Jones tarzı bir antik macera! Kütüphanede bulduğu gizemli tablet ile "
            "Efes'in antik çağlarına zaman yolculuğu yapan çocuğun, bozulan taş su kemerini "
            "aşmasını ve şehri kurtarmasını anlatan heyecanlı bir serüven."
        )
        scenario.theme_key = "ephesus"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = EPHESUS_COVER_PROMPT
        scenario.page_prompt_template = EPHESUS_PAGE_PROMPT
        scenario.story_prompt_tr = EPHESUS_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = EPHESUS_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = EPHESUS_CUSTOM_INPUTS
        scenario.marketing_badge = "Zaman Yolculuğu"
        scenario.age_range = "5-10"
        scenario.tagline = "Gizemli tabletle antik çağlara ışınlan!"
        scenario.is_active = True

        await db.commit()
        print(f"Efes 'Zaman Kapısı' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_ephesus_scenario())
