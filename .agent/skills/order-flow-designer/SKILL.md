---
name: Order Flow Designer – Sipariş Akışı Premium Tasarım Yöneticisi
description: >
  Sipariş oluşturma akışının (create-v2) her adımını premium, mobil-öncelikli,
  güven veren ve butik hizmet hissiyatıyla baştan tasarlamak için ZORUNLU beceri.
  "sipariş tasarla", "adım X'i tasarla", "create-v2 redesign", "order flow"
  dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🎨 Order Flow Designer — Sipariş Akışı Premium Tasarım Yöneticisi

## Amaç

Bu skill, Benim Masalım'ın **sipariş oluşturma sürecini** (create-v2) sayfa sayfa
yeniden tasarlamak için kapsamlı bir rehberdir. Kullanıcı `"1. adımı tasarla"` dediğinde
o adımın tasarımı sıfırdan mükemmel yapılır; `"2. adımı tasarla"` dediğinde diğerine
geçilir. Her adım bağımsız çalışır ama tutarlı bir tasarım sistemi paylaşır.

---

## 🏗️ Mimari Genel Bakış

### Dosya Yapısı
```
frontend/src/app/create-v2/
├── page.tsx                          # Ana orchestrator (743 satır)
├── layout.tsx                        # SEO metadata
├── _hooks/
│   ├── useOrderDraft.ts              # Durum yönetimi (sessionStorage)
│   └── usePromoValidation.ts         # Promo kodu doğrulama
├── _lib/
│   ├── constants.ts                  # Adım tanımları, yaş aralıkları
│   ├── pricing.ts                    # Fiyat hesaplama
│   └── validations.ts               # Form validasyonları
└── _components/
    ├── WizardShell.tsx               # Kabuk: stepper + blob arka plan + layout
    ├── StepProgress.tsx              # 5-adım stepper (masaüstü + mobil)
    ├── StickyCTA.tsx                 # Yapışkan alt navigasyon çubuğu
    ├── OrderSummaryCard.tsx          # Sipariş özeti sidebar (adım ≥4)
    ├── SuccessScreen.tsx             # Sipariş tamamlandı ekranı
    ├── ui/
    │   ├── FormField.tsx             # Input bileşeni
    │   ├── FormTextarea.tsx          # Textarea bileşeni
    │   ├── GenerationProgress.tsx    # İlerleme göstergesi
    │   ├── GenerationWaitingModal.tsx # Bekleme modal
    │   ├── PromoCodeInput.tsx        # Promo kodu inputu
    │   └── TrustBadges.tsx           # Güven rozetleri
    └── steps/
        ├── HeroAndAdventureStep.tsx  # ADIM 1: Kahraman & Macera
        ├── VisualsAndPhotoStep.tsx   # ADIM 2: Fotoğraf & Stil
        ├── PreviewStep.tsx           # ADIM 3: Kitap Önizleme
        ├── ExtrasAndShippingStep.tsx # ADIM 4: Ekstralar & Teslimat
        └── PaymentStep.tsx          # ADIM 5: Ödeme
```

### Mevcut Eski Bileşenler (src/components/)
Bu bileşenler create-v2'ye entegre edilmemiş ama zengin UI barındırır:
```
src/components/
├── AudioSelectionStep.tsx    # 815 satır — Ses seçimi, waveform, klonlama
├── PhotoUploaderStep.tsx     # 28KB — Fotoğraf yükleme, analiz kartı
├── StoryReviewStep.tsx       # 12KB — Hikaye inceleme slaytları
├── CheckoutStep.tsx          # 61KB — Ödeme (yeni PaymentStep ile değiştirildi)
├── VoiceRecorderStep.tsx     # 27KB — Ses kayıt ekranı
├── ImagePreviewStep.tsx      # 34KB — Kitap önizleme
└── VisualsStep.tsx           # 25KB — Fotoğraf + stil seçimi
```

---

## 🎭 Sipariş Akışı Adımları

Kullanıcı **"X. adımı tasarla"** dediğinde aşağıdaki tabloya göre ilgili adım sıfırdan yeniden yazılır:

