"""
Oyuncak Dünyası: Kayıp Kurma Anahtarı — Gizem, Macera, Bulmaca
=============================================================================================
- Kitap adı: [Çocuk adı]'ın Oyuncak Dünyası: Kayıp Kurma Anahtarı (alt başlık yok)
- Bir oyuncak sandığında bulunan kurma anahtarıyla Oyuncak Dünyası'na geçip duran saat kulesini çalıştırma macerası
- Yerler: Blok Şehri, Oyuncak Tren İstasyonu, Robot Atölyesi, Araba Pisti, Pelüş Ormanı, Saat Kulesi
- Kıyafet: Toy-world explorer kıyafeti, kız ve erkek için zorunlu ve her sayfada aynı tutarlı (kıyafet kilidi)
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

TOY_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Child holding a glowing vintage wind-up key. "
    "Background features a giant colorful lego-style city, toy trains, cute robots, and soft plush animals. "
    "Dynamic angle, warm playful lighting. Wide shot: child 30%, environment 70%. Whimsical, adventurous toy kingdom atmosphere. {STYLE}"
)

TOY_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [giant toy kingdom, colorful brick blocks, wooden toy trains, cute bouncing robots, soft plush animals, shiny toy cars, spinning gears]. "
    "Fill scenes with many toys: blocks/lego-like bricks, toy trains, robots, plush animals, toy cars, spinning gears, colorful props. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. Wide angle, full body visible in action, child 30-40% of frame. No eye contact with camera. "
    "child in a bright blue hoodie and red utility vest, dynamic action, full body visible. "
    "Avoid: photorealistic, pasted face, collage, duplicate child, random text, watermark, logo, blurry, low quality. {STYLE}"
)

# ============================================================================
# OUTFIT — Oyuncak Kaşif Takımı (Kesin Kilidi)
# ============================================================================

OUTFIT_GIRL = (
    "child toy-world explorer outfit: bright blue hoodie, red sleeveless utility vest with pockets, "
    "tan shorts, colorful sneakers, a small toy-tool belt, and a tiny headlamp, no logos, plus a small star hair clip. "
    "EXACTLY the same outfit on every page — same blue hoodie, same red vest, same sneakers. "
    "Same child character, consistent face and hair across all pages."
)

OUTFIT_BOY = (
    "child toy-world explorer outfit: bright blue hoodie, red sleeveless utility vest with pockets, "
    "tan shorts, colorful sneakers, a small toy-tool belt, and a tiny headlamp, no logos. "
    "EXACTLY the same outfit on every page — same blue hoodie, same red vest, same sneakers. "
    "Same child character, consistent face and hair across all pages."
)

# ============================================================================
# STORY BLUEPRINT — Kurma Anahtarı ve Dişli Bulmacaları (PURE AUTHOR - PASS 1)
# ============================================================================

TOY_STORY_PROMPT_TR = """
# OYUNCAK DÜNYASI: KAYIP KURMA ANAHTARI

## YAPI: {child_name} odasında bulduğu gizemli kurma anahtarıyla kendini minyatür oyuncakların devasa olduğu renkli bir dünyada bulur. Büyük Saat Kulesi durmuş ve oyuncakların yaşam enerjisi bitmek üzeredir. Çocuk heyecanlı etaplardan (lego köprüsü tamiri, tren rayı seçimi, hızlanan araba takibi ve robot şifreleri) geçerek 3 dişli/parçayı toplar ve kuleyi tekrar çalıştırır. Asla korku veya kötü karakter KESİNLİKLE YOKTUR. Tamamen komik heveslendirici çocuk aksiyonu ve bulmaca macerasıdır.

**BAŞLIK:** Kapak başlığı "[Çocuk adı]'ın Oyuncak Dünyası: Kayıp Kurma Anahtarı" olmalı. Alt başlık EKLEME.

**STİL & TON:** 
- Her sayfa 2 ila 4 kısa cümleden oluşmalıdır. Dili akıcı, enerjik, tempolu ve çok eğlencelidir.
- Sayfaların sonunda çocukları bir sonraki sayfayı çevirmeye motive edecek "Mini Cliffhanger" (küçük merak kırıntıları) bırak. Ormanlar, hayvanlar, kuleler tamamen oyuncak konseptindedir.

