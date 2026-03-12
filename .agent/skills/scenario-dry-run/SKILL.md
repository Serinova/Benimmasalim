---
name: Scenario Dry-Run Tester
description: >
  Senaryo hikaye pipeline'ını GÖRSEL ÜRETMEden çalıştırıp, çıktıları (metin + görsel prompt)
  Scenario Writer kalite standartlarına göre denetleyen ve hikaye kalitesini puanlayan beceri.
  "senaryo test et", "hikaye dene", "dry run", "prompt karşılaştır", "G2 kontrol",
  "eğlence puanı", "hikaye kalitesi" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🧪 Scenario Dry-Run Tester Skill
## BenimMasalım — Senaryo Test, Denetim & Hikaye Kalitesi Analizi

> **Bu skill'i ne zaman kullanırsın?**
> - Kullanıcı "şu senaryoyu test et" dediğinde
> - "Prompt kalitesini kontrol et" dediğinde
> - "Hikaye eğlenceli mi?" dediğinde
> - "Senaryo analizi yap" dediğinde
> - Senaryo güncellemesi sonrası doğrulama testi yapmak istediğinde

---

## ⚡ TEK CÜMLE KURAL

> Bu skill, production pipeline'ını çalıştırarak hikaye + görsel prompt üretir,
> **5 teknik denetim** + **7 hikaye kalitesi analizi** + **genel eğlence puanı** hesaplar.

---

## 📋 ADIM ADIM SÜREÇ

### ADIM 1 — Senaryo theme_key Bul

```powershell
python -c "
import asyncio
from app.core.database import async_session_factory
from app.models import Scenario
from sqlalchemy import select

async def find():
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario.theme_key, Scenario.name, Scenario.scenario_bible)
            .where(Scenario.name.ilike('%ARAMA_TERİMİ%'))
        )
        for row in result.all():
            bible = 'VAR' if row[2] else 'YOK'
            print(f'{row[0]:30s} | {row[1]} | bible={bible}')

asyncio.run(find())
"
```

> **Cloud SQL Proxy çalışmıyorsa:**
> ```powershell
> cloud-sql-proxy gen-lang-client-0784096400:europe-west1:benimmasalim-db --port 5433
> ```

### ADIM 2 — Dry-Run Çalıştır

```powershell
python scripts/scenario_dry_run.py --theme_key <THEME_KEY> --child_name "Yusuf" --child_age 7 --child_gender erkek
```

Bu TEK KOMUT aşağıdakilerin hepsini yapar:
1. DB'den senaryoyu çeker
2. PASS-0 Blueprint + PASS-1 Story Writer çalıştırır (~60-90sn)
3. **5 Teknik Denetim** uygular
4. **7 Hikaye Kalitesi Analizi** yapar
5. **Genel Eğlence Puanı** hesaplar
6. JSON'a kaydeder: `tmp/dry_run/<theme>_dry_run.json`

### ADIM 3 — Sonuçları Rapor Et

Script çıktısındaki tüm sonuçları kullanıcıya artifact rapor olarak sun.

---

## 🔍 TEKNİK DENETİM KONTROLLERI (5 Adet)

| # | Kontrol | Açıklama |
|---|---------|----------|
| 1 | **G2-a Companion Tutarlılığı** | Yardımcı karakter her sayfada aynı türde mi? CAST BLOCK var mı? |
| 2 | **Kıyafet Kilidi** | Outfit anchor her sayfada birebir aynı mı? |
| 3 | **İçerik Güvenliği** | Yasaklı kelime, dini/siyasi referans, ten/saç rengi var mı? |
| 4 | **Sayfa Tamamlılığı** | Beklenen sayfa sayısı üretilmiş mi? Boş sayfa var mı? |
| 5 | **Metin-Görsel Uyumu** | Metindeki anahtar öğeler prompt'ta var mı? (eş anlamlı destekli) |

---

## 📚 HİKAYE KALİTESİ ANALİZLERİ (7 Adet)

### 🔁 Tekrar Analizi (%15)
- 4-6 kelimelik n-gram kalıplarını sayar
- Benzer açılış cümlelerini tespit eder
- 3+ tekrar eden kalıp varsa puan düşer

### 💬 Diyalog Analizi (%15)
- Tırnak/guillemet içi konuşmaları sayar
- İdeal: %30-50 sayfada diyalog olmalı
- Çok az (<15%) veya çok fazla (>70%) diyalog puan düşürür

### 🏃 Aksiyon/Pasiflik (%15)
- Aktif fiiller (koştu, atladı, bastı...) vs Pasif fiiller (izledi, baktı, hissetti...)
- İdeal aktif oran: %40-80
- Çok pasif kahraman (<30%) ciddi puan kaybı

