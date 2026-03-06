"""
Uzayın Kayıp Sinyali — Enerji Çekirdeği, Gizem, Astronot Kıyafeti
=============================================================================================
- Kitap adı: [Çocuk adı]'ın Uzayın Kayıp Sinyali (alt başlık yok)
- Bir deneme kapsülünden uzay istasyonuna geçerek uzay istasyonunun enerji çekirdeğini dengeleme çabası
- Yerler: Roket merkezi, uzay istasyonu koridorları, sıfır yerçekimi, enerji çekirdeği odası, kapılar
- Kıyafet: Astronot takımı (Sadece Türk bayraklı), kız ve erkek için zorunlu ve her sayfada aynı tutarlı (kıyafet kilidi)
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

SPACE_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child astronaut floating weightlessly in a sleek futuristic space station corridor with polished metallic walls and glowing holographic control panels displaying signal waveforms. "
    "Breathtaking view of Earth — swirling blue oceans and white cloud patterns — through a large hexagonal reinforced window, soft reflected Earth-glow illuminating the scene. "
    "Cool cinematic neon lighting with electric blue and soft white panels, tiny floating particles catching the light in zero gravity. "
    "Dynamic floating angle: child 30% mid-frame, expansive station environment and Earth view 70%. "
    "Sci-fi palette: deep space black, electric blue neon, pristine white suit, warm amber Earth glow."
)

SPACE_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [space station interior, futuristic corridors, floating objects, Earth view through window, soft neon panels, zero gravity motion, energy core glow]. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera. "
    "child astronaut wearing a white EVA suit with Turkish flag patches only (no USA flag), dynamic action. "
    "Avoid: photorealistic, pasted face, collage, duplicate child, random text, watermark, logo, blurry, low quality, USA flag, American flag, NASA logo, SpaceX logo. {STYLE}"
)

# ============================================================================
# OUTFIT — Astronot Takımı (Türk Bayrağı ve Kesin Kilidi)
# ============================================================================

OUTFIT_GIRL = (
    "white EVA-style astronaut suit for a child, modern helmet with clear visor, life-support backpack, "
    "gloves and boots, small Turkish flag patches on both shoulders and a Turkish flag patch on the chest, "
    "mission-style name tag, no other national flags, no logos. "
    "EXACTLY the same outfit on every page — same white astronaut suit, same helmet, same patches. "
    "Same child character, consistent face and hair across all pages."
)

OUTFIT_BOY = (
    "white EVA-style astronaut suit for a child, modern helmet with clear visor, life-support backpack, "
    "gloves and boots, small Turkish flag patches on both shoulders and a Turkish flag patch on the chest, "
    "mission-style name tag, no other national flags, no logos. "
    "EXACTLY the same outfit on every page — same white astronaut suit, same helmet, same patches. "
    "Same child character, consistent face and hair across all pages."
)

# ============================================================================
# STORY BLUEPRINT — Sinyal Şifresi ve Çekirdek Kurtarma (PURE AUTHOR - PASS 1)
# ============================================================================

SPACE_STORY_PROMPT_TR = """
# UZAYIN KAYIP SİNYALİ

## YAPI: {child_name} roket merkezinde bir eğitim kapsülüne binmesiyle kendini gerçek bir uzay istasyonunda bulur. Bir uzaylının varlığı ya da yaratıklar KESİNLİKLE YOKTUR, istasyonun yapay zekası arızalanmış/enerji çekirdeği dengesizleşmiştir ve çözümü ritmik bir şifredir. Çocuk kendi astronot becerilerini ve "şifre(ritim)" çözme yeteneklerini kullanarak sıfır yerçekiminde kayıp şifreyi tamamlayıp istasyonun çekirdeğini kurtarır. Gerçekçi, güvenli ve "ben başardım!" hissi veren bir kurgudur.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Uzayın Kayıp Sinyali" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, ritimli ve çocuk okurları heveslendirici şekilde dinamiktir.
- Uzaylı veya ölüm tehlikesi yoktur. Meteorlar "pencere dışındaki görsel"dir, istasyona çarpmaz. Temel zorluk eşyaların havada uçuşması, kilitli kapılar ve ritmi tutturmaktır.

---

### Bölüm 1 — Deneme Uçuşu (Sayfa 1-4)
- Sayfa 1: {child_name} dev gibi füzelerin sergilendiği görkemli bir roket merkezinde gezerken köşede bırakılmış gümüş renkli, son teknoloji parlak bir kapsül fark eder. Kapsülün vizöründe tatlı bir mavi ışıkla "Deneme Uçuşu Hazır" yazısı yavaşça göz kırpmaktadır.
- Sayfa 2: Astronot olma hayaliyle yanan kahramanımız o kocaman kokpit koltuğuna gururla oturur oturmaz etrafındaki düğmeler rengarenk ışıldamaya başlar. Tam o sırada ana navigasyon panelinde kırmızı harflerle büyük bir "UNKNOWN SIGNAL" (Bilinmeyen Sinyal) ibaresi parlar.
- Sayfa 3: Kapsül bir anlığına şiddetli şekilde sarsılıp tüm iç ışıklarını kapatınca çocuğumuz gözlerini sımsıkı kapatır. Saniyeler sonra gözlerini usulca açtığında, karşısındaki devasa dış camdan o eşsiz mavi mermer, dev Dünya gezegeni görünüyordur!
- Sayfa 4: Tıslayarak açılan ağır kapıdan süzülen çocuk kendini yepyeni, parıltılı ve sonsuz bir uzay istasyonu koridorunda bulur. Nefesini tutup şaşkınlıkla etrafına bakınarak "Bu inanamıyorum... Gerçekten uzaydayım!" diye fısıldar.

