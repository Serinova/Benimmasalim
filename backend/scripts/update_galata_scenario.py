"""
Galata Macerası — Işık Haritası, Gizem, Indiana Jones Tarzı
=========================================================================================
- Kitap adı: [Çocuk adı]'ın Kayıp Işık Haritası: Galata (alt başlık yok)
- Sürekli değişen dijital/aydınlık bir ışık haritası ile Galata sokaklarında kayıp eşya bulma macerası
- Yerler: Galata Kulesi çevresi, dar sokaklar, renkli merdivenler, kediler, tramvay, banklar
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

GALATA_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child holding a tiny glowing brass mini-projector device aimed at the weathered cobblestone, intricate glowing golden light map lines materializing on the stone floor. "
    "Iconic historic Galata Tower rising behind narrow Istanbul streets, warm amber-orange sunset sky, seagulls in flight above the rooftops. "
    "Rich golden hour backlighting casting long cobblestone shadows, warm volumetric sunset haze, soft rim light on the child and the glowing device. "
    "Dynamic street-level angle: child 30% foreground, tower and atmospheric streetscape 70%. "
    "Istanbul evening palette: warm amber sunset, golden cobblestone, rich burgundy building facades, soft purple twilight sky."
)

GALATA_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Galata Tower area, Istanbul, narrow cobblestone streets, steep colorful stairs, street cats, cozy cafes, warm sunset light, lively crowd, seagulls]. "
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
# STORY BLUEPRINT — Işık Haritası ve Gizem Temalı Kurgu (PURE AUTHOR - PASS 1)
# ============================================================================

GALATA_STORY_PROMPT_TR = """
# GALATA'NIN KAYIP IŞIK HARİTASI: GİZEMLİ MACERA

## YAPI: {child_name} Indiana Jones tarzı kıyafetleriyle Galata sokaklarında gezerken bulduğu sokak sanatçısına ait sihirli/teknolojik bir "ışık dürbünü" sayesinde yerlere yansıyan haritayı takip ederek heyecanlı bir kayıp eşya arama macerasına atılır. Heyecanlı, koşturmacalı, zamanla (gün batımıyla) yarış hissi veren ama tamamen günümüzde geçen, tehlikesiz aile dostu bir kurgu sür. Tamamen günümüzde geçer, IŞINLANMA VE GEÇMİŞE GİTME YOKTUR.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Kayıp Işık Haritası: Galata" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, ritimli ve 5-10 yaş aralığında merak uyandırıcı olmalıdır. 
- Her sayfada küçük bir merak kırıntısı bırak. 
- Bilgi yığını yapma; yokuşlar, sokak kedileri, renkli merdivenler, kafeler ve tramvaylar ipucu noktaları olsun.
- Şiddet yok, korku yok. Sadece eğlenceli ve heyecanlı ipucu takibi var.

---

### Bölüm 1 — Işık Saçan Dürbün (Sayfa 1-3)
- Sayfa 1: {child_name} güneş batarken kalabalık İstanbul Galata Kulesi çevresinde merakla gezinmektedir. Yanından hızla ve telaşla toparlanıp geçen bir sokak sanatçısının çantasından küçük bir nesne seker ve yere düşer.
- Sayfa 2: Hemen eğilip alır; bu, çok farklı tasarlanmış, ucundan ışık saçan pirinç bir "mini ışık aparatı" yani dürbündür. Üzerindeki düğmeye yanlışlıkla basmasıyla yaldızlı taş zemine incecik, parlak çizgiler halinde bir harita yansımaya başlar!
- Sayfa 3: O an az ileride sanatçının acı dolu sesini duyar: "Eyvah! Gözüm gibi baktığım en nadide sahnem için çok önemli o bilekliği düşürmüşüm!" Kahramanımız hiç tereddüt etmeden ışıklı aparattan yardım alarak ona yardım etmeye karar verir.