| Komut | Adım | Sayfa | Dosya | İçerik |
|-------|------|-------|-------|--------|
| `1. adımı tasarla` | 1 | Kahraman & Macera | `HeroAndAdventureStep.tsx` | İsim, cinsiyet, yaş, senaryo seçimi |
| `2. adımı tasarla` | 2 | Fotoğraf & Stil | `VisualsAndPhotoStep.tsx` | Fotoğraf yükleme, analiz, stil seçimi |
| `3. adımı tasarla` | 3 | Kitap Önizleme | `PreviewStep.tsx` | Bekleme, ilerleme, sayfa sayfa önizleme |
| `4. adımı tasarla` | 4 | Ekstralar & Teslimat | `ExtrasAndShippingStep.tsx` | Sesli kitap, boyama, ithaf, adres |
| `5. adımı tasarla` | 5 | Ödeme | `PaymentStep.tsx` | Fatura, promo, sipariş özeti, ödeme |
| `başarı ekranını tasarla` | 6 | Tebrikler | `SuccessScreen.tsx` | Sipariş onay, takip bilgileri |
| `shell'i tasarla` | — | Kabuk | `WizardShell.tsx` + `StepProgress.tsx` | Stepper, arka plan, layout |

---

## 🎨 Tasarım Sistemi — PREMIUM BOUTIQUE STANDARD

Her adım tasarlanırken aşağıdaki tasarım prensipleri **ZORUNLU** uygulanır:

### 1. Marka Hissiyatı
```
"Sıradan bir kitapçıdan sipariş vermiyorsunuz.
 Çocuğunuz için benzersiz, elle işlenmiş premium bir hediye yaratıyorsunuz.
 Her dokunuş özel, her detay düşünülmüş."
```

### 2. Renk Paleti
```css
/* Ana Renkler */
--brand-primary:    #7C3AED;   /* Violet 600 — marka ana rengi */
--brand-gradient:   linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
--brand-surface:    #FAF5FF;   /* Violet 50 — sayfa arka planı */

/* Durum Renkleri */
--success:          #059669;   /* Emerald 600 */
--warning:          #D97706;   /* Amber 600 */
--error:            #DC2626;   /* Red 600 */

/* Nötr — Apple-vari cool gray */
--text-primary:     #1E293B;   /* Slate 800 */
--text-secondary:   #64748B;   /* Slate 500 */
--text-muted:       #94A3B8;   /* Slate 400 */
--surface-card:     #FFFFFF;
--surface-border:   #F1F5F9;   /* Slate 100 */

/* Premium Aksan */
--gold:             #F59E0B;   /* Amber 500 — premium özellikler için */
```

### 3. Tipografi Hiyerarşisi
```css
/* Başlıklar — Bold, impactful */
h1: text-xl sm:text-2xl font-extrabold tracking-tight text-slate-900
h2: text-lg sm:text-xl font-bold text-slate-800
h3: text-base font-semibold text-slate-700

/* Gövde — Okunabilir, ferah */
body: text-sm sm:text-base text-slate-600 leading-relaxed
caption: text-xs text-slate-500
badge: text-[10px] sm:text-xs font-bold uppercase tracking-wider
```

### 4. Boşluk & Layout Kuralları
```
• Mobil yaklaşım: max-w-lg mx-auto (dar, odaklanmış layout)
• Kartlar arası boşluk: space-y-4 sm:space-y-5
• Kart iç padding: p-4 sm:p-5
• Border radius: rounded-2xl (kartlar), rounded-xl (inputlar), rounded-full (badge'ler)
• Gölgeler: shadow-sm (normal), shadow-lg shadow-purple-100 (vurgulu)
• Kartlar: bg-white border border-slate-100 rounded-2xl shadow-sm
```

### 5. Mobil Öncelikli Kurallar (KRİTİK)
```
✅ YAPILACAKLAR:
• Dokunma hedefleri minimum 44×44px (W3C WCAG standart)
• Tek elle kullanılabilir UI — önemli butonlar ekranın alt yarısında
• StickyCTA her zaman ekranın altında sabitlenmeli
• safe-area-inset-bottom desteği (iPhone çentikli ekranlar)
• Yatay scroll yok — her şey dikey akışta
• Fotoğraf yükleme: hem kamera hem galeri destekli
• Input'lar focus'ta yumuşak scroll (scrollIntoView)
• Yazı boyutu minimum 14px (mobil okunabilirlik)

❌ YAPILMAYACAKLAR:
• Hover-bağımlı UI (mobilde hover yok)
• Çok küçük dokunma alanları
• Karmaşık nested açılır menüler
• Modalsız kayan paneller (sheet tercih et)
```

