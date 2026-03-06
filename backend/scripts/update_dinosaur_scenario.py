"""
Dinozorlar Alemi: Kayıp Yuva — Güvenli Macera, Pusula Gizemi, Indiana Jones Tarzı
=============================================================================================
- Kitap adı: [Çocuk adı]'ın Dinozorlar Alemi: Kayıp Yuva (alt başlık yok)
- Bir müzede bulunan fosil pusula ile dinozorlar çağına geçerek fırtınada kalmış yavruyu yuvasına götürme macerası
- Yerler: Müze dev iskelet altı, dev eğrelti ormanı, bataklık kenarı, kanyon, taşlı nehir
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

DINOSAUR_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child holding a small glowing fossil compass emitting warm pulsing amber light from ancient stone carvings. "
    "Background: colossal prehistoric tree ferns with massive fronds, a dramatic stormy sky with billowing dark clouds and lightning flashes, "
    "majestic dinosaur silhouettes — a long-necked Brachiosaurus and a horned Triceratops — visible through swirling mist in the valley below. "
    "Dramatic cinematic backlighting from the stormy sky, volumetric mist weaving through the giant ferns, warm compass glow illuminating the child's face. "
    "Low-angle epic shot: child 30% foreground, immersive prehistoric wilderness 70%. "
    "Prehistoric palette: deep jungle greens, stormy slate grey, warm amber compass glow, misty lavender distance."
)

DINOSAUR_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [prehistoric dinosaur valley, giant tree ferns, mist, dramatic cloudy sky, volcanic rocks, winding river, muddy trail]. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera. "
    "Large predators only in the far distance, no direct contact, child remains safe. Friendly dinosaurs are majestic and peaceful. "
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
# STORY BLUEPRINT — Fosil Pusula ve Yavru Kurtarma Macerası (PURE AUTHOR - PASS 1)
# ============================================================================

DINOSAUR_STORY_PROMPT_TR = """
# DİNOZORLAR ALEMİ: KAYIP YUVA

## YAPI: {child_name} Indiana Jones tarzı explorer kıyafetleriyle müzede gezerken gizemli bir fosil pusula bularak kendini Dinozorlar Alemi'nde bulur. Amacı fırtına çıkmak üzereyken ailesini kaybetmiş minik, sevimli bir dinozor yavrusunu yuvaya güvenle teslim etmektir. Şiddet, kan veya travma yoktur. Etraftaki iri dinozorlar sadece yol gösterici (Triceratops, Stegosaurus) veya arka plan unsurlarıdır (T. rex uzakta). Heyecanlı, koşturmacalı ve bulmaca çözmeli bir macera yazılıdır.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Dinozorlar Alemi: Kayıp Yuva" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, ritimli ve heyecanlıdır. Yaş grubu 5-10 için basit ve nettir.
- Kan, şiddet, saldırı KESİNLİKLE YOK. Yırtıcılardan sadece hızlanmak için uzaktan bahsedilebilir ama direkt tehlike oluşturmazlar.

---

### Bölüm 1 — Fosil Pusula (Sayfa 1-3)
- Sayfa 1: {child_name} tatil gününde devasa fosillerin sergilendiği görkemli doğa tarihi müzesinde ilgiyle gezmektedir. O koskocaman iskeletin hemen ayağının dibinde soluk mavi bir ışıkla parlayan garip, yuvarlak bir "fosil pusula" görür.
- Sayfa 2: Merakına yenilip yerden o pusulayı eline aldığı anda, cihaz "vızır vızır" dönerek titremeye başlar. Bir an için müzenin duvarlarındaki tüm orman resimleri canlanmış gibi hareket eder!
- Sayfa 3: Müzenin ışıkları gider; etrafı ağır bir sis basıp rüzgâr eser ve çocuğumuz gözlerini açtığında kendini beton zemin yerine gökyüzüne değen dev eğrelti otlarıyla dolu antik bir ormanda bulur.

