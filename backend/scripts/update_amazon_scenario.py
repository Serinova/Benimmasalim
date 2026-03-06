"""
Amazon Ormanları Macerası — Hayvan İzleri, Gizem, Indiana Jones Tarzı
=========================================================================================
- Kitap adı: [Çocuk adı]'ın Amazon'un Gizli Çağrısı (alt başlık yok)
- Ormanda yankılanan "tık tık" sinyalinin izini hayvanların yardımıyla sürme macerası
- Yerler: Amazon sağanağı, dev ağaçlar, nehir, liana köprüleri, sık bitki örtüsü
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

AMAZON_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child pushing through hanging lianas and dense layered tropical jungle foliage, colossal ancient trees draped in vines and bromeliads. "
    "Winding Amazon river glimmering in the distance, exotic scarlet macaws and toucans in flight among the canopy. "
    "Dramatic god-rays of golden sunlight piercing through the dense canopy, volumetric jungle mist, glistening dew on giant emerald leaves. "
    "Eye-level adventure shot: child 25% foreground, immersive jungle depth 75%. "
    "Vibrant tropical palette: deep emerald greens, golden light shafts, rich earth browns, pops of scarlet and turquoise."
)

AMAZON_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Amazon rainforest, dense jungle, winding river, mist, sun rays through canopy, hanging vines, exotic wildlife, vibrant colors]. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera. "
    "Dangerous animals only in the distance, no direct contact, child remains safe. "
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
# STORY BLUEPRINT — Hayvanlarla İpuçları Takibi Temalı Kurgu (PURE AUTHOR - PASS 1)
# ============================================================================

AMAZON_STORY_PROMPT_TR = """
# AMAZON'UN GİZLİ ÇAĞRISI: GİZEMLİ MACERA

## YAPI: {child_name} Indiana Jones tarzı kıyafetleriyle, katıldığı güvenli Amazon ormanı kampında tuhaf bir "tık tık" sinyali/mesajı alır. Şiddet içermeyen bu macerada, çocuğumuz vahşi hayvanların uzaktan verdikleri görsel/hareket ipuçlarını birbirine bağlayarak kayıp ve yalnız bir hayvan yavrusuna ulaşır. Heyecanlı, koşturmacalı ama hayvan tehlikesi/korkusu olmayan (her tehlikeli hayvan güvenli mesafededir), biyolojik çeşitlilik ipucu dolu bir keşif öyküsü yaz.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Amazon'un Gizli Çağrısı" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, ritimli ve 5-10 yaş aralığında merak uyandırıcı olmalıdır. 
- Her sayfa sonunda küçük bir merak kırıntısı bırak. 
- Bilgi yığını yapma; hayvanların özelliklerini, çocuğun ipucu ve harita ögesi olarak hissetmesine yardımcı olarak entegre et.

---

### Bölüm 1 — Gizemli Ritim (Sayfa 1-3)
- Sayfa 1: {child_name} ormanın her köşesinden inanılmaz bitki kokuları ve kuş ıslıkları yükselen, yemyeşil güvenli Amazon kampına büyük bir heyecanla adım atar. Tam o an dev ağaçların arasından "tık tık... tık!" diye ritmik, garip bir sinyal duyar.
- Sayfa 2: Başını kaldırıp dikkatle dinlediğinde o tok ritmin bir hayvanın adımı değil, sanki uzaklardan gelen zekice bir ısrar mesajı olduğunu anlar. Yanındaki deri çantasını düzeltirken kendi kendine fısıldar: "Bu bir işaret olabilir mi?"
- Sayfa 3: Kamptaki yaşlı rehber gülümseyerek "Ormanda hiçbir ses nedensiz değildir, her fısıltı sana bir şey anlatır" der. Tık-tık seslerinin geldiği kalın lianaların (sarmaşık) sarktığı yola doğru cesaretle yürüme kararı alır.