### 6. Güven İnşa Eden Elementler (Her Sayfada ZORUNLU)
```
Her adımda en az 2 güven sinyali gösterilmeli:

🔒 "256-bit SSL Şifreli"
🛡️ "KVKK Uyumlu"
🚚 "Ücretsiz Kargo"
💚 "Mutluluk Garantisi"
⭐ "4.9/5 Müşteri Puanı"
🏆 "1000+ Mutlu Aile"
📞 "Canlı Destek"
🔄 "14 Gün İade Hakkı"

Güven rozetleri: StickyCTA'nın hemen üstünde veya kartların altında.
Görsel: İkonlu, küçük (text-xs), soluk ama okunabilir (text-slate-400).
```

### 7. Mikro-Animasyonlar (framer-motion)
```tsx
// Sayfa geçişi (WizardShell zaten uyguluyor)
initial={{ opacity: 0, x: 20 }}
animate={{ opacity: 1, x: 0 }}
exit={{ opacity: 0, x: -20 }}
transition={{ duration: 0.18 }}

// Kart/Section giriş animasyonu
initial={{ opacity: 0, y: 12 }}
animate={{ opacity: 1, y: 0 }}
transition={{ delay: index * 0.05 }}

// Buton dokunma geri bildirimi
whileTap={{ scale: 0.97 }}

// Seçim state geçişi
layoutId="selected-indicator" // smooth morph animasyonu

// Başarı → pulse
animate={{ scale: [1, 1.05, 1] }}
transition={{ duration: 0.3 }}
```

### 8. Kurumsal İzlenim — "Boutique E-Commerce" Tarzı
```
Her sayfada şu hissiyat olmalı:

• Sipariş numarası veya adım bilgisi — "Adım 2/5" tarzı progress bilgisi
• Marka logosu veya watermark hissiyatı
• Yardım erişimi — her sayfada küçük "?" veya "Yardım" butonu
• Profesyonel dil — "Lütfen", "Teşekkür ederiz", "Güvenle"
• Boş alan kullanımı — Apple web sayfası gibi ferah
• Beklemede bilgilendirme — "Bu işlem genellikle 30 saniye sürer"
• İlerleme duygusu — "Neredeyse bitti!", "Son adım!"
```

---

## 📐 Adım Tasarım Şablonu

Her adım tasarlanırken bu yapı takip edilir:

```tsx
"use client";

// 1. Import'lar — React, framer-motion, lucide-react, yerel bileşenler
// 2. Interface — Props tanımı
// 3. Ana bileşen

export default function StepXName(props: StepXProps) {
  return (
    <div className="pb-24 space-y-5">
      {/* ── Adım Başlığı ── */}
      <header>
        <p className="text-[10px] sm:text-xs font-bold text-violet-500 uppercase tracking-wider mb-0.5">
          Adım X
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-slate-800">
          Başlık Metni
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Açıklama metni
        </p>
      </header>

      {/* ── İçerik Kartları ── */}
      <section className="space-y-4">
        {/* Her bölüm kendi kartında */}
        <div className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden">
          {/* Kart başlığı */}
          <div className="px-4 pt-3.5 pb-2.5 border-b border-slate-50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-violet-500" />
              <span className="text-sm font-semibold text-slate-700">Bölüm Adı</span>
            </div>
            {/* Opsiyonel: badge, durum göstergesi */}
          </div>
          {/* Kart içeriği */}
          <div className="p-4">
            {/* ... */}
          </div>
        </div>
      </section>

      {/* ── Güven Rozetleri ── */}
      <TrustBadges />

      {/* ── Yapışkan CTA (StickyCTA) ── */}
      <StickyCTA
        primaryLabel="Sonraki Adım"
        onPrimary={onContinue}
        primaryDisabled={!canContinue}
        secondaryLabel="← Geri"
        onSecondary={onBack}
      />
    </div>
  );
}
```

---

## 🔄 Her Adımın Tasarım Gereksinimleri

