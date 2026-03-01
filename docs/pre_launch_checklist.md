# 🚀 Benim Masalım — Canlıya Çıkış Öncesi Kontrol Listesi

**Tarih:** 2026-03-01  
**Durum:** Performans ✅ | Güvenlik ✅ | Refactoring ✅ | **Aşağıdakiler ❓**

---

## Zaten Yapılan Analizler

| Analiz | Durum | Rapor |
|--------|-------|-------|
| Performans Analizi | ✅ Tamamlandı | `docs/performance_analysis.md` |
| Güvenlik Analizi | ✅ Tamamlandı | `docs/security_analysis.md` |
| Refactoring Analizi | ✅ Tamamlandı | `docs/refactoring_analysis.md` |

---

## 🔴 KRİTİK — Bunlar Olmadan CANLIYA ÇIKMA

### 1. 💳 Ödeme Akışı Uçtan Uca Test

> [!CAUTION]
> Müşterinin parasını aldığın an her şey mükemmel çalışmalı. Tek bir hata = müşteri kaybı + yasal sorun.

- [ ] İyzico **production** anahtarlarıyla gerçek ödeme testi (1 TL test siparişi)
- [ ] Ödeme başarılı → kitap üretimi başlıyor mu?
- [ ] Ödeme başarısız → promo kod geri veriliyor mu?
- [ ] Ödeme sonrası webhook geliyor mu? (İyzico panelden kontrol)
- [ ] `verify-iyzico` endpoint'i production'da çalışıyor mu?
- [ ] %100 indirimli (ücretsiz) sipariş akışı çalışıyor mu?
- [ ] Fatura PDF'i oluşturuluyor mu?
- [ ] Fatura numarası sıralı ve boşluksuz mu?
- [ ] İade/iptal durumunda ne oluyor? (Manuel süreç tanımlı mı?)

**Tahmini süre:** 2-3 saat

---

### 2. 📧 Email Teslim Edilebilirlik Testi

> [!WARNING]
> Müşteriye email ulaşmazsa sipariş kaybolmuş gibi görünür. Destek talebi yağar.

- [ ] Gmail'e email gidiyor mu? (Spam klasörüne düşmüyor mu?)
- [ ] Outlook/Hotmail'e email gidiyor mu?
- [ ] Yandex Mail'e email gidiyor mu?
- [ ] Email içeriği düzgün render ediliyor mu? (Responsive HTML)
- [ ] Hikaye önizleme emaili → görseller yükleniyor mu?
- [ ] Şifre sıfırlama emaili → link çalışıyor mu?
- [ ] Sipariş tamamlandı emaili → PDF linki çalışıyor mu?
- [ ] SPF, DKIM, DMARC kayıtları DNS'te yapılandırılmış mı?
- [ ] Email gönderen adres `noreply@benimmasalim.com` gibi profesyonel mi?
- [ ] Gönderim limiti (günlük/saatlik) yeterli mi?

**Tahmini süre:** 2-3 saat

---

### 3. 📜 Yasal Uyumluluk (KVKK + Ticaret)

> [!CAUTION]
> Türkiye'de e-ticaret yapmak için yasal zorunluluklar var. Eksikse para cezası kesilir.

- [ ] **KVKK Aydınlatma Metni** sayfada var mı? (Zorunlu)
- [ ] **Gizlilik Politikası** sayfası var mı? (Zorunlu)
- [ ] **Kullanım Koşulları / Hizmet Sözleşmesi** var mı?
- [ ] **Mesafeli Satış Sözleşmesi** checkout'ta onaylatılıyor mu? (Zorunlu)
- [ ] **Ön Bilgilendirme Formu** checkout'ta gösteriliyor mu? (Zorunlu)
- [ ] **Cayma Hakkı** (14 gün) bilgisi var mı? (Kişiselleştirilmiş ürün istisnası belirtilmeli)
- [ ] **İletişim bilgileri** (adres, telefon, email) sitede var mı? (Zorunlu)
- [ ] **Ticaret Sicil No** veya **Vergi No** sitede görünüyor mu?
- [ ] Çocuk fotoğrafı için **açık rıza** alınıyor mu? (KVKK hassas veri)
- [ ] Çocuk fotoğrafları **30 gün sonra otomatik siliniyor** mu? (Kod var ✅, çalıştığını doğrula)
- [ ] **Cookie banner** var mı? (Google Analytics kullanılıyorsa zorunlu)
- [ ] Fatura kesim zorunluluğu → e-fatura/e-arşiv fatura entegrasyonu gerekli mi?
- [ ] **ETBİS kaydı** yapıldı mı? (E-ticaret yapan firmalar için zorunlu)