### Bölüm 2 — Nehir ve Çamur İzleri (Sayfa 4-6)
- Sayfa 4: Gizemli sesi takip ederken ulaştığı çamurlu nehrin pembeleşen sularında, muazzam bir pembe nehir yunusu (boto) hava almak için aniden sıçrar. Yunus suyun belli bir akış yönünü gösterircesine neşeyle burnunu savurup kaybolur, rota bellidir!
- Sayfa 5: Suyun işaret ettiği yöne yürürken sinyal sesi artık çok daha güçlü gelmeye başlar fakat çocuk duraksar. Yumuşak çamurun üzerinde yüzlerce farklı karmaşık iz birbirine girmiştir, acaba doğru yol hangisidir?
- Sayfa 6: O anda dev yaprakların arasından yavaşça çıkan tonton bir kapibara, karmaşayı hiç umursamadan ormanın en net ve sakin ayak izlerini toprağa çıkarak sakince karşıya geçer. Çocuk anlar: "Onun gibi sakin olmalı, karışıklıktaki net izleri okumalıyım."

### Bölüm 3 — Desenin Sırrı (Sayfa 7-10)
- Sayfa 7: Çamur izi bittiği anda dev ağaçların en tepesinden koca gagalı bir tukan yüksek bir edayla bağırır. Renkli tukan bilerek mi yaptı bilinmez ama büyük, parlak lekeli bir meyveyi çocuğun hemen önüne ormana düşürüverir.
- Sayfa 8: Meyveninki sıradan bir leke değildir, çocuğumuz yaprağın ışığındaki bu lekelerde az önce duyduğu ritmin "şeklini" görür gibi olur: Üç nokta ve bir çizgi! Ama ses asıl başka yönden ona gelmektedir.
- Sayfa 9: Dikkatle o yöne baktığında, uzak bir yaprağın üzerinde göz alıcı parlaklıkta çok ufak bir zehirli ok kurbağası parıldar. Çocuk kurbağadaki uyarıcı desenlerin, meyvedeki sırayla tamamen aynı olduğunu görüp, "Bu işaret bana hem yolu hem de dokunmadan uzaktan durmayı öğretiyor" der.
- Sayfa 10: Kurbağanın gösterdiği yöndeki üç leke-bir çizgi şeklindeki ağaç kökünü geçerken zihnine kaydettiği kod işe yaramıştır. Ama ses bir anda yön değiştirmiş ve "tık-tık-tık... zzz!" diye yepyeni ve daha hızlı bir sinyale dönüşmüştür.

### Bölüm 4 — Ormanın Rehberleri (Sayfa 11-14)
- Sayfa 11: Zemin birden canlanmış gibi harekenlenince, yaprak kesen devasa karıncaların kendilerinden büyük yapraklarla çizgi gibi muazzam bir otoban kurduklarını görür. "İşte benim canlı ve hareketli haritam," diyerek karınca hattını sessizce izlemeye başlar.
- Sayfa 12: Bu canlı hat onu, oldukça derin görünen ıslak bir dereciğin üzerine gerilmiş o ufacık ve sallantılı liana (sarmaşık) köprüsüne getirir. Kalbi güm güm atarak dengede kalmaya odaklanıp rüzgarda dikkatle karşıya geçer.
- Sayfa 13: Köprüyü aştığında yukardaki dallardan birinde ters asılı, çok sevimli "üç parmaklı bir tembel hayvan" ona adeta yavaş adımlarla ileriyi işaret ediyordur. Kahramanımız bir ağaç köküne çıkıp tembel hayvan gibi "yüksekten, paniksiz bakmanın" yeni bir daha gizli yolu açtığını fark eder.
- Sayfa 14: Yol çok karanlıklaşınca uzakların pusunda beliren ulu bir Jaguarın güçlü sesi ve yalnızca göz kamaştırıcı ince silüeti geçer. Kahramanımız ona güvenli bir saygı mesafesinden bakar, rehberinin sözünü hatırlar; ormanın gizemli korkusu değil, sadece dikkatli olunması gereken kalbidir.

### Bölüm 5 — Sinyalin Kaynağı (Sayfa 15-18)
- Sayfa 15: Jaguarın süzüldüğü aralıktan güneş ışıkları vurunca, tık-tık sesi birden kesilir ve onun yerini çok daha cılız, ince bir "cıvıltı" andıran ses alır. Çocuğun kalbine bu sesin bir sinyal değil, çaresiz bir 'yardım çağrısı' olduğu hissi doğar!
- Sayfa 16: İlerideki o kocaman, iç içe geçmiş yaprak kümesinin arasına indiğinde, korkuyla titreşen ve sürüsünden ayrılmış minicik bir yavru tukan bulur. Baştan beri ormanda yankılanan o ritmik sinyal, tamamen savunmasız bu minik yavruyu kurtarma çağrısıdır.
- Sayfa 17: Yavruyu daha da korkutmamak için Indiana Jones bilgeliğiyle elini çok yavaşça uzatır ve yavru güvende olduğunu anlayınca çocuğun çantasının dış kayışına atlayıverir. Yavru uzaklardaki kocaman çiçekli gür bir çalıya doğru hüzünle "cıvk" diyerek bakmaktadır.
- Sayfa 18: Çocuğumuz hemen aklındaki yapbozu kurar; karıncaların döndüğü yön ile kurbağadaki üç noktalı çiçeğin deseni o dev çalılıkları işaret etmektedir. Vakit kaybetmeden patikayı aşar ve çalıların arkasındaki o tertemiz büyük yeşil düzlüğe varır.

