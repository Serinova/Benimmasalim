"""
Masal Dünyası: Rüya Anahtarı — Gizem, Macera, Büyülü Atmosfer
=============================================================================================
- Kitap adı: [Çocuk adı]'ın Masal Dünyası: Rüya Anahtarı (alt başlık yok)
- Eski bir masal kitabından düşen rüya anahtarıyla açılan kapıdan geçerek Masal Ağacı'nı kurtarma macerası
- Yerler: Uçan adalar, Bulut Köprüsü, Şeker Ormanı, Kristal Göl, Masal Ağacı
- Kıyafet: Masal kâşif kıyafeti (zümrüt yeşili pelerin), kız ve erkek için zorunlu ve her sayfada aynı tutarlı (kıyafet kilidi)
- Kurguyu bozabilecek kullanıcı seçenekleri yok (custom_inputs boş)
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (AI DIRECTOR - PASS 2)
# ============================================================================

FAIRY_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child holding a glowing magical key. "
    "Background features majestic floating islands, sparkling fairy lights, and dreamy clouds. "
    "Dynamic angle, enchanting magical lighting. Wide shot: child 30%, environment 70%. Whimsical, fairytale adventure atmosphere. {STYLE}"
)

FAIRY_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [floating islands, glowing fairies, sparkling particles, talking animals, tiny dragon, candy forest, crystal lake, flying fish, star dust]. "
    "Fill scenes with magical elements and fairytale wonder. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera. "
    "child wearing an emerald green cloak and carrying a small satchel, dynamic action, full body visible. "
    "Avoid: photorealistic, pasted face, collage, duplicate child, random text, watermark, logo, blurry, low quality. {STYLE}"
)

# ============================================================================
# OUTFIT — Masal Kaşif Takımı (Kesin Kilidi)
# ============================================================================

OUTFIT_GIRL = (
    "fairytale explorer outfit for a child: emerald green cloak with a small hood, light brown tunic, "
    "dark leggings, comfy boots, a small leather satchel, and a tiny glowing lantern charm, no logos, plus a small star hairpin. "
    "EXACTLY the same outfit on every page — same green cloak, same brown tunic, same boots. "
    "Same child character, consistent face and hair across all pages."
)

OUTFIT_BOY = (
    "fairytale explorer outfit for a child: emerald green cloak with a small hood, light brown tunic, "
    "dark leggings, comfy boots, a small leather satchel, and a tiny glowing lantern charm, no logos. "
    "EXACTLY the same outfit on every page — same green cloak, same brown tunic, same boots. "
    "Same child character, consistent face and hair across all pages."
)

# ============================================================================
# STORY BLUEPRINT — Rüya Işığı ve Masal Ağacı Bulmacaları (PURE AUTHOR - PASS 1)
# ============================================================================

FAIRY_STORY_PROMPT_TR = """
# MASAL DÜNYASI: RÜYA ANAHTARI

## YAPI: {child_name} okuduğu kitabın içinden düşen sihirli Rüya Anahtarı sayesinde duvarında beliren kapıdan Masal Dünyası'na adım atar. Renksizleşen Masal Ağacı'nı kurtarmak için kahkaha tozu ve rüya ışığını bulması gerekmektedir. Bulut köprüsündeki şaşırtmacaları geçip, Şeker Ormanı ve Kristal Göl'de ipuçlarını tamamlar. Şiddet, korkunç canavarlar veya karanlık temalar KESİNLİKLE YOKTUR. Çok yaratıcı, gizemli ve parlak fantastik çocuk aksiyonudur.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Masal Dünyası: Rüya Anahtarı" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili pırıl pırıl, sürükleyici, gizemli ve eğlencelidir.
- Sayfaların sonunda küçük merak kırıntıları bırak. Bolca masalsı obje (şeker ağaçları, su perileri, ışık küreleri, uçan balıklar vd.) kullan.

---

### Bölüm 1 — Sihirli Kapı (Sayfa 1-3)
- Sayfa 1: {child_name} odasında eski bir masal kitabını okurken sayfaların içinden aniden altın renginde pırıl pırıl parlayan gizemli bir ışık huzmesi fırlar. Sayfalar kendi kendine hızla dönerken kitabın tam ortasından minik, üzeri yıldız desenli bir "Rüya Anahtarı" "tık" diye kucağına düşüverir!
- Sayfa 2: Anahtarı usulca avucuna aldığında eline sıcacık, tatlı bir karıncalanma yayılır. O eşsiz anahtarı hiç düşünmeden boşlukta çevirdiği anda, odasının düz duvarında ışıl ışıl parlayan devasa bir sayfa kapısı ardına kadar açılır.
- Sayfa 3: {child_name} o ışıltılı kapıdan büyük bir cesaretle adım atar atmaz kendini havada süzülen koca uçan adaların tam üstünde bulur! Ayaklarının altından yumuşacık bulutlar hızla akarken şaşkınlıkla fısıldar: "İnanamıyorum, bir masalın bizzat içine düştüm!"

