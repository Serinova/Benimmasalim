# Amazon Ormanları Keşfediyorum Senaryosu - İmplementasyon Raporu

## Özet

"Amazon Ormanları Keşfediyorum" senaryosu başarıyla sisteme eklenmiştir. Bu senaryo:

- ✅ Style-agnostic (tüm görsel stillerle uyumlu)
- ✅ Page-count-agnostic (esnek sayfa sayısı desteği)
- ✅ Wide-angle composition (geniş açılı, çevre odaklı çekim)
- ✅ Animal visibility (hayvanlar net ve görünür)
- ✅ Biodiversity focused (biyolojik çeşitlilik eğitimi)
- ✅ Child-safe content (yaşa uygun, güvenli içerik)

## Oluşturulan Dosyalar

### 1. Senaryo Güncelleme Script'i
**Dosya:** `backend/scripts/update_amazon_scenario.py`

Bu script şunları içerir:
- Cover prompt template (stil-bağımsız)
- Page prompt template (stil-bağımsız)
- Story prompt (TR - Gemini için)
- Custom inputs schema (3 özelleştirme seçeneği)
- Scenario-specific outfits (kız ve erkek)
- Cultural elements (Amazon özel mekanlar ve hayvanlar)

### 2. Admin API Endpoint
**Dosya:** `backend/app/api/v1/admin/scenarios.py`
**Endpoint:** `POST /api/v1/admin/scenarios/scripts/update-amazon`

Bu endpoint senaryoyu veritabanına ekler veya günceller.

### 3. PowerShell Script (Opsiyonel)
**Dosya:** `scripts/run-amazon-update.ps1`

Admin JWT token ile endpoint'i çağırmak için yardımcı script.

## Senaryonun Özellikleri

### Prompt Templates

#### Cover Prompt
- Massive tree roots, kapok trees
- Flying macaws and toucans
- Winding brown river
- Multi-layered canopy
- Golden god rays through mist
- Child on lower third, looking into forest

#### Page Prompt
- Authentic Amazon flora: kapok trees, strangler figs, lianas, bromeliads
- Rich fauna: macaws (pairs), pink river dolphins, sloths, toucans, leafcutter ants, morpho butterflies
- Water features: tributary rivers (tea-brown), flooded forest (igapó)
- Layered canopy structure (emergent, canopy, understory, forest floor)
- **Critical:** Animals "clearly visible and recognizable, NOT hidden in foliage"
- **Composition:** Wide shot (child 25-30%, environment 70-75%)

#### Story Prompt (TR)
- 4 ana hayvan grubu:
  - Scarlet macaw ailesi → Aile bağları, yardımlaşma
  - Pembe nehir yunusu (boto) → İletişim, rehberlik
  - Üç parmaklı tembel → Sabır, herkesin kendi hızı var
  - Yaprak kesici karıncalar → İşbirliği, organize çalışma
- Mini bilgiler (ansiklopedik değil, hikayeye gömülü)
- Şiddetsiz, güvenli, pozitif ton
- Yaş uygun dil

### Custom Inputs

1. **favorite_animal** (En Sevdiği Hayvan)
   - Renkli Papağan (Macaw)
   - Pembe Nehir Yunusu
   - Ağaç Tembeli
   - Toucan (Gagalı Kuş)
   - Mavi Kelebek

2. **helper_tool** (Yardım Aracı)
   - Harita ve Pusula
   - Dürbün ve Not Defteri
   - Su Matarası
   - Sihirli Fener

3. **jungle_mission** (Orman Görevi)
   - Kayıp Yavruyu Ailesine Ulaştır
   - Gizli Su Kaynağını Keşfet
   - Dev Ağacın Sırrını Çöz
   - Orman Haritasını Tamamla

### Kıyafetler (Scenario-Specific)

**Kız:**
```
khaki explorer vest over light green breathable shirt, 
cargo shorts with multiple pockets, sturdy brown hiking boots, 
small binoculars around neck, fabric hat with mosquito net
```