**Tahmini süre:** 1 gün (avukat danışmanlığı gerekebilir)

---

### 4. 💾 Yedekleme & Felaket Kurtarma

- [ ] PostgreSQL veritabanı **günlük otomatik yedek** alınıyor mu?
- [ ] Yedekten **geri yükleme testi** yapıldı mı?
- [ ] GCS'deki görseller yedekleniyor mu? (Bucket versioning açık mı?)
- [ ] Redis verisi kaybolursa ne olur? (Rate limit reset, token blacklist reset)
- [ ] Cloud Run servis çökerse otomatik restart var mı? (Evet, varsayılan ✅)
- [ ] DNS provider çökerse ne olur? (Secondary DNS var mı?)
- [ ] Tüm API anahtarları güvenli bir yerde saklanıyor mu? (GCP Secret Manager?)
- [ ] Kritik hata durumunda **admin'e bildirim** gidiyor mu? (Sentry + email?)

**Tahmini süre:** 3-4 saat

---

### 5. 💰 Maliyet İzleme & Bütçe Alarmları

> [!IMPORTANT]
> AI API'leri çok pahalı. Kontrol edilmezse tek bir viral günde binlerce dolar fatura gelebilir.

- [ ] **GCP Billing Alert** kuruldu mu? (Günlük $50, aylık $500 gibi)
- [ ] **Gemini API** maliyet limiti ayarlandı mı?
- [ ] Fal.ai / Replicate kullanımda mı? Maliyet limiti var mı?
- [ ] GCS depolama maliyeti tahmini yapıldı mı?
  - Sipariş başına ~16 görsel × ~2 MB = ~32 MB
  - 1000 sipariş = ~32 GB → aylık ~$1
- [ ] Cloud Run instance sayısı sınırlandırıldı mı? (`--max-instances`)
- [ ] Cloud SQL tier'ı uygun mu? (Başlangıç için db-f1-micro veya db-g1-small)
- [ ] **Tahmini aylık maliyet hesaplandı mı?**

```
Tahmini aylık maliyet (100 sipariş/ay):
├── Cloud Run:        ~$15-30
├── Cloud SQL:        ~$10-25
├── GCS Storage:      ~$1-5
├── Gemini API:       ~$20-50 (hikaye üretimi)
├── Gemini Image:     ~$50-100 (görsel üretimi)
├── Redis (Memorystore): ~$30-50
├── Domain + DNS:     ~$1-2
├── Email (SMTP):     ~$5-10
├── Sentry:           ~$0 (free tier) 
└── TOPLAM:           ~$130-275/ay
```

**Tahmini süre:** 2 saat

---

### 6. 🧪 Uçtan Uca Kullanıcı Akışı Testi

> [!IMPORTANT]
> Gerçek bir müşteri gibi siteyi baştan sona dene. Mobilde de!

- [ ] **Senaryo 1: Yeni Kullanıcı**
  - Siteye giriş → Senaryo seç → Çocuk bilgileri gir → Fotoğraf yükle
  - Hikaye üretilmesini bekle → Önizleme gör
  - Ödeme yap → Kitap üretimini takip et
  - Email al → PDF indir → Ses kitap dinle (varsa)

- [ ] **Senaryo 2: Misafir Kullanıcı**
  - Kayıt olmadan sipariş ver → Sonradan kayıt ol
  - Eski siparişler hesaba bağlanıyor mu?

- [ ] **Senaryo 3: Hata Durumları**
  - İnternet kesilirse ne oluyor?
  - Ödeme sayfasında tarayıcı kapatılırsa?
  - Görsel üretimi başarısız olursa? (Müşteriye bilgi veriliyor mu?)
  - Aynı siparişe iki kez ödeme yapılmaya çalışırsa?

- [ ] **Senaryo 4: Boyama Kitabı**
  - Boyama kitabı siparişi uçtan uca çalışıyor mu?

**Tahmini süre:** 4-6 saat

---

## ⚠️ ÖNEMLİ — Launch Haftasında Yapılmalı

### 7. 📊 SEO & Analytics

- [ ] Google Analytics 4 kuruldu mu?
- [ ] Google Search Console'a site eklendi mi?
- [ ] `robots.txt` var mı ve doğru mu?
- [ ] `sitemap.xml` var mı?
- [ ] Her sayfada `<title>` ve `<meta description>` var mı?
- [ ] Open Graph meta tag'leri var mı? (Sosyal medya paylaşımları)
- [ ] Sayfa hızı testi yapıldı mı? (Google PageSpeed Insights)
- [ ] Favicon var mı?

