"""
Sultanahmet Macerası — Zaman Kırpışmaları, Gizem, Indiana Jones Tarzı
=========================================================================================
- Kitap adı: [Çocuk adı]'ın Zamanın Fısıltısı: Sultanahmet (alt başlık yok)
- Gizli bir müzik çarkıyla (sesli harita) "zaman kırpışmaları" oluşturup bir gizemi çözme macerası
- Yerler: Sultanahmet Meydanı, çeşmeler, taş yollar, kapı kemerleri, güneş saati/gölgeler
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

SULTANAHMET_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child holding a small mechanical music wheel glowing with subtle golden light waves. "
    "Sultanahmet Square with Hagia Sophia's massive dome and slender minarets silhouetted against a warm amber sunset, a flock of white pigeons mid-flight catching the golden light. "
    "Warm golden hour backlighting, soft lens flare behind the domes, volumetric dust motes in the evening air. "
    "Slightly low-angle shot: child 25% foreground, majestic Ottoman skyline 75%. "
    "Regal warm palette: amber gold, Ottoman blue tile accents, creamy marble, soft coral sky."
)

SULTANAHMET_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Sultanahmet Square exterior, historic stone pavements, soaring archways, ancient stone fountains, warm sunset light, lively crowd, pigeons]. "
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
# STORY BLUEPRINT — Sesli Harita ve Gizem Temalı Kurgu (PURE AUTHOR - PASS 1)
# ============================================================================

SULTANAHMET_STORY_PROMPT_TR = """
# SULTANAHMET'TE ZAMANIN FISILTISI: GİZEMLİ MACERA

## YAPI: {child_name} Indiana Jones tarzı kıyafetleriyle Sultanahmet'te rehber kitabında bulduğu eski bir "ses çarkı / müzik kutusu" ile tarihi "zaman kırpışmaları" yaşayarak geçmişle bugün arasında bir köprü kurar ve kayıp bir tarihi emaneti bulur. Heyecanlı, sır dolu, zamanla yarış hissi veren ama korkutucu/şiddet içermeyen, İstanbul'un akşam güneşini hissettiren tempolu bir kurgu. Tam ışınlanma yok; sadece kısa anlarda eski zamanlar üst üste biniyor.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Zamanın Fısıltısı: Sultanahmet" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, ritimli ve 5-10 yaş aralığında merak uyandırıcı olmalıdır. 
- Her sayfa sonunda küçük bir merak kırıntısı bırak. 
- Bilgi yığını yapma; meydanı, çeşmeleri, güvercinleri, güneş saati ve gölgeleri zorluk/ipucu ögesi olarak kullan.
- Şiddet yok, korku yok. Sadece gizemli ve heyecanlı yakalanmadan ipucu toplama kurgusu var.

---

### Bölüm 1 — Gizemli Çark (Sayfa 1-3)
- Sayfa 1: {child_name} akşamüzeri Sultanahmet Meydanı'nda gezerken yerde deri kaplı, çok eski bir rehber kitap görür. Kitabın sayfalarının arasına gizlenmiş pirinçten, tekerlekli mekanik bir "ses çarkı" bulur.
- Sayfa 2: Merakla çarkın kenarını hafifçe çevirdiğinde içinden çok ince, minicik bir melodi duyulur. Melodi çalmaya başladığı anda etrafındaki ağaçlar ve insanlar "bir an için" eski bir zaman gibi titrer!
- Sayfa 3: Kahramanımız şaşkınlık içindeyken etrafındaki onlarca güvercin aniden havalanır ve rüzgarla kitabın içinden bir sayfa uçuşur. Yere düşen o sayfada aceleyle çizilmiş, el yapımı bir harita parçası vardır.