**Erkek:**
```
olive green explorer shirt with rolled-up sleeves, 
khaki cargo pants with zippered pockets, brown leather hiking boots, 
canvas backpack with water bottle, wide-brim explorer hat
```

### Cultural Elements (JSON)

- **Landmarks:** giant kapok trees, winding tributary rivers, multi-layered canopy, flooded forest (igapó), strangler figs
- **Fauna:** scarlet macaws, pink river dolphins, sloths, toucans, leafcutter ants, poison dart frogs, morpho butterflies, capybaras
- **Flora:** kapok/ceiba trees, bromeliads, orchids, hanging lianas, strangler figs, dense ferns
- **Color palette:** deep emerald green, vibrant scarlet, electric blue, golden amber, jade, warm brown
- **Educational themes:** biodiversity, ecosystem layers, animal behavior, conservation

### Varsayılan Ayarlar

- **default_page_count:** 22
- **display_order:** 12
- **location_en:** "Amazon Rainforest"
- **theme_key:** "amazon_rainforest"

## Senaryoyu Aktifleştirme Adımları

### Yöntem 1: Admin Panel API Çağrısı (Önerilen)

1. Admin paneline giriş yap
2. Browser Developer Tools'u aç (F12)
3. Console'a git
4. Şu kodu çalıştır:

```javascript
// Get admin token from localStorage
const token = localStorage.getItem('authToken');

// Call the update endpoint
fetch('https://benimmasalim-backend-554846094227.europe-west1.run.app/api/v1/admin/scenarios/scripts/update-amazon', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(res => res.json())
.then(data => console.log('✅ Success:', data))
.catch(err => console.error('❌ Error:', err));
```

5. Console'da `✅ Success` mesajını gör
6. Senaryolar sayfasını yenile
7. "Amazon Ormanları Keşfediyorum" senaryosu listelenecek

### Yöntem 2: PowerShell Script

```powershell
cd scripts
.\run-amazon-update.ps1
```

Token istendiğinde admin JWT token'ı yapıştır (Browser DevTools > Application > Local Storage > authToken).

### Yöntem 3: Doğrudan Veritabanı (Cloud Run Job)

```bash
gcloud run jobs execute benimmasalim-backend-shell \
  --project gen-lang-client-0784096400 \
  --region europe-west1 \
  --command "python,-m,scripts.update_amazon_scenario"
```

## Test Senaryoları

### Test 1: Default Storybook Style
1. Admin'den yeni sipariş oluştur
2. Senaryo: Amazon Ormanları Keşfediyorum
3. Stil: Default Storybook
4. Sayfa sayısı: 22 (default)
5. Kontroller:
   - ✓ Hayvanlar net görünüyor mu?
   - ✓ Wide shot kompozisyon mu?
   - ✓ Kıyafet tutarlı mı?
   - ✓ Amazon flora/fauna doğru mu?

### Test 2: Watercolor Style
1. Aynı senaryo, farklı stil
2. Stil: Watercolor
3. Kontroller:
   - ✓ Stil doğru enjekte edildi mi?
   - ✓ Template değişkenleri çalışıyor mu?

### Test 3: Custom Inputs
1. Özelleştirme seç:
   - favorite_animal: "Pembe Nehir Yunusu"
   - helper_tool: "Dürbün ve Not Defteri"
   - jungle_mission: "Kayıp Yavruyu Ailesine Ulaştır"
2. Kontroller:
   - ✓ Hikayede pembe yunus öne çıkıyor mu?
   - ✓ Dürbün vurgulanıyor mu?
   - ✓ Kayıp yavru görev ana tema mı?

## Kalite Kontrol Kriterleri

### Composition Check
- ✓ Child occupies 25-30% frame
- ✓ Full body visible (head to feet, both legs)
- ✓ NOT close-up or portrait
- ✓ Environment dominant (70-75%)

### Animal Visibility Check
- ✓ Animals clearly recognizable
- ✓ NOT hidden in foliage blur
- ✓ Accurate proportions and colors

### Style-Agnostic Check
- ✓ Template uses only {character}/{scene} variables
- ✓ NO hardcoded style terms
- ✓ Style injected via BookContext