### ADIM 1: Kahraman & Macera Seçimi
**Mevcut durum:** ✅ İyi tasarlanmış (459 satır)
**Geliştirmeler:**
- Avatar: isim girdikçe canlanan emoji → daha sofistike bir karakter ilustrasyonu
- Senaryo kartları: hover'da hafif 3D tilt efekti
- Yaş seçimi: seçilen yaş butonunda pulse animasyonu
- Cinsiyet seçimi: seçilen cinsiyete göre renk geçişi (erkek → mavi tonu, kız → pembe tonu)
- Seçili macera banner'ında kapak görseli shimmer efekti

### ADIM 2: Fotoğraf & Stil Seçimi
**Mevcut durum:** ⚠️ Eski `VisualsStep` wrapper — BAŞTAN YAZILMALI
**Tam kapsamlı yeniden tasarım:**

| Bölüm | Yeni Tasarım |
|-------|-------------|
| **Fotoğraf Yükleme** | Polaroid tarzında yükleme kartı, çerçeve efekti ile |
| **Fotoğraf Analiz** | AI-powered analiz kartı: yüz tespiti → yeşil çerçeve overlay |
| **KVKK Onay** | Checkbox + güvenlik badge'leri (SSL, KVKK, 30 gün silme) |
| **Ek Fotoğraflar** | 4'e kadar mini fotoğraf grid'i (opsiyonel bölüm) |
| **Stil Seçimi** | 2 sütunlu grid (mobil), büyük önizleme kartları |
| **Gelişmiş Ayarlar** | Collapsible — yüz benzerliği slider'ı |

### ADIM 3: Kitap Önizleme
**Mevcut durum:** ⚠️ Eski `ImagePreviewStep` wrapper — BAŞTAN YAZILMALI
**Tam kapsamlı yeniden tasarım:**

| Bölüm | Yeni Tasarım |
|-------|-------------|
| **Bekleme Ekranı** | Slayt tarzı: "Hikayeniz yazılıyor..." → "Karakterler çiziliyor..." → "Son rötuşlar..." |
| **İlerleme Çubuğu** | Yüzdelik ilerleme + tahmin süresi |
| **Sayfa Önizleme** | Carousel/Page-flip efekti ile kitap sayfaları |
| **Kapak Sayfası** | Özel vurgulanmış 3D kitap kapağı |
| **Onay Aksiyonları** | "Beğendim, Devam Et" + "Tekrar Oluştur" butonları |

### ADIM 4: Ekstralar & Teslimat
**Mevcut durum:** ✅ Yeni ama sadeleştirilmiş audio
**Geliştirmeler:**

| Bölüm | Yeni Tasarım |
|-------|-------------|
| **Sesli Kitap** | Full-width seçim kartları: 3 opsiyon (Yok/Profesyonel/Sizin Sesiniz) |
| **Ses Önizleme** | Waveform animasyonlu oynatıcı, 2 ses seçeneği (kadın/erkek) |
| **Boyama Kitabı** | Önizleme görselli toggle kart |
| **İthaf Notu** | Faded preview "Bu kitap ... için" |
| **Adres Formu** | Kayıtlı adres seçici + yeni adres formu |

### ADIM 5: Ödeme
**Mevcut durum:** ✅ Yeni (240 satır)
**Geliştirmeler:**

| Bölüm | Yeni Tasarım |
|-------|-------------|
| **Sipariş Özeti** | Kitap kapağı mini preview + fiyat kırılımı |
| **Fatura Tipi** | Bireysel/Kurumsal toggle (TCKN veya Vergi Dairesi) |
| **Promo Kodu** | Inline doğrulama, başarı/hata animasyonu |
| **Ödeme Butonu** | Büyük, premium, CTA — "₺XXX Güvenle Öde" |
| **Güven Alanı** | Iyzico/Visa/Mastercard logoları + SSL badge |

### ADIM 6: Başarı Ekranı
**Mevcut durum:** Basit (2.8KB)
**Geliştirmeler:**

| Bölüm | Yeni Tasarım |
|-------|-------------|
| **Kutlama** | Confetti animasyonu + büyük yeşil tik |
| **Sipariş Özeti** | Sipariş no, tahmini teslimat, kapak preview |
| **Sonraki Adımlar** | "Siparişimi Takip Et", "Yeni Kitap Oluştur" |
| **Sosyal Paylaşım** | "Bu deneyimi arkadaşlarınla paylaş" |

---

## 🛠️ Tasarım Uygulama Prosedürü