### Bölüm 2 — Zaman Kırpışması (Sayfa 4-6)
- Sayfa 4: Haritanın üzerinde belirgin 3 işaret çizilidir: oymalı bir çeşme, devasa bir kapı kemeri ve garip bir taş desen. {child_name} heyecanla etrafına bakınıp "Bunlar tam da burada!" diyerek çeşmeye doğru koşmaya başlar.
- Sayfa 5: Püsküren suların olduğu çeşmeye varınca çarktaki melodiyi bir kez daha çevirir. Tıpkı bir göz kırpması gibi: meydandaki kalabalık bir anlığına eski kaftanlı, sarıklı insanlarla dolu bir tarihe dönüşüverir.
- Sayfa 6: Bu "zaman kırpışmasının" o kısacık anında, panikle koşan birinin elinden çok önemli küçük bir mühür-kılıfı benzeri nesne düşürdüğünü görür. Bir saniye sonra görüntü tamamen günümüze döner ama kahramanımız nesnenin düştüğü noktayı artık biliyordur.

### Bölüm 3 — Kayıp Görev (Sayfa 7-10)
- Sayfa 7: Hızla o noktaya gider, tarihi taş desenin köşesinde çok ufak bir oyuk fark eder. Taşların arasına sıkışmış eski, tozlu mühür kılıfını bulup çıkarır; fakat kötü haber: içi boştur!
- Sayfa 8: Az ilerideki bir rehberin telaşla "Sergiye ait çok önemli eski bir etiket mühür bugün kayboldu, bulunmazsa eser yanlış tanıtılacak ve tarih değişecek!" dediğini duyar. Artık çözmesi gereken bir görevi vardır.
- Sayfa 9: Kılıfın kayıp parçasını bulmak için haritadaki ikinci işarete, devasa kapı kemerine doğru atılır. Çarkını tekrar çevirdiğinde oluşan o sihirli dalgayla, kemerin gölgesindeki duvarda yepyeni parlayan bir işaret beliriverir.
- Sayfa 10: Duvardaki gizli işaret bir bulmacadır: üç sembol yan yanadır (Lale, Dalga ve Yıldız). Kahramanımız etrafındaki binlerce tarihi taş desenin arasında bu üçlünün doğru sıralanışını nefes nefese aramaya başlar.

### Bölüm 4 — Gölgenin Oyunu (Sayfa 11-14)
- Sayfa 11: Lale, dalga ve yıldız oymalarını doğru sırda yan yana bulduğu an, elindeki harita sayfası sanki kendi iradesi varmışçasına katlanıp şekil değiştirir! Üzerinde yeni bir ok ve "Gölge nereye düşerse..." yazısı belirir.
- Sayfa 12: Güneşin altın sarısı son ışıklarıyla meydanda upuzun bir gölge çizgisi oluşmuştur; çocuğumuz güneş batmadan gölgeyi yakalayabilmek için kalabalıkların arasında adeta uçarcasına hızlanır.
- Sayfa 13: Takip ettiği gölge çizgisi tam da eski bir ahşap bankın ayaklarının hizasında son bulur. Hemen yere eğilip gizlenmiş karanlık noktaya bakar: orada, toprağın rengine karışmış çok küçük bir kese durmaktadır!
- Sayfa 14: Keseyi heyecanla açar, içinde aynı lale ve yıldız desenlerini taşıyan kayıp mührün parçası vardır. Ancak parça ortadan kırıktır; bulmacanın bitmesi için o sivri ucun da tamamlanması gerekmektedir.

### Bölüm 5 — Birleşen Yapboz (Sayfa 15-18)
- Sayfa 15: {child_name} bu sefer bir risk alıp çarkın melodisini "ters" yönde çevirir. Oluşan bu yeni ters-zaman kırpışmasında, yıllar yıllar önce eksik parçanın panikten koşuşturan adamın çantasındaki "püsküle" takılıp savrulduğunu izler.
- Sayfa 16: Hemen gerçek zamana döner; meydanı tarar ve kimseyi suçlamadan sadece aklına kazıdığı o "eski desenli püskülün" birebir aynısını bulmak için standlara ve insan geçişlerine odaklanır.
- Sayfa 17: Turist dükkanlarının sıralandığı köşede, tezgahın kenarında asılı nostaljik bir çanta püskülü görür, tezgahın tam arkasında toprağa gizlenmiş bir ışık parıldar. Eğilir ve düşmüş olan o ufacık eksik parçayı da bulur!
- Sayfa 18: İki parçayı mühür kılıfında birleştirdiği an haritadaki tüm semboller altın gibi parlar. Kahramanımız zafer sevinciyle hiç vakit kaybetmeden doğrudan rehberin olduğu sergi noktasına doğru depar atar.

