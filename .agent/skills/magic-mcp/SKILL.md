---
name: Magic MCP – Frontend UI Üretici
description: >
  21st.dev Magic MCP sunucusunu kullanarak Benim Masalım projesinin frontend (Next.js/TSX) arayüzlerini
  doğal dil ile hızlı şekilde oluşturmak, geliştirmek ve mevcut bileşenleri iyileştirmek için
  MUTLAKA referans alınacak beceri rehberi. `/ui` komutu verildiğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🪄 Magic MCP — Frontend UI Üretici Becerisi

## Ne İşe Yarar?

**21st.dev Magic MCP**, AI ajanının (Antigravity) doğal dil açıklamalarından **hazır, modern
React/TSX bileşenleri** üretmesini sağlar. Cursor'daki v0'a benzer; ama doğrudan bu IDE içinde çalışır.

Benim Masalım frontendi **Next.js 14 + TypeScript + Tailwind CSS** kullanmaktadır.
Magic MCP üretilen bileşenler bu stack ile %100 uyumludur.

---

## ⚙️ Kurulum & Aktivasyon

### 1. API Key Edinme
👉 **[21st.dev/magic/console](https://21st.dev/magic/console)** adresine git.
- Hesap oluştur veya giriş yap
- "Generate API Key" butonuna tıkla
- Key'i kopyala

### 2. API Key'i Antigravity'ye Ekle
`C:\Users\yusuf\AppData\Roaming\Antigravity\User\settings.json` dosyasındaki şu satırı bul:

```json
"API_KEY": "YOUR_21ST_DEV_API_KEY_HERE"
```

`YOUR_21ST_DEV_API_KEY_HERE` kısmını kendi API key'inle değiştir:

```json
"API_KEY": "sk-21st-xxxxxxxxxxxxxxxxxxxx"
```

### 3. MCP Sunucusunu Yeniden Başlat
Antigravity'yi **kapat ve tekrar aç** ya da:
- `Ctrl+Shift+P` → **"MCP: Restart Server"** → `@21st-dev/magic` seç

---

## 🚀 Kullanım Kılavuzu

### Temel Komut: `/ui`

Antigravity chat paneline `/ui` yazıp ardından ne istediğini Türkçe veya İngilizce açıkla:

```
/ui Benim Masalım projesine yakışan bir hikaye kartı bileşeni oluştur.
    Kart üzerinde kapak görseli, hikaye başlığı, çocuk adı ve sipariş
    durumu badge'i olsun. Glassmorphism efekti ve hover animasyonu ekle.
```

```
/ui Admin paneli için bir sipariş özet tablosu. Sütunlar: Sipariş No,
    Müşteri Adı, Tarih, Durum (badge), İşlemler. Dark mode uyumlu.
```

### Logo / İkon Getirme: `/logo`

Marka logolarını SVG olarak projeye ekler:

```
/logo Next.js logosu al
/logo Stripe ödeme logosu
/logo Google Play Store ikonu
```

---

## 📋 Benim Masalım'a Özel Kullanım Senaryoları

### Senaryo 1: Yeni Admin Panel Bileşeni
```
/ui Benim Masalım admin paneli için sipariş detay modal bileşeni:
- Üstte: Sipariş numarası ve durum badge
- Ortada: 3 sütunlu grid: Müşteri bilgisi | Hikaye bilgisi | Ödeme bilgisi
- Altta: İşlem butonları (Onayla, İptal Et, PDF İndir)
- Renk paleti: indigo/purple (#6366f1) ana renk, dark tema
```

### Senaryo 2: Müşteri Yolculuğu Adım Göstergesi
```
/ui Sipariş oluşturma sihirbazı için adım göstergesi (stepper):
4 adım: Karakter → Senaryo → Ekstralar → Ödeme
Aktif adım parlak, tamamlananlar yeşil tikli, bekleyenler soluk.
Mobil uyumlu yatay layout.
```

### Senaryo 3: Hikaye Önizleme Kartı
```
/ui Benim Masalım için hikaye önizleme bileşeni:
- Kitap kapağı görseli (1:1.4 oran, book spine efekti)
- Öne çıkan bilgiler: Çocuk adı, Yaş, Senaryo tipi
- Hover'da 3D flip animasyonu ile arka sayfa görünsün
- Arka sayfada: Sipariş durumu ve aksiyon butonları
```

### Senaryo 4: Dashboard Metrik Kartları
```
/ui Dashboard için 4'lü metrik kartı grid:
- Kart 1: Toplam Sipariş (trend ok + yüzde)
- Kart 2: Tamamlanan Hikaye (başarı rengi)
- Kart 3: Bekleyen Görev (uyarı rengi)
- Kart 4: Bugünkü Gelir (para birimi formatı)
Glassmorphism + subtle gradient border efekti.
```

---

## 🎨 Benim Masalım Tasarım Sistemi Referansı (APPLE-STANDARD BOUTIQUE)

Magic MCP'ye bileşen üretirken DAİMA şu **Premium & Güven Veren** tasarım ruhunu prompt'a ekle:

```
Tasarım ruhu ve sistemi:
- Tarz: Apple standartlarında, premium, ultra-kaliteli butik e-ticaret hizmeti.
- Hissiyat: "Sıradan bir kitap değil, özel tasarlanmış çok değerli bir hediye veriyoruz."
- Estetik: Minimalist, temiz, gereksiz çizgilerden arındırılmış (borderless design).
- Gölgeler: Çok yumuşak, geniş ve havadar gölgeler (Apple vari shadow-sm veya shadow-lg).
- Tipografi: Keskin, yüksek okunabilirlikli ve asil (örn: Inter veya SF Pro tarzı). Yazılar okuması keyifli ve ferah olmalı.
- Elementler: Keskin köşeler yerine çok hafif yuvarlatılmış şık hatlar (radius: 12px-16px).
- Renk Paleti: Çok bağıran pastel renkler YERİNE, yüksek kaliteli indigo (#6366f1) detaylar, bolca negatif boşluk (white space) ve nötr griler.
- Etkileşim: Hızlı, pürüzsüz ve "expensive" (pahalı) hissettiren micro-animasyonlar (framer-motion).
- Tailwind CSS v3 ve shadcn/ui altyapısı kullan.
```

---

## ⚠️ Kurallar & Dikkat Edilecekler

1. **Otomatik entegrasyon**: Magic MCP bileşeni oluşturduğunda, dosyayı projenin
   uygun klasörüne (`frontend/src/components/`) otomatik ekler. Yolun doğruluğunu kontrol et.

2. **TypeScript zorunluluğu**: Üretilen bileşenler `.tsx` uzantılı olmalı.
   Magic MCP bunu otomatik yapar; ama `any` type kullanımını sonradan temizle.

3. **Import kontrolü**: `lucide-react`, `framer-motion`, `@radix-ui` gibi kütüphane
   importlarını kontrol et. Proje `package.json`'ında yoksa ekle.

4. **Mevcut bileşenlerle çakışma**: Aynı isimde bileşen varsa Magic MCP üzerine yazar.
   Önemli dosyalarda önce `git commit` yap.

5. **Ücretli kullanım**: Magic MCP aylık belirli sayıda ücretsiz üretim hakkı sunar.
   Karmaşık bileşenler için tek bir kapsamlı prompt yaz, birden fazla küçük istek yapma.

---

## 🔗 Faydalı Kaynaklar

- **Magic Console** (kullanım/kota): https://21st.dev/magic/console
- **Bileşen Kütüphanesi**: https://21st.dev
- **GitHub Repo**: https://github.com/21st-dev/magic-mcp
- **Antigravity MCP Docs**: https://antigravity.google/docs/mcp

---

## 🛠️ Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| `/ui` komutu tanınmıyor | Antigravity'yi yeniden başlat, MCP sunucusunu kontrol et |
| API key geçersiz hatası | 21st.dev console'dan yeni key üret, settings.json'ı güncelle |
| Bileşen yanlış klasöre eklendi | Magic MCP'ye prompt'ta `src/components/ui/` yolunu belirt |
| TypeScript hatası | Üretilen bileşende `any` → uygun type ile değiştir |
| Tailwind class'ları çalışmıyor | `tailwind.config.js` content path'ini kontrol et |
