"""
Mercan Şehrin Sinyali — Okyanus Macerası, Gizem, Yardım
=============================================================================================
- Kitap adı: [Çocuk adı]'ın Mercan Şehrin Sinyali (alt başlık yok)
- Bir araştırma merkezinde bulunan deniz pusulası ile okyanusa inerek mercanları ve yavru balıkları kurtarma macerası
- Yerler: Akvaryum merkezi, araştırma kapsülü, mercan resifi, karanlık geçit
- Kıyafet: Okyanus keşif dalgıç kıyafeti, kız ve erkek için zorunlu ve her sayfada aynı tutarlı (kıyafet kilidi)
- Kurguyu bozabilecek kullanıcı seçenekleri yok (custom_inputs boş)
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import or_, select
from app.core.database import async_session_factory
from app.models import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (AI DIRECTOR - PASS 2)
# ============================================================================

OCEAN_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child swimming gracefully next to a small glass-domed underwater research capsule with glowing instrument panels inside. "
    "Surrounded by a magnificent vibrant coral reef ecosystem — branching staghorn corals, fan corals, sea anemones — and shimmering schools of tropical fish in formation. "
    "Dramatic underwater lighting: golden sun rays piercing through the turquoise water surface creating dancing caustic light patterns, subtle bioluminescent blue accents from deep-sea organisms. "
    "Dynamic underwater angle: child 30% foreground, expansive coral reef environment 70%. "
    "Ocean palette: deep turquoise blue, vibrant coral oranges and pinks, golden caustic light, pearl white bubbles."
)

OCEAN_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [underwater reef, vibrant corals, sun rays through water, bubbles, schools of fish, deep blue gradients]. "
    "Include multiple sea creatures in most scenes (fish, turtle, dolphin, octopus, seahorse, manta ray, jellyfish, etc.). "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera. "
    "child ocean explorer in a teal wetsuit and yellow diving vest, dynamic action, full body visible. "
    "Dangerous animals only in the distance, no direct contact, child remains safe. "
    "Avoid: photorealistic, pasted face, collage, duplicate child, random text, watermark, logo, blurry, low quality. {STYLE}"
)

# ============================================================================
# OUTFIT — Okyanus Dalgıç Takımı (Kesin Kilidi)
# ============================================================================

OUTFIT_GIRL = (
    "child-sized ocean explorer outfit: a teal lightweight wetsuit with short sleeves, a yellow diving vest, "
    "waterproof knee pads, snorkeling mask pushed up on the forehead, compact oxygen mini-tank backpack, "
    "flippers, and a small waterproof satchel, no logos, plus a small seashell charm bracelet. "
    "EXACTLY the same outfit on every page — same teal wetsuit, same yellow vest, same flippers. "
    "Same child character, consistent face and hair across all pages."
)

OUTFIT_BOY = (
    "child-sized ocean explorer outfit: a teal lightweight wetsuit with short sleeves, a yellow diving vest, "
    "waterproof knee pads, snorkeling mask pushed up on the forehead, compact oxygen mini-tank backpack, "
    "flippers, and a small waterproof satchel, no logos. "
    "EXACTLY the same outfit on every page — same teal wetsuit, same yellow vest, same flippers. "
    "Same child character, consistent face and hair across all pages."
)

# ============================================================================
# STORY BLUEPRINT — Mercan Şehri Kurtarma ve Deniz Canlıları (PURE AUTHOR - PASS 1)
# ============================================================================

OCEAN_STORY_PROMPT_TR = """
# MERCAN ŞEHRİN SİNYALİ

## YAPI: {child_name} okyanus keşif kıyafetleriyle araştırma merkezinde akıllı bir deniz pusulası bularak kendini kurtarma görevinde bulur. Okyanusun altındaki dev mercan şehrindeki yavru balıkların yolu kopan bir ağ ile kapanmıştır ve akıntı tersine dönmüştür. Çocuğumuz kapsülüyle iner ve her sayfada başka bir deniz canlısından (kaplumbağa, yunus, denizanası vb.) aldığı zekice ipuçlarıyla bu ağı uzaktan, güvenli bir şekilde çözer. Şiddet, köpekbalığı saldırısı ve boğulma KESİNLİKLE YOKTUR. Bol deniz canlısı tanıtarak, "yardım edip başardım" hissi veren, 22 sayfalık sürükleyici bir kurgudur.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Mercan Şehrin Sinyali" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, ritimli ve çocuk okurları heveslendirici şekilde dinamiktir.
- Ders sıkıcılığında biyoloji bilgisi değil, hayvanların özelliklerini maceranın içine yedirerek (Manta vatozun kanadıyla akıntıyı göstermesi gibi) anlat. Köpek balıkları sadece arka plan majestikliğidir, Asla tehdit değildir.