### Bölüm 6 — Geriye Kalan İmza (Sayfa 19-21)
- Sayfa 19: Nefes nefese kalmış bir halde tamamlanmış mührü tam zamanında sergideki görevliye ulaştırır, hatanın düzeltilmesini sağlar. Görevli, "Sıradan bir ziyaretçi değilsin, büyük bir felaketin önüne geçtin!" diyerek göz kırpar.
- Sayfa 20: Çantasındaki ses çarkı son kez, bu kez çok yumuşak bir ninni gibi çalar; meydanda etrafı saran kalabalık ona bir anlığına sarıklı esnaflar olarak görünüp teşekkür eder gibi gülümserler. Tarihten küçük bir selam almıştır.
- Sayfa 21: Çarkı sonsuza dek durdurduğunda her şey o normal, güzel İstanbul akşamına döner. Ancak harita sayfası yok olmuş, çantasının içinde sadece parlayan küçücük bir yıldız çizimi bırakmıştır. Acaba bu yıldız bir gün başka bir yerde yeniden parlayacak mıdır?

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 21 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child sprinting through pigeon flock in square", "Child twisting small brass musical wheel under archway").
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

SULTANAHMET_CULTURAL_ELEMENTS = {
    "location": "Sultanahmet Square, Istanbul, Turkey",
    "historic_site": "Sultanahmet and Hagia Sophia exteriors, Historic Peninsula",
    "major_elements": [
        "Historic stone pavements, soaring archways, ancient fountains",
        "Warm sunset lighting, sweeping shadows",
        "Lively crowd, pigeons taking flight",
        "A magical mechanical music wheel modifying perception of time",
    ],
    "atmosphere": "Adventurous, mysterious, fast-paced investigation, sunset magic",
    "values": ["Problem Solving", "Tracking", "Historical Empathy", "Patience"],
    "sensitivity_rules": [
        "NO worship close-ups",
        "Exterior focus mostly (Square, fountains, arches)",
        "NO religious figure depictions",
        "Action and mystery focus"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

SULTANAHMET_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_sultanahmet_scenario():
    """Sultanahmet senaryosunu Zaman Kırpışmaları & Gizemli Ses Çarkı kurgusuyla günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "sultanahmet")
                | (Scenario.theme_key == "sultanahmet_blue_mosque")
                | (Scenario.name.ilike("%Sultanahmet%"))
                | (Scenario.name.ilike("%Mavi Cami%"))
                | (Scenario.name.ilike("%Blue Mosque%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Sultanahmet'te Zamanın Fısıltısı", is_active=True)
            scenario.theme_key = "sultanahmet"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Sultanahmet'te Zamanın Fısıltısı"
        scenario.description = (
            "Indiana Jones tarzı müthiş bir tarih gizemi! Bulduğu gizemli ve antik ses çarkı sayesinde "
            "Sultanahmet Meydanı'nda 'zaman kırpışmaları' yaşayan kahramanın, kaybolan "
            "tarihi bir mührü bulma ve sırları çözme yarışını anlatır."
        )
        scenario.theme_key = "sultanahmet"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = SULTANAHMET_COVER_PROMPT
        scenario.page_prompt_template = SULTANAHMET_PAGE_PROMPT
        scenario.story_prompt_tr = SULTANAHMET_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = SULTANAHMET_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = SULTANAHMET_CUSTOM_INPUTS
        scenario.marketing_badge = "Gizemli Macera"
        scenario.age_range = "5-10"
        scenario.tagline = "Ses çarkını çevir, tarihin gizemini çöz!"
        scenario.is_active = True

        await db.commit()
        print(f"Sultanahmet 'Zamanın Fısıltısı' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_sultanahmet_scenario())