### Safety Check
- ✓ NO scary/threatening animals
- ✓ NO violence or danger
- ✓ Age-appropriate content

## Sistem Entegrasyonu

### Mevcut Sistemle Uyumluluk

✅ **Order Config Service:** `default_page_count` priority cascade ile çalışır  
✅ **Outfit Resolution:** `outfit_girl` ve `outfit_boy` sistemde doğru çözülür  
✅ **Visual Style System:** Tüm stillerle uyumlu (DB + hardcoded fallback)  
✅ **Prompt Composer:** `{clothing_description}`, `{scene_description}` değişkenleri  
✅ **Character Bible:** Face analysis + outfit locking sistemiyle uyumlu  
✅ **Negative Prompts:** Mevcut anti-close-up, anti-text kurallarına uyumlu  

### Kullanılan Servisler

- `gemini_service.py`: Story generation (V3 pipeline primary)
- `gemini_consistent_image.py`: Image generation with Gemini 2.5 Flash
- `visual_prompt_builder.py`: Prompt enhancement and character locking
- `order_config_service.py`: Page count and configuration resolution
- `page_builder.py`, `cover_builder.py`: Template rendering

## Deployment Status

✅ **Backend:** Deployed to `benimmasalim-backend-00323-rtt`  
✅ **Script:** `backend/scripts/update_amazon_scenario.py` included in image  
✅ **Admin Endpoint:** `/api/v1/admin/scenarios/scripts/update-amazon` active  
🔄 **Scenario in DB:** Needs activation (run admin endpoint)  

## Sonraki Adımlar

1. ✅ Admin endpoint'i çağır (yukarıdaki JavaScript kodu ile)
2. ✅ Admin panel'de senaryoyu kontrol et
3. ✅ Test hikayesi oluştur (3 farklı stil)
4. ✅ Custom inputs test et
5. ✅ Hayvan görünürlüğü ve kompozisyon kontrol et
6. ✅ Production'a aç (is_active=true)

## Risk Değerlendirmesi

### Düşük Risk
- Senaryo yapısı mevcut pattern'leri takip ediyor (Kapadokya, Efes benzeri)
- Template'ler stil-bağımsız
- Sayfa sayısı esnek (sistem zaten destekliyor)

### Orta Risk - Mitigasyonlu
- **Hayvan görünürlüğü:** Amazon yoğun bitki örtüsü hayvanları gizleyebilir
  - **Mitigasyon:** Explicit "clearly visible, NOT hidden" promptları
  - **Test:** 3 stil ile validate et

### Test Kapsamı
- 3 stil smoke testleri (Default, Watercolor, Adventure Digital)
- Custom inputs injection testi
- Page count flexibility testi
- Composition rules validation

## Teknik Notlar

### Style Injection Flow
```
User Selection → VisualStyle.prompt_modifier 
  → BookContext.style 
  → PromptComposer 
  → cover_builder / page_builder
```

Template render edildikten SONRA `ctx.style.anchor`, `ctx.style.leading_prefix`, `ctx.style.style_block` ile enjekte edilir.

### Outfit Resolution Priority
```
1. Scenario.outfit_girl / outfit_boy (highest)
2. Product.custom_clothing (if linked)
3. Fallback generic outfit
```

### Page Count Resolution Priority
```
1. Request.page_count (user input)
2. Scenario.linked_product.default_page_count
3. Scenario.default_page_count (22 for Amazon)
4. Product.default_page_count
5. Fallback: 16
```

## Referanslar

- **Plan Dosyası:** `c:\Users\yusuf\.cursor\plans\amazon_ormanları_senaryosu_1930d69d.plan.md`
- **Script Dosyası:** `backend/scripts/update_amazon_scenario.py`
- **Admin API:** `backend/app/api/v1/admin/scenarios.py` (line 879+)
- **Kapadokya Örneği:** `backend/scripts/update_kapadokya_scenario.py`

---

**Oluşturulma Tarihi:** 2026-02-25  
**Son Deployment:** benimmasalim-backend-00323-rtt  
**Status:** ✅ Ready for activation