---

### Bölüm 1 — Mavi Sinyalin Çağrısı (Sayfa 1-4)
- Sayfa 1: {child_name} devasa akvaryumların olduğu deniz araştırma merkezinde büyülü sualtı dünyasını hayranlıkla izlemektedir. Gezi yolunun tam köşesinde, cam kenarında mavi bir ışıkla hafifçe parlayan o küçük ve garip akıllı deniz pusulasını fark eder.
- Sayfa 2: Çocuk merakla eğilip pusulaya dokunduğu anda küçücük ekranda parlayan harflerle yanıp sönen bir "BLUE SIGNAL" (Mavi Sinyal) ibaresi beliriverir! Kahramanımızın kalbi hızla çarpar, sanki okyanusun bizzat kendisi ondan çok önemli bir görev için yardım istiyordur.
- Sayfa 3: Tam o an merkezdeki sevimli araştırma robotu yanına yaklaşır ve heyecanlı bir sesle "Mini araştırma kapsülü birinci göreve hazır!" diye anons geçer. Çocuk büyük bir sevinçle yüksek teknolojili sarı kapsüle oturur ve üstündeki sağlam cam kubbe güvenle tıslayarak kapanır.
- Sayfa 4: Kapsül yavaşça ve güvenli bir şekilde denizin serin sularına dalarken etrafındaki dünya aniden huzur veren muazzam bir mavi uzaya dönüşür. Onu ilk karşılayanlar ise etrafında dans eden ve yön gösteren, sürü halinde gümüş gibi parlayan minicik balıklar olur.

### Bölüm 5 — Mercanlara İniş (Sayfa 5-7)
- Sayfa 5: Biraz daha derinleştikçe bilgece ve yavaşça yüzen, çok tatlı devasa bir deniz kaplumbağası kapsülün yanına dostça yaklaşır. Kaplumbağa kocaman gözleriyle çocuğun kolundaki pusulaya bakar ve tam o sinyalin yönüne doğru yüzerek sanki "Lütfen, beni takip et" demek ister.
- Sayfa 6: Biraz sonra kapsül muazzam Mercan Şehrine ulaşır ama orada bir gariplik vardır; palyaço balıkları ve renkli anemonlar çok üzgündür ve suyun doğal akıntısı sanki tamamen tersine ve yanlış yöne dönmüştür.
- Sayfa 7: Ufukta çok neşeli sesler çıkartan yunuslar ortaya çıkar ve akıntının merkezinde "dairesel bir yol ve burgu" çizerek yukarıyı gösterirler. Zeki çocuğumuz bu ipucunu hemen anlar: Koca resifin doğal akıntısını tıkayan büyük ve yanlış bir şey oraya yapışmıştır!

### Bölüm 8 — Ağdaki İpuçları (Sayfa 8-10)
- Sayfa 8: Çok geçmeden kocaman, üstü atık dolu ve kopup gelmiş dev bir halat/ağ parçasının tam da mercan geçidinin kilit noktasına sıkıca takıldığını görürler. Çocuk dışarı çıkıp tehlikeli bir şekilde dokunmak yerine, bunu akıllı kapsülündeki araçlarla ve daha güvenli bir şekilde çözeceğine söz verir.
- Sayfa 9: Kayaların hemen altından kıvrak kollarıyla uzanan zeki bir ahtapot yavrusu yanaşarak uzun kollarıyla dikkatlice o koca ağın bağlı olduğu "üç anahtar kaya noktasını" tek tek işaret eder. Macera tam da burada devasa bir sualtı bulmacasına dönüşür: Acaba önce hangi kilidi açmalıdır?
- Sayfa 10: Çocuğumuz hemen bileğindeki o mavi ışıklı deniz pusulasına bakar, ekranda üç yeni simge şekli parlamaktadır: Bir denizkabuğu, bir deniz yıldızı ve bir dalga... Ve resifin üstündeki kayalar tam da şekillere benzemektedir!