### Bölüm 5 — Çekirdeğin Durumu (Sayfa 5-7)
- Sayfa 5: Ama her şey yolunda gitmiyordur; istasyonun duvar ışıkları sürekli titremekte ve uyarı sirenleri hafifçe "bip... bip..." diye öterek yankılanmaktadır. Köşeden süzülen tekerlekli şirin bir hizmet rotobu tiz ama telaşlı bir sesle "ENERGY CORE UNSTABLE!" anonsu geçer.
- Sayfa 6: Kahramanımız hemen cesaretini toplayıp mini robotu takip eder ama koridordaki yapay yerçekimi bir kapanıp bir açıldığı için zorlanır. Havada süzülerek başıboş gezen kalemler, tabletler ve uzay bisküvilerini usta bir astronot edasıyla tek tek yakalayıp cebine koyar.
- Sayfa 7: İleride devasa ve kalın kapıları olan asıl büyük enerji odasına ulaştıklarında kapının tamamen kilitli olduğunu, sadece üzerinde üç küçük elektronik yuva bulunduğunu görür. Bu yuvalarda sırasıyla parlayan üç dijital simge vardır: Bir yıldız, bir halka ve bir şimşek!

### Bölüm 8 — Ritmi Yakalamak (Sayfa 8-10)
- Sayfa 8: İstasyonda en başından beri cihazlardan gelen o tuhaf ve gizemli ritim yeniden duyulur: "bip... bip-bip... biiip!" Çocuğun aklına hemen bir fikir gelir ve duyduğu o ritmik zamanlamaya uyarak kapıdaki simgelere aynı sırayla basmayı dener.
- Sayfa 9: Tuşlara aynı müzik temposuyla dokunduğu anda dev kapı büyük bir basınçla iki yana açılır ve içeride fırıl fırıl dönen devasa enerji çekirdeği belirir! Fakat çekirdek öyle aşırı parlıyordur ki, dengesinin tamamen bozulduğu ve her an durabileceği bellidir.
- Sayfa 10: İstasyonun yanından hiç ayrılmayan asistan robotu ekranında kocaman sayılarla "3 STABILIZER SWITCH" yazısını göstererek anahtarların eksik olduğunu bildirir. Bu üç acil durum anahtarı, tehlikede olan istasyonun bambaşka koridorlarına gizlenmiştir!

### Bölüm 11 — Sıfır Yerçekimi Koridoru (Sayfa 11-13)
- Sayfa 11: Kurtarma görevini üstlenen kahramanımız kendisini dev bir sıfır yerçekimi tüneline bırakır ve uzay giysisinin eldivenleriyle duvardaki tutamaklara asılarak ilerler. O an arızadan dolayı hızından kopmuş metal bir alet kutusu çok hızlı bir şekilde üzerine doğru kaymaya başlar; ona çarpabilirdi!
- Sayfa 12: Çevikliği on numara olan çocuk ellerini son saniyede bir refleksle uzatıp süzülen kutuyu boşlukta kusursuzca yakalar ve geçiti güvene alır. Kutuyu köşeye sabitledikten sonra o büyük ilk anahtarı bulur ama onu açtığı an anahtar otomatik mekanizmayla hızla geri kapanır!
- Sayfa 13: Demek ki bir kilit ve şifre daha vardır. İkinci numaralı anahtar için dev gözlem camlı bölüme geçtiğinde, fırtına gibi hızla kayan ama sadece manzara olan o harika sarı yıldız yamacını ve meteor çizgilerini seyre dalarak derin bir odaklanma yaşar.

### Bölüm 14 — Sistemleri Başlatma (Sayfa 14-16)
- Sayfa 14: İkinci anahtarı da yerinde tutabilmek için yine o bilindik ritmik şifreyi eldiveniyle panellere girmesi gerekiyordur; pür dikkat kulak kabartır: "bip-bip... dur... biiip!" Bir astronot ciddiyetiyle kodları şutlar.
- Sayfa 15: Tık! İkinci anahtar büyük bir güçle yeşil yanar ve sisteme kilitlenir. Fakat istasyon motorların zorlanmasıyla çok daha güçlü şekilde titremeye başlayınca zamanlarının hızla azaldığını, çok acele etmeleri gerektiğini çok iyi anlar.
- Sayfa 16: Üçüncü ve en son kilit anahtarı, sadece acil durum kırmızı flaşörlerinin yanıp söndüğü karanlık bir tamir koridorunun en dibindedir. Çocuğumuz soğukkanlılığını asla yitirmeden koridordaki ışık oklarını bir harita gibi takip ederek hedefe saniyeler içinde ulaşır.

