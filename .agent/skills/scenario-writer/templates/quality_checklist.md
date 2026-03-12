# Kalite Kontrol Listesi — Senaryo Denetim Rehberi

> Bu dosyayı her yeni senaryo tamamlandığında VE mevcut senaryoları denetlerken kullan.

---

## ✅ HIZLI KONTROL (Her Senaryo İçin)

```
□ story_prompt_tr mevcut ve 400 kelime üzeri
□ story_prompt_tr gezi rehberi formatında DEĞİL ("x'i gördü, sonra y'e gitti" yok)
□ Eğitsel değer → olay örgüsü: min. 4 değer için somut bağlantı var
□ "BU BİR GEZİ REHBERİ DEĞİL" uyarısı var
□ "YANLIŞ/DOĞRU" örnek cümleleri var
□ Yardımcı karakter: min. 4 seçenek, lokasyonla organik bağ
□ cover_prompt_template: varsayılan DEĞİL, senaryoya özgü
□ page_prompt_template: varsayılan DEĞİL, atmosfer öğeleri var
□ outfit_girl ve outfit_boy: İngilizce, "EXACTLY same outfit on every page" var
□ Min. 1 Görsel Kimlik Kartı (G2-a) doldurulmuş
□ Sahne Yönetmeni Bloğu (G3) story_prompt_tr'de var
□ location_en: İngilizce, kısa
□ theme_key: snake_case, benzersiz
```

---

## 📊 DETAYLI PUANLAMA

### Kriter 1: story_prompt_tr Uzunluğu (Max 10 puan)

```
400 kelime altı    → 0 puan (geçersiz)
400-499 kelime     → 5 puan
500-699 kelime     → 7 puan
700+ kelime        → 10 puan
```

### Kriter 2: story_prompt_tr Kalitesi (Max 10 puan)

```
Kontrol Et:
□ Gezi rehberi formatı YOK (+3)
□ "YANLIŞ/DOĞRU" örnek var (+2)
□ Eğitsel değer hikayeyi şekillendiriyor, öğüt vermiyor (+3)
□ "Bu bir gezi rehberi değil" uyarısı var (+1)
□ Sahne açıklama örnekleri somut ve lokasyona özgü (+1)
```

### Kriter 3: Kültürel Mekan (Max 10 puan)

```
10 mekan altı                   → 0 puan (geçersiz)
10 mekan, rol tanımı yok        → 5 puan
10+ mekan, hikayedeki rolleri var → 8 puan
10+ mekan + SAHNELERDEKİ rolü somut → 10 puan
```

### Kriter 4: Yardımcı Karakter (Max 5 puan)

```
4 seçenek altı                    → 0 puan (geçersiz)
4 seçenek, lokasyon bağı zayıf    → 2 puan
4 seçenek, orijinal & organik bağ → 5 puan
```

### Kriter 5: Görsel Akış Sistemi (Max 10 puan)

```
G3 yok, lokasyon injection kör     → 0 puan
G3 bloğu var ama kademe haritası yok → 5 puan
G3 bloğu + kademe haritası var     → 8 puan
+ Her kademede spesifik sahne örnekleri → 10 puan
```

### Kriter 6: page_prompt_template (Max 10 puan)

```
Varsayılan template kullanılmış    → 0 puan (kritik eksik)
Custom ama çok genel               → 4 puan
Custom + atmosfer öğeleri listesi  → 7 puan
Custom + öğe listesi + kamera çeşitliliği → 10 puan
```

### Kriter 7: Karakter Tutarlılık Kartları (Max 10 puan)

```
G2 kartı yok                      → 0 puan
Sadece G2-a (hayvan) var          → 5 puan
G2-a + G2-b (eşya) var           → 8 puan
G2-a + G2-b + G2-c (yan rol) var → 10 puan
```

### Kriter 8: Kıyafet Sistemi (Max 5 puan)

```
outfit_girl/boy boş               → 0 puan
Var ama çok kısa                  → 2 puan
Detaylı + "EXACTLY same outfit every page" → 4 puan
+ Hem kız hem erkek + temayla uyumlu → 5 puan
```

### Kriter 9: Eğitsel Değer Entegrasyonu (Max 5 puan)

```
Değer bağlantısı yok              → 0 puan
1-2 değer için bağlantı var       → 2 puan
3 değer için somut senaryo        → 3 puan
4+ değer + "yaşayarak öğrensin" kuralı → 5 puan
```

### Kriter 10: İçerik Güvenliği (Max 5 puan)

```
Dini ritüel veya siyasi atıf var  → -5 puan (ağır ihlal)
Korku/şiddet ağırlıklı sahne var  → -3 puan
Aile kısıtı ihlali (no_family durumunda) → -3 puan
İçerik tamamen güvenli + kısıtlamalar açıkça belirtilmiş → 5 puan
İçerik güvenli ama kısıtlama bloğu eksik → 3 puan
```

---

## 🔍 MEVCUT SENARYOLAR DURUM TAHMİNİ

| Senaryo | Tahmini Puan | Öncelikli Sorun |
|---------|-------------|-----------------|
| Kapadokya | ~70/80 | G2 kartları eksik |
| Galata Kulesi | ~55/80 | page_prompt varsayılan, G3 yok |
| Efes | ~65/80 | G2 kartları eksik |
| Yerebatan | ~65/80 | G2-b (Medusa taşı) eksik |
| Göbeklitepe | ~60/80 | G3 haritası eksik |
| Çatalhöyük | ~75/80 | En iyi mevcut senaryo |
| Amazon | ~50/80 | G2 + G3 eksik |
| Uzay | ~50/80 | G2 + G3 eksik |
| Okyanus | ~45/80 | Genel eksikler |
| Sultanahmet | ~60/80 | G2 + page_prompt |
| Sümela | ~60/80 | G2 + G3 |
| Abu Simbel | ~60/80 | G2 + G3 |
| Tac Mahal | ~60/80 | G2 + G3 |
| Kudüs | ~55/80 | G2 + G3 + page_prompt |
| Dinozor | ~55/80 | G2 + G3 |
| Umre | ~55/80 | G2 + page_prompt |

> **Not:** Bu tahminler kod analizi bazlı. Gerçek denetim için her senaryoyu
> tek tek bu checklist ile değerlendirmek gerekiyor.