### Bölüm 11 — Akıntıya Karşı (Sayfa 11-13)
- Sayfa 11: Hedeflenen kilit noktaya gitmesi gerekiyorken birdenbire ufuktaki çok büyük bir denizanası grubu pırıl pırıl ışıldayarak ona o doğru ve zararsız olan asıl geçidi aydınlatır. Çocuğumuz o minik ışıkları rotası kılarak yavaşça karanlık bir kemerin tam altından başarıyla süzülerek geçer.
- Sayfa 12: O karanlık ve dar geçidin duvarlarına harika kuyruklarıyla tamamen kamufle olarak saklanmış incecik yüzlerce denizatı, güvenle onu tepeden izlemektedir. O an pusula incecik bir sesle "bip"leyerek zamanın azaldığını ve gün batmadan yüzeye dönmesi gerektiğini hatırlatır.
- Sayfa 13: Geçitten hemen sonra karşısına çıkan koca gövdeli bilge Manta vatozu o devasa kanadıyla zorlu akıntının açısını göstererek sanki "Şu taraftan dolaşırsan güvendesin!" der. Müzisyen gibi ellerini kullanan çocuğumuz, kapsülün açısını tam da vatozun o güzel kanat yönüne doğru ustaca çeviriverir.

### Bölüm 14 — Çözüm Başlıyor (Sayfa 14-16)
- Sayfa 14: Karşıya geçerken derinliklerin sisi içinde koca yüzgeciyle sadece uzaktan ve yanlarından çok asilce süzülen majesterik bir köpekbalığı geçer (asla tehdit değildir). Çocuk ona olan saygısıyla sükunet içinde mesafesini korur ve güvenli kapsülüyle görev yoluna hiç durmadan şevkle devam eder.
- Sayfa 15: Tam zamanında gelmiştir; işte karşısında, kocaman ağın resifi inatla boğduğu ve sökülmesi gereken o gizemli üç kilit kaya noktası duruyordur. Çocuk büyük bir ciddiyetle kapsülünün kontrol panelini açar ve yüksek teknolojili "Remote Cutter" (Kancalı Robot Kol) düğmesine basar.
- Sayfa 16: Robotik kol ustaca uzanarak ağdaki o ilk kördüğümü zekice kesip çözer; o koca ağ zinciri biraz gevşese de yerinden çıkmaya hiç niyeti yoktur. Fakat o ikinci zorlu nokta çok daha derindedir ve okyanusun ters akan girdap akıntısı kapsülü titretip oldukça zorlamaktadır!

### Bölüm 17 — Son Hamleler (Sayfa 17-19)
- Sayfa 17: Tam da o noktada, rehberi olan deniz kaplumbağasının usulca girdiği iki kayanın harika boşluğunu fark edip o siperden koca akıntıyı kırarak en uca yaklaşır. Ustaca yönlendirdiği kol yardımıyla fıskiyeli ağın o inatçı ikinci kilit noktasını da ustalıkla kesip büyük bir yükten kurtulur.
- Sayfa 18: Geriye sadece en son kilit nokta kalmıştır, ama oradaki yuvalarında olan yavru palyaço balıkları resifin çıkışı kapandığı için büyük bir telaş yaşamaktadır. Ancak iyi bir kaşif olan çocuğumuz derin ve uzun bir nefes alıp fısıldar: "Sakin kalın minikler, bu sadece en son küçük bir adım..."
- Sayfa 19: Çocuğumuz son kesim düğmesine basar basmaz kalın ağ tamamen serbest kalıp süzülür ve kapsülün önündeki büyük atık toplama haznesinin içine güvenle ve ustaca çekilir. Büyük şehrin tüm akıntısı birdenbire doğru yönünü bulur; grileşen bütün güzel mercanlar sanki derin bir nefes alıp yeniden canlanır!