### 📈 Duygusal Yay (%20 — en yüksek ağırlık)
- 8 duygu kategorisi: merak, heyecan, korku, üzüntü, sevinç, cesaret, şaşkınlık, gurur
- Duygusal çeşitlilik: en az 4 farklı duygu gerekli
- Korku→Cesaret geçişi: dramatik yayın en kritik noktası

### 📏 Sayfa Ritmi (%10)
- Kelime sayısı ortalaması, min, max, standart sapma
- Çok kısa (<25 kelime) veya çok uzun (>100 kelime) sayfalar flag'lenir
- İdeal: 40-70 kelime/sayfa, düşük StdDev

### 🔤 Kelime Çeşitliliği (%10)
- Type-Token Ratio (TTR): benzersiz kelime / toplam kelime
- İdeal TTR: 0.35-0.55 (çocuk kitabı)
- Renk ve boyut sıfat çeşitliliği

### 🪝 Sayfa Sonu Hook'ları (%15)
- Her sayfanın son cümlesi merak uyandırıyor mu?
- Hook göstergeleri: "birden", "tam o sırada", "ansızın", "ama", "?"
- İdeal: %50+ sayfada hook

---

## 🎯 EĞLENCE PUANI HESAPLAMA

| Puan | Emoji | Değerlendirme |
|------|-------|---------------|
| 9-10 | 🌟🌟🌟🌟🌟 | OLAĞANÜSTÜ |
| 8-8.9 | 🌟🌟🌟🌟 | ÇOK İYİ |
| 6.5-7.9 | 🌟🌟🌟 | İYİ |
| 5-6.4 | 🌟🌟 | ORTA |
| 1-4.9 | 🌟 | GELİŞTİRİLMELİ |

---

## 📊 RAPOR FORMATI

Denetim sonuçlarını artifact olarak şu formatta sun:

```markdown
# 🧪 [Senaryo Adı] — Dry-Run Test Raporu

## 📊 Teknik Denetim
| Kontrol | Sonuç |
|---------|-------|
| G2-a Companion | ✅ PASS |
| Kıyafet Kilidi | ✅ PASS |
| ... | ... |

## 📚 Hikaye Kalitesi
| Analiz | Puan |
|--------|------|
| 🔁 Tekrar | X/10 |
| 💬 Diyalog | X/10 |
| ... | ... |

## 🎯 EĞLENCE PUANI: X.X/10 🌟🌟🌟

## 📈 Duygusal Yay
S.1:merak → S.3:heyecan → S.11:korku → S.12:cesaret → S.18:gurur

## 🛠️ İyileştirme Önerileri
1. ...
```

---

## 🔄 TAM AKIŞ ÖZETİ

```
1. Kullanıcı senaryo seçer
2. theme_key bulunur
3. Dry-run script çalışır (PASS-0 + PASS-1, ~60-90sn)
4. 5 Teknik Denetim → companion, kıyafet, güvenlik, tamamlılık, uyum
5. 7 Hikaye Kalitesi → tekrar, diyalog, aksiyon, duygu, ritim, kelime, hook
6. Eğlence Puanı hesaplanır (ağırlıklı ortalama)
7. JSON kaydedilir + Artifact rapor sunulur
8. Sorunlar varsa → Scenario Writer skill ile düzeltme önerisi
```

---

## 📁 İlgili Dosyalar

| Dosya | Ne İşe Yarar |
|-------|-------------|
| `backend/scripts/scenario_dry_run.py` | Ana test script (tüm analizler dahil) |
| `backend/app/services/ai/_story_writer.py` | V3 pipeline (generate_story_v3) |
| `backend/app/prompt/page_builder.py` | CAST LOCK & companion enjeksiyonu |
| `backend/app/services/ai/cast_validator.py` | CAST block builder |
| `backend/app/prompt_engine/visual_prompt_builder.py` | Prompt composer |
| `.agent/skills/scenario-writer/` | Senaryo oluşturma/güncelleme skill'i |

---

## ⚠️ ÖNEMLİ NOTLAR

1. **Cloud SQL Proxy ZORUNLU**: Script DB'ye bağlanıyor → port 5433
2. **Gemini API KULLANIR**: PASS-0 + PASS-1 = ~2 API call
3. **GÖRSEL ÜRETİLMEZ**: Sadece metin + prompt çıktısı
4. **~60-90 saniye sürer**: Blueprint + Story generation
5. **scenario_bible ÖNEMLİ**: Companion tutarlılığı için bible gerekli
6. **Tekrarlanabilir**: Aynı parametrelerle farklı sonuçlar çıkabilir (AI)