---

### Bölüm 1 — Büyülü Geçiş (Sayfa 1-3)
- Sayfa 1: {child_name} gece yarısı odasında dağılmış oyuncaklarını özenle toplarken çalışma masasının en alt çekmecesinde eski, pırıl pırıl parlayan gizemli bir "kurma anahtarı" bulur. 
- Sayfa 2: Karanlık odada anahtarın o büyüleyici ışığına kapılıp onu ihtiyar oyuncak sandığının kilidine yaklaştırdığı an, koca sandıktan harika bir "Klik!" sesi yankılanır. Kapağın altından rengarenk simli bir rüzgar yüzüne doğru esmeye başlar!
- Sayfa 3: {child_name} gözlerini yavaşça açtığında etrafındaki her şey değişmiştir; kendisi ufacık kalmıştır ve etrafında devasa lego binaların, hareket eden trenlerin ve uçuşan pelüşların olduğu muazzam bir Oyuncak Dünyası'na gelmiştir!

### Bölüm 4 — Tehlikeli Duraklama (Sayfa 4-6)
- Sayfa 4: Tam o sırada telaşla koşturan yumuşacık bir pelüş ayıcık nefes nefese yanına gelir ve "Oyuncak Dünyası'nın kalbi olan Büyük Saat Kulesi durdu, kahraman!" diye bağırır. Ayıcık, eğer o altın kurma anahtarının parçaları bulunmazsa tüm dünyanın sonsuza dek donup kalacağını söyler.
- Sayfa 5: Çok ileride, ufukta dondurma külahlarına benzeyen dev Saat Kulesi görünür ama oraya giden yollar tamamen kapalıdır. Önlerinde harika seçeneklerle üç görkemli kapı duruyordur: Blok Şehri, Tren İstasyonu ve Robot Atölyesi... Önce hangisine girmelidir?
- Sayfa 6: Zaman kaybetmeden devasa lego binaların olduğu Blok Şehri'ne cesurca adamını atar. Ama üzerinde yürümek zorunda olduğu rengarenk blok köprünün parçaları çatırdamaya başlayınca, suya düşmemek için acil bir çözüm bulması gerekir!

### Bölüm 7 — Tren İpuçları (Sayfa 7-9)
- Sayfa 7: Zekasıyla lego bloklarının renklerini doğru sıraya dizip şifreyi tamamlayan kahramanımız, köprüyü çelik gibi güçlendirerek karşıya geçer. Orada ilk ipucunu kırmızı bir kutunun içinde bulur, kağıtta kocaman harflerle şöyle yazmaktadır: "RAYLAR KALBE GİDER."
- Sayfa 8: İkinci kapı olan Tren İstasyonu'na girdiğinde vızır vızır küçük trenlerin bir oraya bir buraya geçtiğini, zembereklerin çınladığını duyar. Minyatür şapkalı tatlı bir istasyon şefi ona telaşla "Yanlış raya girersen sonsuza dek kaybolursun ufaklık!" diye uyarır.
- Sayfa 9: Gözlerini yere indiren {child_name}, yerdeki o karmaşık rayların içine çok gizli renk kodlarının işlendiğini fark ediverir. Hiç tereddüt etmeden o doğru rengin parladığı ray üzerinde en hızlı oyuncak trenle nefes kesen mutlu bir yarışa girerek koşmaya başlar.