### Bölüm 6 — Tamamlanma (Sayfa 19-21)
- Sayfa 19: Düzlüğün bittiği aydınlık nehir kenarında, yetişkin dev tukan sürüsü telaş içinde tur atmaktadır (Güvenli, zarar vermeyen atmosfer). Yavru kuş inanılmaz bir sevinçle anında kanat çırparak oraya, güvenle ailesinin dallarına döner kavuşur.
- Sayfa 20: Tam o an arkasından usulca kamp rehberi yetişir ve büyük bir gururla "Ormanı dinlemeyi harika başardın!" der. Amazonun gizemli yeşilliğinde yankılanan o acı dolu çağrı tamamen susmuş, yerini huzurlu bir nehir şırıltısına bırakmıştır.
- Sayfa 21: Yere bakınca tukan tüyleriyle kaplı ufak pırıl pırıl, kırmızı bir tohum görür, onu kocaman bir anı olarak şapkasına takar. Kahramanımız gülümser, "Amazon’un sırları hiçbir zaman bitmez..." Acaba yarınki sinyal nerede yankılanacaktır?

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 21 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child creeping slowly behind capybara tracks", "Child balancing carefully across hanging liana bridge").
- Bu hikaye tehlikeli saldırılar veya korku dolu sahneler içermemelidir; hayvanlar (jaguar vb.) sadece uzakta, bir tablo veya silüet gibi, saygı duyulacak figürlerdir.
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

AMAZON_CULTURAL_ELEMENTS = {
    "location": "Amazon Rainforest, dense jungle",
    "historic_site": "Wilderness ecosystem",
    "major_elements": [
        "Kapok trees, hanging lianas, dense ferns",
        "Winding brown river, misty golden sun rays",
        "Pink river dolphins, sloths, poison dart frogs, toucans",
        "Leafcutter ant trails, capybara tracks",
    ],
    "atmosphere": "Lush, adventurous, exotic, safely wild, biodiverse",
    "values": ["Empathy", "Observation", "Respect for Nature", "Resilience"],
    "sensitivity_rules": [
        "NO aggressive animal encounters",
        "Dangerous animals (like jaguars) only far away or as silhouettes",
        "Child remains safe throughout the journey",
        "Action and ecology focus"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

AMAZON_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_amazon_scenario():
    """Amazon senaryosunu yeni Hayvan İzleri ve Gizemli Sinyal Şablonuna göre günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "amazon")
                | (Scenario.theme_key == "amazon_rainforest")
                | (Scenario.name.ilike("%Amazon%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Amazon'un Gizli Çağrısı", is_active=True)
            scenario.theme_key = "amazon"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Amazon'un Gizli Çağrısı"
        scenario.description = (
            "Indiana Jones ruhuyla efsanevi bir ekoloji macerası! "
            "Amazon ormanlarında duyduğu gizemli bir sinyalin peşinden koşan kahramanımızın, "
            "egzotik hayvanların bıraktığı şeffaf izleri birleştirerek yalnız bir yavruyu "
            "kurtarma serüveni."
        )
        scenario.theme_key = "amazon"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = AMAZON_COVER_PROMPT
        scenario.page_prompt_template = AMAZON_PAGE_PROMPT
        scenario.story_prompt_tr = AMAZON_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = AMAZON_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = AMAZON_CUSTOM_INPUTS
        scenario.marketing_badge = "Doğa ve Gizem"
        scenario.age_range = "5-10"
        scenario.tagline = "Ormanı dinle, hayvanların sırrını çöz!"
        scenario.is_active = True

        await db.commit()
        print(f"Amazon 'Gizli Çağrı' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_amazon_scenario())