### Bölüm 4 — Kayıp Yavru (Sayfa 4-6)
- Sayfa 4: Uzaklardan pes ve güçlü kükremeler duyulurken çocuğun ayaklarının altındaki toprak bile hafifçe ritmik olarak titremektedir. Ama o hiç panik yapmaz, havalı şapkasını düzeltir ve "Sakin ol... Indiana Jones keşif modu devrede!" diyerek ormana adım atar.
- Sayfa 5: Az ilerideki dev çalılıkların titremesiyle bitkilerin arasından minicik, kafası kalkanlı, çok şirin ama ürkmüş bir dinozor yavrusu fırlar. Yavrucuk koca gözleriyle çocuğa bakıp ürkek, incecik bir ses çıkarır: "Piip!"
- Sayfa 6: Kahramanımız başını kaldırıp gökyüzüne bakar, simsiyah fırtına bulutları hızla toplanmaya ve dev yapraklar havada uçuşmaya başlamıştır. Bu minik yavru, kopacak fırtınadan önce yuvasına ulaştırılmak zorundadır!

### Bölüm 7 — Triceratops'un Rehberliği (Sayfa 7-9)
- Sayfa 7: İkili bir süre gittikten sonra uzak ve güvenli tepede, zararsız bir Triceratops (üç boynuzlu dinozor) süzülerek geçer. O koca canlının yere bıraktığı sert ve kocaman ayak izleri, bataklığın içine doğru en güvenli yolu gösterir gibidir.
- Sayfa 8: Çocuk yavruyla beraber dev ayak izlerini dikkatle takip ederek fokurdayan çamurlu bir antik bataklığın kenarına varır. Yanlış bir adım atıp kayarsa o yoğun çamura tamamen saplanma tehlikesi vardır!
- Sayfa 9: Tam o an bataklığın içindeki Stegosaurus'un sırtındaki kocaman sert plakalara benzeyen eski sağlam taşları fark eder. Kahramanımız bir kurbağa çevikliğiyle o sert taşlara seke seke basarak bataklığı tamamen kuru ayaklarla aşmayı başarır.

### Bölüm 10 — Gökyüzünün Haritası (Sayfa 10-12)
- Sayfa 10: Ormanın derinliğinde yavru aniden pıt diye durup, ince boynunu uzatıp kulağını sağ tarafa dikkatle diker. Çok çok uzaklardan bir Parasaurolophus’un yankılı ve borazan gibi çağrısı duyulur; sanki o ses yavruya "Bu tarafa gelin" diyordur.
- Sayfa 11: Karşılarına ağaç kökleriyle ayrılmış iki dev patika çıkınca çocuğumuz hangisinin doğru olabileceğini düşünmeye başlar. Tam çıkmaza gireceklerken elindeki fosil pusula deli gibi titremeye ve ışık saçmaya başlar!
- Sayfa 12: Pusulanın oku gökyüzüne, oradaki dev şelale yönüne uzanan bir ağacın taç noktasını işaret eder. Çok geçmeden koca süzülen kanatlarıyla uçan bir Pteranodon o noktadan geçerek rotalarının doğruluğunu müjdeler.

### Bölüm 13 — Rüzgar Vadisi ve Kaçış (Sayfa 13-15)
- Sayfa 13: Sükunetle devam eden yolculuk birden iki tarafı sarp kayalık olan ve karanlık, dar bir geçide çıkar. Fırtına tam da burada ciddileşip rüzgar korkunç bir fısıltıyla kanyona dolmaya başlar.
- Sayfa 14: Kötü şans yakalarını bırakmaz ve şimşek yüzünden çatırtıyla devrilen devasa bir ağaç tüm o dar kanyon çıkışını bir kalenin kapısı gibi kapatır. Çocuğumuz hemen çantasını açıp o sağlam keşif ipini çıkararak mükemmel bir üstten aşırtma tırmanışı planlar ve beraberce yukarı çıkarlar.
- Sayfa 15: Geçidin en üst noktasına varıp tırmanışı bitirdiklerinde çok uzak vadinin sisleri içerisinde büyük şöhretin, T. rex'in ürkütücü ve saygıdeğer siluetini ile adımlarını hissederler. Çocuk zekice fısıldar: “Yakınlaşmadan hızlıca ormana dalalım!”

### Bölüm 16 — Nehirdeki Atılım (Sayfa 16-18)
- Sayfa 16: Çalılıkların arasında koştururken yavrucuk çılgın gibi sevinç gösterileri yapar, çünkü ailesinin sıcak yuva kokusunu sonunda alabilmiştir. Fakat bu kavuşmadan önce önlerinde çağlayarak akan gürül gürül bir dinozor vadisi nehri durmaktadır.
- Sayfa 17: Maceracımız elindeki ipi bele bağlayıp nehrin sığ yerlerindeki kocaman kaya parçalarını santim santim hesaplayarak harika bir sekiş planlayıp kendi yolunu çizer. Her büyük ve cesur atlayışında minik de "piip!" diye sevinerek ondan güç alarak kayalara seker.
- Sayfa 18: Islak taşlardan sekip yemyeşil karşı kıyıya, büyük vadinin o geniş ve bereketli açıklığına ulaşırlar. Vadinin sükunet dolu tepesinden, bu serüvende onlara iz bırakan bütün Triceratops (üç boynuzlu) sürüsü neşeyle ama uzaktan onları izlemektedir.