### Bölüm 17 — Son Sıralama (Sayfa 17-19)
- Sayfa 17: Tam en son mavi anahtarı büyük bir umutla çevireceği esnada panel acı bir "dıt" sesi çıkararak "SEQUENCE REQUIRED" hatasını fırlatır! O an panik yapmaz, hafızasındaki o üç simgenin tam ve kusursuz sırasını kafasında kurgular: Yıldız... Halka... Şimşek!
- Sayfa 18: Tüm simgeleri ve üç ayrı anahtarı başarıyla birbirine kenetleyen roket kahramanımız, havada zarif perendeler atarak ana makinedeki dev çekirdeğe zafer edasıyla geri döner. Son hamle, o başta duydukları mükemmel ritmi ana ekranda tek tuşla, mikrosaniye bile kaçırmadan "onaylamaktır".
- Sayfa 19: Nefesini derince tutar, kulağındaki o sesi kalbiyle hisseder ve parmağını "biiiip" notasının tam o en yüksek anında "ENTER" tuşuna büyük bir inançla basar! Saniyeler içinde çekirdeğin o kör edici patlak ışığı harika bir mavi sükunete dönüşür ve tüm sistem dengeye oturur.

### Bölüm 20 — Görev Tamam! (Sayfa 20-22)
- Sayfa 20: İstasyonun o can sıkıcı titremeleri anında son bulur, solgun ışıklar gün gibi aydınlanır ve şaşkın robot sevinçle havada zıplayarak tiz bir "Bip!" sesi çıkarır. Çocuğun önüne gelen dev ekranda yemyeşil harflerle gurur verici bir mesaj parlamaktadır: "SIGNAL: THANK YOU" (Sinyal: Teşekkürler).
- Sayfa 21: Çekirdeğin aydınlığıyla tünelin sonundaki o ilk parlak metalik kapsülün kapısı tekrar davetkar bir şekilde belirginleşir; çocuk tüm görevini harika bir iş çıkarmanın verdiği o huzurla tamamlayıp kapsüle ağır adımlarla geri girer.
- Sayfa 22: Kapsülün vizörü bir kez daha göz kamaştıran bir ışıkla flaşlandığı an çocuğumuz kendini müzedeki eski roket sergisinde sapasağlam bir şekilde kalkarken bulur, ama kalın eldiveninin içinde parlayan özel ve ufak yıldız şeklinde metal bir roket rozeti kalmıştır. Gözü gökyüzüne kayar: "Acaba o gizemli sinyal evrendeki başka bir maceradan bana geri döner mi?"

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 22 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child grabbing a floating toolbox in zero gravity", "Child pressing buttons on glowing control panel").
- NASA, ABD bayrağı yok, logosuz ve sadece Türk Bayraklı astronot kıyafeti vurgusunu koru. 
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SPACE_CULTURAL_ELEMENTS = {
    "location": "A grand Space Museum, moving to a futuristic Space Station",
    "historic_site": "Earth orbit",
    "major_elements": [
        "Sleek silver training capsule",
        "Zero-gravity corridors windowed to Earth, floating objects",
        "A huge glowing energy core, robotic assistant",
        "Control panels with unknown signal rhythm inputs"
    ],
    "atmosphere": "Futuristic, tense but highly rewarding, scientific, action-hero driven",
    "values": ["Quick Thinking", "Focus", "Action-oriented", "Determination"],
    "sensitivity_rules": [
        "NO weapons, NO aliens, NO scary monsters",
        "Peril is environmental (floating objects, timers, alarms) but safe",
        "Child wears a spacesuit completely devoid of American flags and NASA logos, specifically emphasizing modern Turkish space pride."
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

SPACE_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_space_scenario():
    """Uzay senaryosunu yeni Kayıp Sinyal Şifre-Çözüm Şablonuna göre günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "space")
                | (Scenario.theme_key == "solar_system")
                | (Scenario.theme_key == "solar_systems_space")
                | (Scenario.name.ilike("%Uzay%"))
                | (Scenario.name.ilike("%Güneş%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Uzayın Kayıp Sinyali", is_active=True)
            scenario.theme_key = "space"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Uzayın Kayıp Sinyali"
        scenario.description = (
            "Yerçekimi olmayan istasyonda adrenalin dolu bir zeka oyunu! "
            "Kahramanımız devasa bir uzay istasyonunun sistem arızasını çözmek için "
            "havada süzülen simgelerin ve gizemli ritmik sinyallerin izini sürerek çekirdeği kurtarıyor."
        )
        scenario.theme_key = "space"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = SPACE_COVER_PROMPT
        scenario.page_prompt_template = SPACE_PAGE_PROMPT
        scenario.story_prompt_tr = SPACE_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = SPACE_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = SPACE_CUSTOM_INPUTS
        scenario.marketing_badge = "Uzay Macerası"
        scenario.age_range = "5-10"
        scenario.tagline = "Sinyalin sırrını çöz, çekirdeği dengede tut."
        scenario.is_active = True

        await db.commit()
        print(f"Uzay 'Kayıp Sinyal' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_space_scenario())