### Bölüm 20 — Güvenli Geçit (Sayfa 20-22)
- Sayfa 20: Tam bu sevinç yaşanırken mavi uçsuz bucaksız sisin ardından çok çok büyük bir balina en tatlı şarkısını söylercesine bir ton fırlatır; kocaman okyanus adeta ona bu derin sesiyle "Teşekkür" ediyordur. Yol boyunca kurtarılmayı bekleyen tüm minik deniz yavruları açılan o harika güvenli geçitten neşeyle yüzerek geçerler.
- Sayfa 21: Çocuğumuz büyük başarının ardından araştırma kapsülünün kollarını çeker, kabarcıkların arasından güneşin pembeye büründüğü su yüzeyine çıkarak merkeze sağ salim ve okyanus bilinciyle döner.
- Sayfa 22: Merkezde soyunma odasına geçerken o mavi deniz pusulası ekranında kocaman bir istiridye kabuğu simgesi bırakarak görevi bittiği için usulca söner; çocuğumuzun cebinde ise anı olarak sapsarı bir deniz kabuğu rozeti kalmıştır. Islak saçlarıyla pencereden denize bakarak gülümser: "Acaba koca okyanus bana yarın yeni bir mavi sinyal daha yollar mı?"

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 22 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child navigating glass-domed research capsule", "Child watching an octopus point to the net").
- Hayvanların hiçbiri konuşmaz (çizgi film gibi değil), sadece eylemleri, davranışları ve fiziksel yetenekleriyle yol gösterirler. 
- Hiçbir deniz canlısı saldırısı olmamalı (Güvenli, çevreye saygılı okyanus atmosferi).
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

OCEAN_CULTURAL_ELEMENTS = {
    "location": "A deep oceanic vibrant Coral Reef",
    "historic_site": "Wilderness ecosystem",
    "major_elements": [
        "A magnificent Coral City",
        "A tiny high-tech underwater research capsule with a glass dome",
        "Sea turtles, dolphins, clownfish, jellyfish, and a distant whale",
        "Glowing blue oceanic signal compass"
    ],
    "atmosphere": "Vibrant, educational, wondrous, safe yet adventurous",
    "values": ["Environmental Protection", "Observation", "Empathy", "Agility"],
    "sensitivity_rules": [
        "NO aggressive animal encounters (sharks are distant and respected)",
        "NO direct dangerous physical tasks (uses capsule robot arm)",
        "Child wears a proper teal wetsuit throughout, ensuring realism to diving safety",
        "Child acts as a protector of the ocean and its creatures"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

OCEAN_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_ocean_adventure_scenario():
    """Okyanus senaryosunu Mercan Şehrin Sinyali Şablonuna göre günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                or_(
                    Scenario.theme_key == "ocean",
                    Scenario.theme_key == "ocean_depths",
                    Scenario.name.ilike("%Okyanus%"),
                    Scenario.name.ilike("%Ocean%"),
                    Scenario.name.ilike("%Mercan%")
                )
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Mercan Şehrin Sinyali", is_active=True)
            scenario.theme_key = "ocean"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Mercan Şehrin Sinyali"
        scenario.description = (
            "Bulduğu sihirli sualtı pusulasıyla mini bir araştırma kapsülüne binen çocuğumuzun, "
            "okyanus derinliklerindeki muazzam Mercan Şehrinde kilitli kalmış balık yavrularını "
            "deniz canlılarından aldığı ipuçlarıyla dev ağlardan kurtarma macerası!"
        )
        scenario.theme_key = "ocean"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = OCEAN_COVER_PROMPT
        scenario.page_prompt_template = OCEAN_PAGE_PROMPT
        scenario.story_prompt_tr = OCEAN_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = OCEAN_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = OCEAN_CUSTOM_INPUTS
        scenario.marketing_badge = "Okyanus Macerası"
        scenario.age_range = "5-10"
        scenario.tagline = "Deniz canlılarının ipucunu takip et, mercanları kurtar!"
        scenario.is_active = True
        scenario.display_order = 16

        await db.commit()
        print(f"Okyanus 'Mercan Şehri' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_ocean_adventure_scenario())
