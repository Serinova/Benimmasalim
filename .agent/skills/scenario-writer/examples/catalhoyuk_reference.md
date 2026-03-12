# Çatalhöyük Referans — En İyi Senaryo Örneği

> Bu dosya, mevcut senaryolar içinde en iyi kalitedeki Çatalhöyük senaryosunun
> kilit unsurlarını belgeliyor. Yeni senaryolar yazarken bu yaklaşımı baz al.

---

## Neden Çatalhöyük En İyi?

1. **✅ Custom cover_prompt_template** — varsayılan değil, senaryoya özgü
2. **✅ Custom page_prompt_template** — atmosfer öğeleri listesi var
3. **✅ story_prompt_tr'de GÖRSEL ÇEŞİTLİLİK kuralı** — kamera açısı çeşitliliği zorunlu
4. **✅ Eşya tutarlılığı** — madalyon her sayfada aynı tanımla
5. **✅ Yan rol tutarlılığı** — yaşlı bilge "wise old man wearing..." sabit tanım
6. **✅ Indiana Jones kıyafeti kilidi** — "EXACTLY the same outfit on every page"
7. **✅ Sabit kurgu** — custom_inputs boş, kullanıcı kurguyu bozamıyor

---

## ✨ Öğrenilecek Pattern'ler

### Pattern 1: Custom page_prompt_template

```python
CATALHOYUK_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Mud-brick clustered houses: flat roofs, ladder access / "    # ← Lokasyon öğeleri listesi
    "Wall art: ancient paintings / Daily life: clay pots, hearths, smoke, rooftop pathways]. "
    "Cinematic action lighting, dynamic pose, detailed environment, depth of field. "
    "Wide angle, full body visible in action, child 30-40% of frame. "
    "No eye contact with camera. Earthy colors: mud brown, ochre, terracotta."
)
```

> **Ders:** `page_prompt_template` içine `Elements: [A / B / C]` formatında
> lokasyon öğeleri listesi eklemek, AI'ın hangisini seçeceğini serbest bırakır
> ama her zaman ortama uygun çizmesini sağlar.

### Pattern 2: story_prompt_tr'de Görsel Çeşitlilik Kuralı

```
GÖRSEL ÇEŞİTLİLİK (ÇOK ÖNEMLİ):
Her sahnenin görsel İngilizce betimlemesi (scene_description) hep aynı çatı manzarasını
ÇİZMEMELİDİR. Çizim açılarını Sürekli Değiştir!
- Bazen tılsıma veya ele ÇOK YAKIN (macro close-up)
- Bazen loş bir evin içi (interior hearth)
- Bazen eski toprak testiler (still life)
- Bazen çatıların uzak ve geniş manzarası (wide angle epic shot)
- Bazen de sadece çocuğun zorlu çabasına odaklan (medium shot)
Tekdüze manzarayı mutlaka boz.
```

> **Ders:** Kamera açısı çeşitliliğini story_prompt_tr'ye açıkça yaz.
> Gemini serbest bırakılırsa genelde aynı açıyı tekrarlar.

### Pattern 3: Eşya + Yan Rol Tutarlılık Kuralı

```
NESNE VE YARDIMCI KARAKTER TUTARLILIĞI:
- Antik madalyon (amulet) → her sayfada "an ancient clay medallion with spiral symbols"
  AYNI ifade — değişmez
- Yaşlı bilge adam → "wise old man wearing ancient baggy trousers and woven tunic"
  AYNI tanım — değişmez
```

> **Ders:** story_prompt_tr içinde "ANCHOR CÜMLE = [tanım] — HER SAYFADA AYNI" formatında
> sabit tanımlar ver. Gemini bunu uygular.

### Pattern 4: Outfit Kilitleme

```python
OUTFIT_BOY = (
    "khaki explorer shirt, brown leather vest, tan cargo shorts, sturdy brown boots, "
    "small satchel crossbody bag, classic fedora hat. "
    "EXACTLY the same outfit on every page — same khaki shirt, same fedora hat, same brown vest."
)
```

> **Ders:** Kıyafet tanımının sonuna "EXACTLY the same outfit on every page" cümlesi ekle.
> Bu `enhance_all_pages` tarafından her frame'e inject edilir.

### Pattern 5: Sabit Kurgu (Custom Inputs Boş)

```python
CATALHOYUK_CUSTOM_INPUTS: list[dict] = []  # Kurguyu bozmayacak şekilde boş
```

> **Ders:** Hikaye kurgusu sabit ve tutarlıysa (zaman yolculuğu gibi), kullanıcıdan
> özel girdi almak kurguyu dağıtabilir. Bu tip senaryolarda custom_inputs boş bırak.

---

## 📋 Çatalhöyük'ün Tam Senaryo Özeti

| Alan | Değer |
|------|-------|
| Tip | TİP C (Fantastik/Zaman Yolculuğu) |
| story_prompt_tr | ~800 kelime ✅ |
| cover_prompt_template | Custom ✅ |
| page_prompt_template | Custom + Elements listesi ✅ |
| Yardımcı karakterler | Yaşlı bilge adam, köylüler ✅ |
| Özel eşya | Antik madalyon (amulet) — anchor cümle var ✅ |
| Kıyafet | Indiana Jones teması — "EXACTLY same every page" ✅ |
| Görsel çeşitlilik kuralı | story_prompt_tr'de var ✅ |
| G3 kademe haritası | Yok ❌ (bu eksik — ama tip C için daha az kritik) |
| custom_inputs | Boş (sabit kurgu korunuyor) ✅ |
| Kalite puanı | ~75/80 |