### Bölüm 4 — Kedi mi Harita mı? (Sayfa 4-6)
- Sayfa 4: Taşların üstündeki parlak ışık haritası titreyerek çok dar, tarihi bir sokağı işaret eden bir ok oluşturur. Çocuk doğru yolda olduğunu hissederek o ince sokağa atılır ama rüzgarla birlikte harita sürekli titremektedir.
- Sayfa 5: Dik yokuş olan renkli merdivenlere gelir, merdivenleri nefes nefese çıkarken ışık haritası birden kaybolur; durup aletin ayarlarıyla oynayınca harita üstteki başka bir taşa atlar.
- Sayfa 6: O taşın üzerinde oturan uykucu bir sokak kedisi yüksek sesle mırıldanarak hızla yana doğru yön değiştirir; sanki ışık onu rahatsız etmiş de yolu o açmış gibidir! Çocuk "Bu kedi bana işareti veriyor olabilir mi?" diye kendi kendine gülümser.

### Bölüm 7 — Yanlış Semboller (Sayfa 7-10)
- Sayfa 7: Kedinin peşine takıldığı gökkuşağı rengindeki merdivenlerin tam köşesinde, yerde çok parlak bir parça görür... ancak yanına gittiğinde bu asıl obje değil, basit, parlayan bir kafe düğmesidir. Asıl parça nerededir?
- Sayfa 8: Işık aparatı bu hatadan ders çıkarırcasına birden mod değiştirir ve yere üç farklı sembol çizer: koca bir yıldız, bir dalga ve bir dönen ok işareti. {child_name} etrafta asılı fenerlerde, duvar çizimlerinde ve tabelalarda bu desenleri fellik fellik arar.
- Sayfa 9: Nihayet semboller sıcacık müzik yayılan bir kafenin eski tuğla duvarında eşleşir ve harita sağa doğru dönen keskin bir oktur. Son saniyede yanlış yokuşa sapmaktan kurtulup ok yönünde keskin bir dönüş yapar.
- Sayfa 10: Sokak sanatçılarının, turistlerin dondurma kuyruklarının olduğu en kalabalık caddeye düşer ve bir anlığına ezilme, yön kaybetme korkusu yaşar. Ama sonra kafasındaki havalı fedorasını düzeltip tam bir Indiana Jones gibi bağırır: "Macera modu devrede!" 

### Bölüm 11 — Raylar ve Ses Dalgaları (Sayfa 11-14)
- Sayfa 11: Uzaktan nostaljik kırmızı bir tramvayın çan sesi duyulur; ışık haritası telaşla tam da tramvay raylarının kenarına doğru sürüklenir. Ama çocuk kuralları çok iyi biliyordur, "Raylara yaklaşmak tehlikeli!" diyerek güvenli kaldırımdan saniye saniye yolu takip eder.
- Sayfa 12: Ara sokağa esen ani sert bir Haliç rüzgarıyla harita bozulup uzayıp giden tek bir çizgiye, ardından da yol ayrımında iki farklı renge bölünür! Hangisi doğru yoldur? Çocuğun saniyeler içinde karar vermesi gerekir.
- Sayfa 13: Zekasını kurcalayıp haritayı dikkatle süzer; çizgilerden biri rüzgar estikçe "titrek" atarken diğeri tamamen "net ve sabit" bir ışık kaynağına sahiptir. Kahramanımız gözünü kırpmadan net çizgiyi seçer.
- Sayfa 14: Hemen sokağın başında canlı keman çalan bir sokak müzisyeni vardır ve müzisyen notayı her değiştirdiğinde ışık haritası yön/tepki değiştirir. "Buldum," diye bağırır çocuk coşkuyla; "Ses frekansları haritayı yönetiyor!"

### Bölüm 15 — Hedefe Doğru (Sayfa 15-18)
- Sayfa 15: Müzisyenin yanına koşup, "Lütfen, aynı notayı 3 saniye hiç değiştirmeden çalar mısınız?" diye rica eder. Müzisyen şaşırarak notaya bastığında, ışık haritası inanılmaz bir netleşmeyle tam hedefi kilitler!
- Sayfa 16: Çarpıcı ışığın noktalandığı yer büyük bir heykeller satan hediyelik eşya arabasının en karanlık arka tekerleğinin içidir. Kahramanımız yere yatar, pür dikkat karanlığın içinde taşların arasına sıkışan objeye uzanır.
- Sayfa 17: Tozlu taşlardan çeker alır: O can alıcı kayıptır, sanatçının eşsiz sahneleri için kullandığı deri işlemeli bilekliği dir! Ama nedense ışık aparatı henüz uyarı vermeyi bitirmemiştir, cihaz kırmızı ışıkta yanıp söner.
- Sayfa 18: Çünkü bilekliğe ait olan o küçük toka/klips parçası çöpün arkasındaki küçük nostaljik bankın ayağının dibine yuvarlanmıştır! Aparatın çizdiği son bir ok sayesinde, kahramanımız banka koşup altına bakar.