Kullanıcı **"X. adımı tasarla"** dediğinde şu adımlar sırasıyla izlenir:

### Faz 1: Analiz (İlk 2 dakika)
1. Hedef adımın mevcut dosyasını oku (mevcut state'i anla)
2. Eski `src/components/` altındaki ilgili bileşenleri oku (kayıp zenginlikleri bul)
3. Hedef adımın `page.tsx` içindeki props geçişini incele
4. `useOrderDraft` hook'undaki ilgili state alanlarını kontrol et
5. Adımın API etkileşimlerini belirle
6. Mevcut shared bileşenleri (`StickyCTA`, `FormField`, `TrustBadges`) incele

### Faz 2: Tasarım Kararları
7. Adımın alt bölümlerini listele (kart yapısı)
8. Her bölüm için yukarıdaki tasarım sisteminden uygun pattern'i seç
9. Mobil vs masaüstü layout kararları
10. Animasyon planı (giriş, etkileşim, durum değişimi)
11. Güven elementleri yerleşimi

### Faz 3: Uygulama
12. Yeni adım bileşenini baştan yaz (şablon yapısını takip et)
13. Gerekirse yeni shared UI bileşeni oluştur (`_components/ui/`)
14. Props interface'ini güncelle (page.tsx ile uyumlu)
15. Import'ları düzenle
16. `page.tsx`'teki entegrasyonu kontrol et

### Faz 4: Doğrulama
17. TypeScript hatalarını kontrol et (`npx tsc --noEmit`)
18. Görsel doğrulama: Tarayıcıda aç ve ekran görüntüsü al
19. Mobil görünüm doğrulaması (viewport: 375px)
20. Animasyonları test et

---

## 📱 Ekran Boyutları Referansı

```
iPhone SE:     375 × 667    ← Temel mobil hedef
iPhone 14:     390 × 844
iPhone 14 Pro: 393 × 852
Samsung S23:   360 × 800
iPad Mini:     768 × 1024
Desktop:       1280 × 800   ← Masaüstü breakpoint
```

**Breakpoint stratejisi:** Tailwind varsayılanları
- Mobil: `< 640px` (default — mobil-öncelikli tasarım)
- Tablet: `sm:` (640px+)
- Desktop: `lg:` (1024px+)

---

## ⚠️ Zorunlu Kurallar

1. **Eski bileşenleri import etme** — `src/components/XStep` gibi eski bileşenleri ASLA import etme. Her şeyi `create-v2/_components/` altında yaz.
2. **Props uyumu** — `page.tsx`'teki mevcut props geçişini bozma. Yeni prop eklemek istersen `page.tsx`'i de güncelle.
3. **StickyCTA kullan** — Her adımda `StickyCTA` bileşenini kullan (tutarlılık).
4. **Safe area** — iPhone notch/home bar desteği her sayfada olmalı.
5. **Skeleton loading** — Veri yüklenirken skeleton UI göster.
6. **Error state** — Her adımda hata durumunu handle et.
7. **Empty state** — Veri yoksa (örn: senaryo yüklenmedi) kullanıcıyı bilgilendir.
8. **a11y** — `aria-label`, `role`, `aria-current` kullan. Renk kontrast oranı ≥ 4.5:1.
9. **Performans** — Görseller `next/image` ile, lazy load, proper `sizes` attribute.
10. **Build check** — Her değişiklikten sonra build hatasız geçmeli.

---

## 🔗 İlgili Dosyalar (Hızlı Referans)

| Dosya | Yol | Açıklama |
|-------|-----|----------|
| Ana sayfa | `frontend/src/app/create-v2/page.tsx` | Orchestrator |
| Draft hook | `frontend/src/app/create-v2/_hooks/useOrderDraft.ts` | State yönetimi |
| Validasyonlar | `frontend/src/app/create-v2/_lib/validations.ts` | Form doğrulama |
| Fiyatlama | `frontend/src/app/create-v2/_lib/pricing.ts` | Fiyat hesaplama |
| Sabitler | `frontend/src/app/create-v2/_lib/constants.ts` | Adım tanımları |
| API katmanı | `frontend/src/lib/api.ts` | Backend API fonksiyonları |
| Eski bileşenler | `frontend/src/components/*.tsx` | Referans zenginlik kaynağı |