### Bölüm 10 — Şifreyi Dinlemek (Sayfa 10-12)
- Sayfa 10: Rengarenk rayları şevkle takip ederken, bir anda karşısına çıkan dev bir kavşakta iki büyük ok bulunur: Birinin üzerinde "TİK", diğerinin üzerinde "TAK" yazmaktadır. Çocuk şapkasını hafifçe kaldırıp, saat kulesinin o çok uzaktan gelen zayıf ritmine kulağını verir... Hangisi?
- Sayfa 11: Zekasıyla ritmi eşleştiren çocuk "TAK" tabelasına saparak haklı çıkar ve ikinci ipucunu bulur: "DİŞLİLERİN ŞİFRESİ ÜÇ VURUŞ." Tam o esnada yanından hızla geçen minik komik bir kömür vagonu, havaya fırlattığı gümüş bir "dişli parçasını" ona şapka gibi hediye bırakıverir.
- Sayfa 12: Eksik parçaların sonuncusu için Robot Atölyesi'ne dalar; içerisi zıplayan teneke robotlar, dönen çarklar ve binlerce yanıp sönen komik ışıkla doludur. Karşısında üzerinde dijital ekranı olan, "BİP-BİP-BİP" diyerek arıza veren kilitli bir kapı belirir.

### Bölüm 13 — Arabalı Kovalamaca (Sayfa 13-16)
- Sayfa 13: Kaşifimiz elindeki ikinci ipucunu hatırlar ve mekanizmaya tam "üç vuruş" şifresini tuşlayarak ritmi girer: bip... bip-bip... biiip! Dev çelik kapı inleyerek yana doğru kayar ve içeride saat kulesinin o devasa eksik oyuncak çarkları dönmeye başlar.
- Sayfa 14: Kapı açılır açılmaz atölyeden jet hızıyla fırlayan kırmızı minik ve çılgın bir yarış arabası, son anahtar tamamlama parçasını bagajına kaptığı gibi egzoz dumanı atarak kaçar! "Bekle beni tırmalayacağım!" çocuk da hemen akrobatik bir şekilde onun peşine düşerek adrenalin dolu bir koşuya başlar.
- Sayfa 15: O inanılmaz ve komik Araba Pisti'nde dev rampalar, ters tüneller, bariyerler vardır ama oyuncak dünyasının kahramanı mükemmel zıplayışlarla tüm engelleri bir akrobat gibi aşar. Fakat o hınzır araba karanlık, kocaman ağızlı bir oyun tüneline girerek gözden kaybolur!
- Sayfa 16: Tünelin çıkışı çok daha ilginç bir mekana, pamuk şekeri ağaçların ve zıplayan balon toplarının olduğu yumuşacık, komik bir "Pelüş Ormanı"na açılır. Kahramanımız kırmızı arabanın lastik izlerini o yumuşak şekerleme tozlarının üzerinden mükemmel bir dedektif gibi takip eder.

### Bölüm 17 — Saat Kulesi (Sayfa 17-19)
- Sayfa 17: Nihayet ormanın sonunda, kırmızı yarış arabasının büyük bir elma yumak pamuğu yığınına sıkıştığını bulur ve onu oradan nazikçe kurtararak okşar. Aracın da kornayla "teşekkür" edip parçayı çocuğun avucuna bırakmasıyla eksik halka tamamen bulunmuş olur.
- Sayfa 18: Hiç vakit kaybetmeden tüm parçaları sıkıca tutan çocuk, o kilitli duran dev Saat Kulesi'nin ana kapısına ulaşır; ama kule dişli şekilde son bir kilit yuvası barındırıyordur. Anahtar parçaları ancak doğru takılırsa kilit tamamlanabilecektir!
- Sayfa 19: Kahramanımız zekasını ve elindeki dişlileri sırasıyla yuvalara koyar, "Klik!" diye bir mekanik ses yankılanıverir! O eksik efsanevi kurma anahtarı harika bir ışıkla tamamen bütünleşirken, dev kule saniyeler içinde ışık şovlarıyla aydınlanmaya başlar.