### Bölüm 4 — Tavşanın Çağrısı (Sayfa 4-6)
- Sayfa 4: Tam o an uzun kulaklı, zıplayarak neşeyle ama biraz da telaşla koşan mavi yelekli, konuşan bir tavşan yanına gelir. "Yardımına ihtiyacımız var kâşif! Harika Masal Ağacı soluyor, çünkü neşe kaynağımız 'rüya ışığı' kayboldu!" der.
- Sayfa 5: Çok uzakta devasa kollarına rağmen yaprakları şeffaflaşıp solgunlaşan büyük Masal Ağacı hüzünlü şekilde görünmektedir. Tavşan o eşsiz rüya ışığını bulması için ona üç zorlu yol gösterir: Bulut Köprüsü, Şeker Ormanı ve Kristal Göl.
- Sayfa 6: Zaman kaybetmeden doğruca havada salınan Bulut Köprüsü'ne koşar; ama bu köprünün koca pamuk taşları şiddetli rüzgarla dans edercesine sallanmaktadır. Üstelik o geveze pofuduk taşlar, komik şarkılar söyleyerek çocuğun kafasını ve yönünü şaşırtmaya çalışır!

### Bölüm 7 — Rüzgarın Ritmi (Sayfa 7-9)
- Sayfa 7: Zeki kâşifimiz o aldatıcı şarkılara kulak tıkayarak gözlerini yumar ve sadece okyanus gibi esen nazik rüzgarın gerçek ritmini dinleyerek doğru pamuksu taşlara bir bir sıçrar. Karşıya geçtiğinde havada uçan gümüş bir balık ilk sihirli ipucunu ağzından bırakır: "Işık, kahkahanın peşinden gider."
- Sayfa 8: İkinci durak olan Şeker Ormanı'na daldığında etrafını kocaman lolipop ağaçlar, jelibon çalılar ve kanatları pırıl pırıl eden şeker kelebekler sarar. Fakat ormandaki tüm o tatlı pembe yollar birbirinin tıpatıp aynısıdır; burada sonsuza dek kaybolmak işten bile değildir!
- Sayfa 9: Şaşkınlıkla etrafına bakarken turuncu pullu, avuç içi kadar küçücük bir ejderha pırpır ederek yanına gelir; ateş yerine sadece simli bir parıltı üflemektedir. Zeki küçük ejderha, parıltısıyla yere çok kısa ama ışıltılı bir ok çizer: "Beni takip et, bu taraftan!"

### Bölüm 10 — Şeker Şifresi (Sayfa 10-12)
- Sayfa 10: O simli oku şevkle takip eden kahramanımız çikolatadan devasa bir sınır kapısına ulaşır, ancak kapı sımsıkı kilitlidir. Kapının üstündeki renkli kilit yuvasında koca üç sembolün sırasıyla boş durduğunu görür: Kalp, yıldız ve ay!
- Sayfa 11: Mükemmel bir dikkatle hemen etrafı arayan çocuk, çalıların altında çok gizli kalp şeklinde bir şeker, üst dallarda bir şişe yıldız tozu ve en sonda hilal şeklinde bir ay kurabiyesi bulur. Objelere bakıp doğru şifre sırasını çözdüğü anda kapı şekerimsi bir kokuyla ardına kadar açılır.
- Sayfa 12: Kapının ardındaki pamuk şeker masanın tam üzerinde, üstünde "Kahkaha Tozu" yazan, içi kıkırdayan altın baloncuklarla dolu sihirli bir minik kavanoz onu bekliyordur. Ve hemen yanında gümüş bir yaprağın üzerinde ikinci ipucu yatıyordur: "Toz, suyun aynasında parlar."

### Bölüm 13 — Yansıma Oyunu (Sayfa 13-16)
- Sayfa 13: {child_name} o harika kavanozu sımsıkı cebine koyup koşarak kocaman, ayna gibi pürüzsüz ve cam gibi parlayan Kristal Göl'e varır. Gölün o dingin suyunun tam üzerinde masmavi kanatlı dev uçan balıklar şakıyarak neşeyle sıçramaktadır.
- Sayfa 14: Gölün çok ilerisinde, tam ortasındaki adacıkta asıl aradığı o muazzam "Rüya Işığı" küresi pırıl pırıl parıldıyordur; ama ona doğru heyecanla su kıyısındaki kayalardan yaklaşınca, küre adeta bir oyun gibi yer değiştirmeye başlar!
- Sayfa 15: Kahramanımız bunun kocaman yanıltıcı bir "yansıma ve sihir oyunu" olduğunu anlayarak belindeki küçük fener charm'ını (nazarlığını) çıkarıp güçlü ışığını gölün serin suyuna doğru tutar. Böylece illüzyon olan sahte yansımalar suya karışır ve o asıl gerçek Rüya Işığı'nın yeri apaçık belli olur.
- Sayfa 16: İşe yaradığını görünce sudaki irili ufaklı nilüfer taşlarının üzerinden inanılmaz çevik adımlarla atlayarak gölün kalbine doğru ilerler. Ama o esnada gökyüzündeki sisli bulutlar hızla gölün üstüne kapanmaya başlayarak zamanla büyük bir yarış başlatır!