### Bölüm 19 — Müzeye Dönüş (Sayfa 19-21)
- Sayfa 19: O esnada küçük yavrunun endişeli koca anne ve babası koşarak çıkar gelip ve gözyaşlarına boğulurcasına miniklerine sarılır. Tam da fırtına dinip, ilk kocaman yağmur damlaları düşerken herkesin güvende olması müthiş bir rahatlamadır.
- Sayfa 20: Koruyucu o muazzam dev ana dinozor, kahramanımıza bakıp ona içten, nazikçe başını eğip en derin “Teşekkür” niyetinde mırıldanır. İşi biten cesur pusula anında kıvılcımlar saçarak uyanıp çocuğa tek bir şeyi haykırır: “Görevin Bitti, Dönüş Zamanı!”
- Sayfa 21: Çocuğumuz pusulayı sımsıkı kavramasıyla göz kamaştıran dev mavi bir ışık halkası patlar ve çocuk kendini o sessiz, huzurlu müzede buluverir. Elini usulca açtığında, o sihirli pusula yerini taşlaşmış küçücük bir dinozor pati izine bırakmıştır. Şapkasını düzeltirken kıkırdar: "Pusula bir gün yine bana dönecek mi acaba?"

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 21 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child leaping accurately across big river stones", "Child examining prehistoric footprints in the mud").
- Şiddet veya kan kesinlikle olmamalı, büyük tehlike ve yırtıcılar yalnızca siluet/tempo unsuru olarak çok uzakta bırakılmalıdır.
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

DINOSAUR_CULTURAL_ELEMENTS = {
    "location": "Prehistoric Dinosaur Valley, Late Cretaceous period",
    "historic_site": "Ancient Wilderness",
    "major_elements": [
        "Giant tree ferns, misty dramatic skies",
        "Glowing fossil compass artifact",
        "Triceratops, Stegosaurus, Parasaurolophus, Pteranodon",
        "Swamps, rocky canyons, rushing ancient river",
    ],
    "atmosphere": "Epic, safely wild, prehistoric, time-travel mystery, courageous",
    "values": ["Courage", "Responsibility", "Compassion", "Nimbleness"],
    "sensitivity_rules": [
        "NO aggressive predator encounters",
        "Dangerous predators like T-Rex are only seen far in the distance",
        "Child is a protector and problem solver",
        "Emphasis on rescuing a lost baby dinosaur"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

DINOSAUR_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_dinosaur_scenario():
    """Dinozorlar Alemi senaryosunu yeni Fosil Pusula - Kayıp Yuva Şablonuna göre günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "dinosaur")
                | (Scenario.theme_key == "dinosaur_time_travel")
                | (Scenario.name.ilike("%Dinozor%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Dinozorlar Alemi: Kayıp Yuva", is_active=True)
            scenario.theme_key = "dinosaur"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Dinozorlar Alemi: Kayıp Yuva"
        scenario.description = (
            "Bulduğu sihirli fosil pusula ile zamanda yolculuk yapan maceracımız, "
            "yaklaşan büyük fırtınadan önce kayıp bir dinozor yavrusunu yepyeni devasa ormanlarda "
            "ipuçları bularak ailesine ulaştırmaya çalışıyor!"
        )
        scenario.theme_key = "dinosaur"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = DINOSAUR_COVER_PROMPT
        scenario.page_prompt_template = DINOSAUR_PAGE_PROMPT
        scenario.story_prompt_tr = DINOSAUR_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = DINOSAUR_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = DINOSAUR_CUSTOM_INPUTS
        scenario.marketing_badge = "Zaman Yolculuğu"
        scenario.age_range = "5-10"
        scenario.tagline = "Fosil pusulanı takip et, yavruyu devasa dünyaya aldırış etmeden ailesine yetiştir!"
        scenario.is_active = True

        await db.commit()
        print(f"Dinozorlar 'Kayıp Yuva' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_dinosaur_scenario())