### Bölüm 20 — Canlanan Oyuncaklar (Sayfa 20-22)
- Sayfa 20: Çocuk o harika altın anahtarı kule merkezine hızla ve heyecanla takıp bilek gücüyle ardı ardına çevirir: "tık... tık... tık!" Şehrin tüm kalbi atmaya başlar; donmuş tüm trenler yürür, ayıcıklar zıplar ve koca krallıkta yeniden muazzam, kutlamalı bir müzik patlar!
- Sayfa 21: İlk dostu olan yamalı pelüş ayıcık büyük bir sevgiyle sarılarak teşekkür eder ve çocuğun yeleğine pırıl pırıl minicik bir oyuncak dünya rozeti iliştirir. Çocuğumuz o büyük tatminle gözlerini kapattığında, anında odasının o loş, tanıdık güvenli sessizliğinde sandığının başında bulur kendini.
- Sayfa 22: Elini cebine attığında ayıcığın taktığı o altın oyuncak dünya rozeti cebindedir ve odasındaki tüm o küçük oyuncakları ona göz kırpar gibi duruyordur. Yatağına uzanan kahramanımız, yüzünde kocaman bir gülümsemeyle fısıldar: “Kim bilir... Belki sandık bir gün yine 'klik' eder mi?”

---

## KURALLAR
- Hikayeyi TAM OLARAK {page_count} sayfa yaz. Sayfa 22 bitiminde hikaye kapanır. Toplam TAM 22 sayfa tasarla (1 kapak + 21 iç sayfa).
- AI Görüntü (scene_description) promptlarını (İngilizce) yazarken "standing still" veya "looking at camera" KULLANMA. Aksiyon belirt (örn: "Child leaping over toy train tracks", "Child fixing colorful bricks on a bridge").
- Okyanus, uzay, tehlikeli canavar YOK; sadece mutlu, aksiyonlu ama tam bir OYUNCAK DÜNYASI eğlencesidir.
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

TOY_CULTURAL_ELEMENTS = {
    "location": "Magical Toy World and a child's bedroom",
    "historic_site": "Toy Kingdom",
    "major_elements": [
        "Giant colorful building bricks and a block city",
        "Toy train stations, cute bouncing robots",
        "A giant wind-up clock tower",
        "Plush forests and fast toy cars"
    ],
    "atmosphere": "Energetic, completely playful, whimsical, fast-paced puzzle adventure",
    "values": ["Problem-solving", "Teamwork", "Kindness", "Agility"],
    "sensitivity_rules": [
        "NO frightening monsters or villains",
        "Action is joyous and toy-based (like dodging bouncing balls or chasing toy cars)",
        "Child acts as a clever mechanic/explorer hero"
    ]
}

# ============================================================================
# CUSTOM INPUTS
# ============================================================================

TOY_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE FUNCTION
# ============================================================================

async def create_toy_world_scenario():
    """Oyuncak Dünyası senaryosunu kayıp kurma anahtarı gizemiyle günceller veya oluşturur."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "toy_world")
                | (Scenario.name.ilike("%Oyuncak%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4(), name="Oyuncak Dünyası: Kayıp Kurma Anahtarı", is_active=True)
            db.add(scenario)

        # Meta Bilgiler
        scenario.name = "Oyuncak Dünyası: Kayıp Kurma Anahtarı"
        scenario.thumbnail_url = ""
        scenario.description = (
            "Duran saati kurtarma zamanı! Odasındaki gizemli çekmeceden çıkan kurma anahtarıyla "
            "dev lego binaların, trenlerin ve robotların olduğu muazzam oyuncak dünyasına geçen "
            "çocuğumuzun harika bulmaca macerası!"
        )
        scenario.theme_key = "toy_world"
        
        # Kapaklar ve Promplar
        scenario.cover_prompt_template = TOY_COVER_PROMPT
        scenario.page_prompt_template = TOY_PAGE_PROMPT
        scenario.story_prompt_tr = TOY_STORY_PROMPT_TR
        
        # Kıyafet Sistemi
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        
        # Kültürel & Pazarlama Verileri
        scenario.cultural_elements = TOY_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = TOY_CUSTOM_INPUTS
        scenario.marketing_badge = "Eğlenceli Macera"
        scenario.age_range = "4-8"
        scenario.tagline = "Kurma anahtarını birleştir, oyuncak şehrini kurtar!"
        scenario.is_active = True
        scenario.display_order = 17

        await db.commit()
        print(f"Oyuncak Dünyası 'Kurma Anahtarı' scenario created/updated: {scenario.id}")

if __name__ == "__main__":
    asyncio.run(create_toy_world_scenario())