### Bölüm 17 — Son Birleştirme (Sayfa 17-19)
- Sayfa 17: Sisteki son andaki dev sıçrayışıyla adacığa varıp o paha biçilmez sıcak "Rüya Işığı" küresini ellerinin arasına kapıverir. Fakat dönüş için atladığı taşların üzeri tamamen yoğun ve pembe bir sisle örtülerek çıkış yolunu bir duvar gibi gizlemitşir.
- Sayfa 18: Çantasındaki ışık huzmesinin parlamasıyla, ona ilk başta yardım eden mavi yelekli tavşan ve minicik sevimli parıltı ejderhası sisleri aralayarak koşturup gelirler. Parçaları birleştiren {child_name} bağırır: "Anladım! Kahkaha Tozu ve Rüya Işığı birlikte parlamak zorunda!"
- Sayfa 19: Gölgeleri yırtarak hep birlikte coşkuyla Masal Ağacı'nın o devasa hastalanmış köklerinin tam dibine varırlar. Kahramanımız elindeki altın Kahkaha Tozu'nu gökyüzüne serperek, o sıcacık Rüya Işığı'nı ağacın tam kalbine ustaca ve sevgiyle yerleştirir; o an etraftaki her şey fena halde titremeye başlar!

### Bölüm 20 — Renklerin Dönüşü (Sayfa 20-22)
- Sayfa 20: Masal Ağacı derin bir nefes alır gibi "vuuuh!" diye canlanarak tüm solgun yapraklarına göz kamaştıran rengarenk bir hayat fışkırttı. Gökyüzündeki tüm bulutlardan pırıl pırıl altın rengi yıldız tozları bir müzik eşliğinde yağarken, tüm Masal Dünyası büyük kıkırdamalarla kocaman bir gülümsemeye bürünür!
- Sayfa 21: Çocuğumuz o büyük, sıcacık görevi tamamlamanın haklı gururuyla cebinden ilk baştaki "Rüya Anahtarı"nı çıkarıp karanlığa doğru "tık" diye çevirerek masal kapısını aralar. Yüzünde mutlu bir tebessüm, üzerinde yıldız tozlarıyla güvenle odasına geri döner.
- Sayfa 22: Odasındaki pencereden içeri süzülen ayışığıyla beraber cebine baktığında, o muazzam anahtar gerçek bir yıldız parçası gibi son bir kez tatlıca parlayıp huzurla sessizleşir. {child_name} onu masasının en özel yerine koyarken fısıldar: “Acaba bir gün başka bir maceranın masal kapısı beni bekler mi?”

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 22 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child leaping over fluffy clouds", "Child decoding symbols on a candy door").
- Hayvanların korkunçluğu YOK, ejderhalar çok sempatik ve küçücük olmalıdır.
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

FAIRY_CULTURAL_ELEMENTS = {
    "location": "A Magical Dreamland with Floating Islands",
    "historic_site": "Fairy Tale Kingdom",
    "major_elements": [
        "A magical golden Dream Key",
        "Giant flying islands and bouncy cloud bridges",
        "A sweet Candy Forest and a pristine Crystal Lake",
        "A magnificent ancient Fairy Tale Tree"
    ],
    "atmosphere": "Dreamy, highly creative, bright, enchanting, puzzle-driven",
    "values": ["Imagination", "Problem-solving", "Kindness", "Friendship"],
    "sensitivity_rules": [
        "NO scary monsters, NO dark magic",
        "The mystery relies on exploration, light-logic, and sensory play",
        "Child acts as a whimsical explorer saving the magical balance"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

FAIRY_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE FUNCTION
# ============================================================================

async def create_fairy_tale_scenario():
    """Masal Dünyası senaryosunu Rüya Anahtarı gizemiyle günceller veya oluşturur."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "fairy_tale")
                | (Scenario.theme_key == "fairy_tale_world")
                | (Scenario.name.ilike("%Masal D%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4(), name="Masal Dünyası: Rüya Anahtarı", is_active=True)
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Masal Dünyası: Rüya Anahtarı"
        scenario.thumbnail_url = ""
        scenario.description = (
            "Sihirli kapıdan geçme zamanı! Okuduğu eski kitaptan düşen gizemli 'Rüya Anahtarı' ile "
            "uçan adalar ve şeker ormanlarıyla dolu Masal Dünyası'na geçen kahramanımız, "
            "solmakta olan Büyük Masal Ağacı'nı kurtarmak için harika bir göreve çıkıyor."
        )
        scenario.theme_key = "fairy_tale_world"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = FAIRY_COVER_PROMPT
        scenario.page_prompt_template = FAIRY_PAGE_PROMPT
        scenario.story_prompt_tr = FAIRY_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = FAIRY_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = FAIRY_CUSTOM_INPUTS
        scenario.marketing_badge = "Büyülü Macera"
        scenario.age_range = "4-8"
        scenario.tagline = "Anahtarı çevir, Masal Ağacı'nın ışığını geri getir!"
        scenario.is_active = True
        scenario.display_order = 18

        await db.commit()
        print(f"Masal Dünyası 'Rüya Anahtarı' scenario created/updated: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(create_fairy_tale_scenario())