### Bölüm 19 — Geri Dönüş (Sayfa 19-21)
- Sayfa 19: Klips de bulununca tam set eksiksiz tamamlanır; şimdi zamanla ve gün batımıyla yarış başlar. Çocuk elindeki değerleri sımsıkı sıkıp o dik merdivenlerden bir rüzgar kadar hızlı koşa koşa sanatçının standına geri döner.
- Sayfa 20: Derin bir ah çeken sanatçı bilekliğine kavuşunca, paha biçilemez bir hazine bulmuş gibi sevinir ve ona kocaman teşekkür eder. Kahramanımızın kalbinde harika bir gizemi aydınlatmış olmanın, "Başardım!" demenin huzuru vardır.
- Sayfa 21: Tam karanlık çökerken çocuğun elinde tuttuğu o ışık aparatı aydınlatıcı görevini bitirir, usulca taş zemine minicik parlak bir "ışık yıldızı" imzasını basıp kendi kendine söner. Çocuk gözden kaybolan yıldıza gülümser: "Belki de sokakların karanlığında bir gün beni bekleyen yepyeni ışıklı bir macera daha vardır..."

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 21 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child sprinting up steep colorful stairs", "Child examining light map glowing on cobblestone alley").
- Bu hikaye geçmişte geçmez, IŞINLANMA, ZAMAN MAKİNESİ, BÜYÜ vs. ekleme. Teknolojik ve gizemlidir.
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

GALATA_CULTURAL_ELEMENTS = {
    "location": "Galata Tower area, Istanbul, Turkey",
    "historic_site": "Historic Peninsula surrounding Galata Tower",
    "major_elements": [
        "Narrow cobblestone streets, steep colorful stairs, cozy cafes",
        "Lively crowd, street musicians, nostalgic red tram tracks",
        "Street cats exploring the pathways, warm sunset light",
        "A magical mini projector dropping light maps onto the pavement",
    ],
    "atmosphere": "Active, adventurous investigation, cozy evening, contemporary Istanbul",
    "values": ["Helpfulness", "Observation", "Quick Thinking", "Determination"],
    "sensitivity_rules": [
        "Modern day setting, no historical time travel",
        "Safe and friendly adventure, no villains",
        "Action and deduction focus"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

GALATA_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE
# ============================================================================

async def update_galata_scenario():
    """Galata senaryosunu yeni Kayıp Işık Haritası Şehir Dedektifine göre günceller."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "galata")
                | (Scenario.theme_key == "galata_tower_istanbul")
                | (Scenario.name.ilike("%Galata%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Galata'nın Kayıp Işık Haritası", is_active=True)
            scenario.theme_key = "galata"
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Galata'nın Kayıp Işık Haritası"
        scenario.description = (
            "Indiana Jones ruhunu teknolojiyle birleştiren kusursuz bir modern zaman dedektifliği! "
            "Kahramanımızın bulduğu gizemli mini bir projektör cihazının sokaklara yansıttığı ışıklı harita "
            "ile Galata'nın sokaklarında koşarak eşyayı asıl sahibine yetiştirme mücadelesi."
        )
        scenario.theme_key = "galata"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = GALATA_COVER_PROMPT
        scenario.page_prompt_template = GALATA_PAGE_PROMPT
        scenario.story_prompt_tr = GALATA_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = GALATA_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = GALATA_CUSTOM_INPUTS
        scenario.marketing_badge = "Şehir Macerası"
        scenario.age_range = "5-10"
        scenario.tagline = "Işık haritasını izle, nesneyi sen kurtar!"
        scenario.is_active = True

        await db.commit()
        print(f"Galata 'Işık Haritası' scenario updated seamlessly: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(update_galata_scenario())
