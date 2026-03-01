---
description: Geliştirme sürecinde beyin fırtınası (brainstorm) oturumu başlatma yönergesi. Yeni özellik, UX iyileştirmesi, mimari karar veya problem çözümü için yapılandırılmış bir fikir üretme süreci.
---
Bu workflow, "Benim Masalım" projesi üzerinde yapılandırılmış bir beyin fırtınası (brainstorm) oturumu yürütmek için kullanılır.

**Nasıl Kullanılır:**
Kullanıcı chat üzerine `/brainstorm` veya `/beyinfirtinasi` yazdığında bu adımlar izlenir.

---

1. **Oturum Başlangıcı — Konu ve Kapsam Belirleme:**
   Kullanıcıya şu soruları sor:
   - a) **Konu:** Ne hakkında beyin fırtınası yapmak istiyorsun? (örn. yeni özellik, UX iyileştirmesi, performans, mimari karar, bug çözümü, iş modeli, pazarlama)
   - b) **Kapsam:** Frontend, Backend, Tasarım, Full-Stack veya İş/Strateji?
   - c) **Hedef:** Bu oturumun sonunda ne elde etmek istiyorsun? (örn. karar vermek, fikir listesi çıkarmak, aksiyon planı oluşturmak)

---

2. **Bağlam Toplama:**
   - Konuyla ilgili mevcut kodu, dosyaları ve mimariyi incele.
   - `.cursor/rules/` altındaki ilgili kuralları oku (frontend, backend, vb.).
   - Eğer konu mevcut bir özellikle ilgiliyse, o özelliğin kodunu ve yapısını anla.
   - Rakip analizi veya sektör trendleri gerekiyorsa `search_web` ile araştırma yap.

---

3. **Fikir Üretimi — Yapılandırılmış Beyin Fırtınası:**
   Aşağıdaki çerçeveyi kullanarak en az **5-10 fikir** üret ve bunları bir artifact dosyasına yaz:

   **Artifact dosyası:** `brainstorm_<konu>.md` (artifact dizinine yazılır)

   Her fikir için şu format kullanılır:

   ```markdown
   ### 💡 Fikir #N: [Başlık]
   - **Açıklama:** Fikrin kısa özeti
   - **Neden:** Bu fikir neden değerli?
   - **Zorluk:** 🟢 Kolay | 🟡 Orta | 🔴 Zor
   - **Etki:** ⭐ Düşük | ⭐⭐ Orta | ⭐⭐⭐ Yüksek
   - **Teknik Notlar:** Nasıl implemente edilebilir? (kısa)
   ```

   Fikirler şu kategorilere ayrılır:
   - 🚀 **Hızlı Kazanımlar** (düşük efor, yüksek etki)
   - 🏗️ **Büyük Hamleler** (yüksek efor, yüksek etki)
   - 🧪 **Deneysel** (belirsiz etki, keşfetmeye değer)
   - 🔧 **Teknik İyileştirmeler** (altyapı ve performans)

---

4. **Değerlendirme ve Önceliklendirme:**
   Kullanıcıyla birlikte fikirleri değerlendir:
   - Her fikre **Etki vs. Efor** matrisi üzerinde konum ver.
   - Kullanıcıdan favorilerini seçmesini iste.
   - En yüksek öncelikli 2-3 fikri belirle.

   Artifact dosyasına bir **Öncelik Tablosu** ekle:

   ```markdown
   ## 📊 Öncelik Matrisi

   | Sıra | Fikir | Etki | Efor | Öncelik |
   |------|-------|------|------|---------|
   | 1    | ...   | ⭐⭐⭐ | 🟢   | 🔥 Yüksek |
   | 2    | ...   | ⭐⭐⭐ | 🟡   | 🔥 Yüksek |
   | 3    | ...   | ⭐⭐  | 🟢   | ➡️ Orta   |
   ```

---

5. **Aksiyon Planı Oluşturma:**
   Seçilen fikirleri somut aksiyon adımlarına dönüştür:
   - Her fikir için kısa bir implementasyon planı oluştur.
   - Gerekli dosyalar, değişiklikler ve bağımlılıkları listele.
   - Tahmini süre ver (saat/gün bazında).
   - Artifact dosyasına **Aksiyon Planı** bölümü ekle.

   ```markdown
   ## 🎯 Aksiyon Planı

   ### Adım 1: [Fikir Adı]
   - **Yapılacaklar:**
     - [ ] ...
     - [ ] ...
   - **Dosyalar:** `dosya1.tsx`, `dosya2.py`
   - **Tahmini Süre:** ~X saat
   ```

---

6. **Oturum Kapanışı:**
   - Tüm beyin fırtınası çıktılarını içeren artifact dosyasını kullanıcıya sun.
   - Kullanıcıya sor: "Bu fikirlerden herhangi birini hemen uygulamaya başlamak ister misin?"
   - Eğer evet derse, seçilen fikir için `implementation_plan.md` oluşturup PLANNING moduna geç.