### 8. 📱 Mobil & Tarayıcı Uyumluluğu

- [ ] **iPhone Safari** — tüm akış çalışıyor mu?
- [ ] **Android Chrome** — tüm akış çalışıyor mu?
- [ ] **Desktop Chrome, Firefox, Edge** — test edildi mi?
- [ ] İyzico ödeme sayfası mobilde düzgün açılıyor mu?
- [ ] Responsive tasarım — tablet boyutlarında da güzel görünüyor mu?
- [ ] Fotoğraf yükleme — mobilde kamera açılıyor mu?

### 9. 🛎️ Müşteri Destek Hazırlığı

- [ ] İletişim formu veya WhatsApp butonu var mı?
- [ ] Sık sorulan sorular (SSS) sayfası hazır mı?
- [ ] Sipariş takip sayfası çalışıyor mu?
- [ ] Admin panelden sipariş durumu güncellenebiliyor mu?
- [ ] Takılı kalan siparişleri admin manuel tetikleyebiliyor mu?
- [ ] İade prosedürü tanımlı mı?

### 10. 🌐 DNS / SSL / Domain

- [ ] `benimmasalim.com` DNS yapılandırması tamamlandı mı?
- [ ] SSL sertifikası aktif mi? (Cloud Run otomatik ✅)
- [ ] `www.benimmasalim.com` → `benimmasalim.com` yönlendirmesi var mı?
- [ ] Backend API URL'i production domain'e bağlı mı?
- [ ] Frontend `.env.production`'da doğru API URL var mı?

### 11. 🤖 AI Çıktı Kalitesi

- [ ] En az **5 farklı senaryo** ile hikaye üretimi test edildi mi?
- [ ] Türkçe gramer ve yazım hataları var mı?
- [ ] Görseller çocuğa benziyor mu? (Yüz tutarlılığı)
- [ ] Görsellerde uygunsuz içerik riski var mı? (AI safety)
- [ ] Kapak sayfası tasarımı profesyonel görünüyor mu?
- [ ] PDF baskı kalitesi yeterli mi? (300 DPI kontrol)
- [ ] Metin ve görsel sayfa düzeni doğru mu? (Text overlay okunuyor mu?)

---

## 💡 LAUNCH SONRASI — İlk 2 Hafta

### 12. İzleme & Optimizasyon

- [ ] Sentry hataları günlük kontrol ediliyor mu?
- [ ] Sipariş başarı oranı takip ediliyor mu? (Başlayan vs tamamlanan)
- [ ] Ortalama sipariş süresi kabul edilebilir mi?
- [ ] Müşteri geri bildirimleri toplanıyor mu?
- [ ] Google Analytics trafiği izleniyor mu?
- [ ] Cloud Run CPU/memory metrikleri normal mi?
- [ ] Takılı sipariş kurtarma (`stuck_order_recovery`) çalışıyor mu?

---

## 📋 ÖZET — Öncelik Sırası

```
🔴 ZORUNLU (Canlıya çıkma)
 1. Ödeme akışı uçtan uca test               ⏱️ 2-3 saat
 2. Email teslim testi                        ⏱️ 2-3 saat
 3. Yasal uyumluluk (KVKK, sözleşmeler)      ⏱️ 1 gün
 4. Yedekleme & felaket kurtarma              ⏱️ 3-4 saat
 5. Maliyet izleme & alarmlar                 ⏱️ 2 saat
 6. Uçtan uca kullanıcı testi                 ⏱️ 4-6 saat

⚠️ ÖNEMLİ (Launch haftası)
 7. SEO & Analytics                           ⏱️ 2 saat
 8. Mobil & tarayıcı uyumluluk                ⏱️ 3 saat
 9. Müşteri destek hazırlığı                  ⏱️ 2 saat
10. DNS / SSL / Domain                        ⏱️ 1 saat
11. AI çıktı kalitesi                         ⏱️ 3 saat

💡 LAUNCH SONRASI
12. İzleme & optimizasyon                     ⏱️ Sürekli

TOPLAM TAHMİN: ~3-4 gün
```

---

> [!NOTE]
> En kritik 3 madde: **Ödeme testi**, **Yasal uyumluluk** ve **Email teslim**. Bunlar eksikse siteyi AÇMA — müşteri kaybı + yasal risk.
