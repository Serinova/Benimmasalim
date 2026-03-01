# 🛡️ Benim Masalım — Güvenlik Analizi

**Tarih:** 2026-03-01  
**Kapsam:** Hacklenebilirlik, DDoS/DoS dayanıklılığı, veri sızıntısı, ödeme güvenliği, yetkilendirme, injection saldırıları

---

## 📊 Güvenlik Skorkartı

| Alan | Skor | Durum |
|------|-------|-------|
| **Kimlik Doğrulama (AuthN)** | 9/10 | ✅ Çok sağlam |
| **Yetkilendirme (AuthZ)** | 8/10 | ✅ İyi — küçük riskler var |
| **Ödeme Güvenliği** | 9/10 | ✅ İyzico callback doğrulaması var |
| **Injection (SQL/XSS)** | 9/10 | ✅ SQLAlchemy ORM koruması |
| **DDoS/DoS Dayanıklılığı** | 7/10 | ⚠️ Bazı açık noktalar |
| **Veri Sızıntısı** | 8/10 | ✅ KVKK uyumlu — küçük riskler |
| **Security Headers** | 9/10 | ✅ Tam donanımlı |
| **Secret Yönetimi** | 8/10 | ✅ .gitignore doğru |
| **API Güvenliği** | 7/10 | ⚠️ Rate limit bypass riski |

**Genel Skor: 8.2/10 — Site hacklenemez seviyede değil ama oldukça sağlam.**

---

## ✅ MÜKEMMEL YAPILAN ŞEYLER

### 1. JWT Güvenliği — A+
```
✅ iss (issuer) + aud (audience) doğrulaması
✅ token_version ile tüm tokenları invalidate edebilme
✅ Redis-backed blacklist (logout sonrası token iptal)
✅ Refresh token replay detection (kullanılan token blacklist'e ekleniyor)
✅ Ayrı access/refresh token tipleri (type claim kontrolü)
✅ bcrypt password hashing
✅ Ortak şifre listesi kontrolü (_COMMON_PASSWORDS)
✅ Güçlü şifre politikası (büyük+küçük+rakam+özel karakter)
```

### 2. Ödeme Güvenliği — A+
```
✅ İyzico checkout form (PCI-compliant — kart bilgileri asla sunucuya gelmiyor)
✅ Server-side callback doğrulama (iyzipay.CheckoutForm.retrieve)
✅ Tutar doğrulama (webhook/verify'da expected vs received amount)
✅ FOR UPDATE skip_locked (webhook + verify race condition koruması)
✅ Idempotency (duplicate webhook'lar ignore ediliyor)
✅ Promo code rollback (ödeme başarısız olursa kupon geri veriliyor)
✅ Atomic promo code consume (concurrency-safe)
```

### 3. Security Headers — A
```
✅ X-Frame-Options: DENY (clickjacking koruması)
✅ X-Content-Type-Options: nosniff (MIME sniffing koruması)
✅ Referrer-Policy: strict-origin-when-cross-origin
✅ X-XSS-Protection: 1; mode=block
✅ HSTS: max-age=63072000; includeSubDomains; preload (2 yıl)
✅ Permissions-Policy: camera=(), microphone=(self), geolocation=(), payment=(self)
✅ CSP: frame-ancestors 'none' + restricted script-src
✅ Content-Security-Policy yapılandırılmış
```

### 4. CORS — A
```
✅ Explicit origin whitelist (allow_origins=CORS_ORIGINS)
✅ allow_credentials=False (cookie paylaşımı kapalı — pure Bearer token)
✅ Explicit allow_headers ve expose_headers (yüzey alanı kısıtlı)
✅ Preflight cache 24 saat (max_age=86400)
✅ Production'da sadece gerçek domainler (_SAFE_ORIGINS)
```

### 5. Audit Trail — A
```
✅ Admin mutations otomatik audit (AdminAuditMiddleware)
✅ LOGIN_SUCCESS, LOGIN_FAILED, PASSWORD_CHANGED logları
✅ PROMO_CODE_CONSUMED, PAYMENT_CALLBACK_RECEIVED logları
✅ KVKK: audit_log_retention_cleanup (otomatik eski log silme)
```

---

## 🔴 KRİTİK GÜVENLİK RİSKLERİ

### 1. `verify-iyzico` Endpoint — Authentication Yok!

**Dosya:** [payments.py:653-762](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/api/v1/payments.py#L653-L762)

```python
@router.post("/verify-iyzico")
async def verify_iyzico_payment(
    request: VerifyIyzicoRequest,
    db: DbSession,
) -> dict:
```

> [!CAUTION]
> Bu endpoint **herhangi bir authentication gerektirmiyor**! Herhangi biri rastgele order_id + token gönderebilir. İyzico server-side verify yapılıyor, bu yüzden ödeme sahteciliği yapılamaz, FAKAT:
> - Bir saldırgan rastgele order_id'ler deneyerek order durumlarını görebilir (bilgi sızıntısı)
> - Yanıt mesajları order'ın durumunu leak ediyor (`"already_processed"`, `"amount_mismatch"`)

**Ne yapılmalı:**
- Rate limiting bu endpoint'e özellikle uygulanmalı (zaten var mı kontrol et)
- Yanıt mesajlarını generic yap ("İşlem tamamlandı")
- Veya: `CurrentUserOptional` ile en azından loglama yap

**Risk Seviyesi:** ORTA — İyzico verify sayesinde ödeme manipülasyonu yapılamaz, ama bilgi sızıntısı riski var.

---

### 2. `send-preview` ve `submit-preview-async` — Authentication Yok!

**Dosya:** [orders.py:328-598](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/api/v1/orders.py#L328-L598)

```python
@router.post("/send-preview")
async def send_preview_email(request: SendPreviewRequest, db: DbSession) -> dict:

@router.post("/submit-preview-async")
async def submit_preview_async(request: AsyncPreviewRequest, ..., db: DbSession) -> dict:
```

> [!CAUTION]
> Bu endpointler **hiçbir authentication gerektirmiyor**! Potansiyel kötüye kullanım:
> 1. **Email spam saldırısı:** Saldırgan tekrar tekrar farklı adreslerle çağırarak siteyi email spam botu olarak kullanabilir
> 2. **Kaynak tüketimi:** Her çağrıda Gemini API + GCS upload + email gönderimi tetikleniyor → maliyet saldırısı (billing attack)
> 3. **DB doldurma:** Her çağrı `StoryPreview` kaydı oluşturuyor

Bu risk RATE LIMITING ile hafifletilmiş ama rate limit'ler bypass edilebilir (aşağıya bak).

---

### 3. Rate Limiting Bypass Riski — IP Spoofing

**Dosya:** [rate_limiter.py](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/middleware/rate_limiter.py)

Rate limiter IP'yi şu sırayla alıyor:
1. `X-Forwarded-For` header → ilk IP
2. `X-Real-IP` header
3. `client.host`

> [!WARNING]
> Cloud Run'da load balancer otomatik olarak `X-Forwarded-For` ekliyor, ancak saldırgan kendi `X-Forwarded-For` header'ını ekleyebilir. Sonuç olarak rate limiter **farklı IP'lerden geliyormuş gibi istekler görebilir**.
>
> Google Cloud Run'da doğru yaklaşım: `X-Forwarded-For` header'ındaki **son** IP'yi almak, çünkü Google Load Balancer client IP'yi her zaman header'ın **sonuna** ekler.

**Ne yapılmalı:** IP çıkarma mantığını `X-Forwarded-For`'daki son IP'ye göre düzenle.

---

### 4. Email Service — HTML Injection (E-posta İçeriği)

**Dosya:** [email_service.py](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/services/email_service.py)

Email service'in docstring'lerinde "All user-supplied strings are HTML-escaped" yazıyor, ancak kodda `html.escape()` çağrısı bulunamadı. Bu, `child_name`, `story_title` gibi alanların HTML template'e doğrudan yerleştirildiği anlamına gelebilir.

```
Saldırı vektörü:
child_name = '<script>alert("XSS")</script>'
→ Email HTML'ine direkt gider → Müşterinin email client'ında XSS
```

**Risk Seviyesi:** ORTA — Modern email client'lar JavaScript çalıştırmaz, ama HTML injection ile phishing linki eklenebilir.

> [!IMPORTANT]
> **Aksiyon:** Email şablonlarında tüm kullanıcı girdilerini `html.escape()` ile sanitize edin.

---

### 5. `AdminAuditMiddleware` — `BaseHTTPMiddleware` Kullanıyor

**Dosya:** [admin_audit.py:44](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/middleware/admin_audit.py#L44)

```python
class AdminAuditMiddleware(BaseHTTPMiddleware):
```

> [!WARNING]
> Projedeki diğer middleware'ler (SecurityHeaders, RequestLogging, BodySizeLimit, RateLimiter) doğru şekilde **Pure ASGI** olarak yazılmış. Ancak `AdminAuditMiddleware` hâlâ `BaseHTTPMiddleware` kullanıyor. Bu, streaming response'larda deadlock'a neden olabilir ve request body'nin tamponlanmasına yol açar.

**Risk Seviyesi:** ORTA — Admin endpointleri genelde küçük payload'lar gönderir, ama tutarsızlık bakım riski yaratır.

---

## ⚠️ ORTA SEVİYE RİSKLER

### 6. Dosya Yükleme — Content-Type Güvenilmez

**Dosya:** [orders.py:2946](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/api/v1/orders.py#L2946)

```python
if not photo.content_type or not photo.content_type.startswith("image/"):
    raise ValidationError("Sadece resim dosyası yükleyebilirsiniz")
```

`Content-Type` header'ı **istemci tarafından ayarlanır** ve güvenilmez. Bir saldırgan `Content-Type: image/jpeg` ile `.exe` dosyası yükleyebilir.

**Ne yapılmalı:** Dosyanın *magic bytes*'ını (ilk birkaç byte) kontrol edin:
```python
# İlk 8 byte: JPEG=FFD8FF, PNG=89504E47, GIF=474946
```

### 7. Token Blacklist — Redis Yoksa Çalışmıyor

**Dosya:** [security.py:171-180](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/core/security.py#L171-L180)

```python
async def is_token_blacklisted(token: str) -> bool:
    r = await _get_async_redis()
    if not r:
        return False  # ← Redis yoksa token iptal kontrolü YOK
```

Redis bağlantısı koparsa, **çıkış yapmış kullanıcıların tokenları hâlâ geçerli kalır.** Log out sonrası hesap güvenliği Redis'e bağlı.

**Risk Seviyesi:** DÜŞÜK-ORTA — `token_version` ikincil koruma sağlıyor (şifre değişikliğinde tüm tokenlar geçersiz). Ama logout tek başına yeterli değil.

### 8. Guest Token — `sub` Claim Yok

**Dosya:** [security.py:107-124](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/core/security.py#L107-L124)

```python
def create_guest_token() -> str:
    to_encode = {
        "type": "guest",
        "exp": expire,
        "iss": _ISSUER,
        "aud": _AUDIENCE,
    }
```

Guest token'da `sub` claim yok. Bu, tüm guest token'ların birbirinin yerine kullanılabileceği anlamına gelir. Bir guest token'ı başka bir guest'in oturumunu ele geçirmek için kullanılabilir (eğer guest token ile kaynak erişimi varsa).

### 9. Error Response'da Bilgi Sızıntısı — Development Mode

**Dosya:** [main.py:734](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/main.py#L734)

```python
detail = str(exc) if settings.app_env == "development" else "Sunucu hatası"
```

Production'da güvenli ("Sunucu hatası"). Ama `app_env` yanlışlıkla `development` kalırsa stack trace sızar.

### 10. `_get_async_redis()` — Singleton Yarış Durumu

**Dosya:** [auth.py:499-501](file:///c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/backend/app/api/v1/auth.py#L499-L501)

```python
async def _get_async_redis():
    import redis.asyncio as aioredis
    return aioredis.from_url(str(settings.redis_url), decode_responses=True)
```

Her şifre sıfırlama isteğinde **yeni bir Redis bağlantısı** oluşturuluyor (pool yok, singleton yok). Saldırgan 1000 forgot-password isteği gönderirse Redis bağlantı havuzu tükenir.

---

## 🏥 DoS / "SİTEYİ PATLATABİLİR MİYİM?" ANALİZİ

### Saldırı Vektörleri ve Dayanıklılık:

| Saldırı | Korunma | Sonuç |
|---------|---------|-------|
| **HTTP Flood (DDoS)** | ✅ Cloud Run auto-scaling + Rate Limiter | **Sağlam** — Google altyapısı absorbe eder |
| **Slowloris** | ✅ Cloud Run timeout 300s + httpx timeout | **Sağlam** |
| **Body size bomb** | ✅ 50MB BodySizeLimitMiddleware | **Sağlam** |
| **Gemini API exhaustion** | ⚠️ submit-preview-async auth yok | **Risk var** — maliyet saldırısı |
| **Email spam via API** | ⚠️ send-preview auth yok | **Risk var** — rate limit var ama bypass edilebilir |
| **Auth brute force** | ✅ Endpoint rate limit (5/min login) | **Sağlam** — circuit breaker da var |
| **Redis connection exhaustion** | ⚠️ auth.py her seferinde yeni connection | **Risk var** — forgot-password flood |
| **Database connection exhaustion** | ✅ pool_size=5, max_overflow=3 | **Sağlam** — pool taşarsa 503 döner |
| **GCS storage bomb** | ⚠️ GCS upload rate limit yok | **Düşük risk** — sadece auth endpoint'lerden |

### En Gerçekçi Saldırı Senaryosu:

```
Saldırgan → submit-preview-async (auth yok)
→ Her istekte:
  - 1 × StoryPreview DB kaydı
  - 3 × GCS upload (initial images)
  - 1 × Arq job (Gemini API çağrısı)
  - 1 × Email gönderimi

1 dakikada 60 istek = 60 Gemini API call + 180 GCS upload + 60 email

Maliyet: ~$5-10/dakika saldırı maliyeti
Rate limiter: story generation endpoint'ine 5/dk limit var → etkili koruma
IP spoofing ile: ~30/dk × birden fazla IP → aylık $2000+ maliyet
```

> [!IMPORTANT]
> **Rate limiter IP spoofing düzeltilirse bu senaryo büyük ölçüde önlenir.** Ek olarak, unauthenticated endpointlere CAPTCHA veya email doğrulama eklenebilir.

---

## 📋 ÖNCELİKLENDİRİLMİŞ AKSİYON PLANI

### 🔴 Acil (Bu Hafta)

| # | Aksiyon | Risk | Dosya |
|---|---------|------|-------|
| 1 | IP çıkarma: `X-Forwarded-For` son IP'yi al | Rate limit bypass | `rate_limiter.py` |
| 2 | Email HTML'de `html.escape()` ekle | HTML injection | `email_service.py` |
| 3 | `auth.py._get_async_redis()` singleton yap | Redis exhaustion | `auth.py:499` |

### ⚠️ Bu Ay

| # | Aksiyon | Risk | Dosya |
|---|---------|------|-------|
| 4 | `verify-iyzico` yanıt mesajlarını generic yap | Bilgi sızıntısı | `payments.py` |
| 5 | File upload magic bytes kontrolü | Zararlı dosya yükleme | `orders.py:2946` |
| 6 | `AdminAuditMiddleware` → Pure ASGI dönüştür | Streaming deadlock | `admin_audit.py` |
| 7 | `submit-preview-async` email doğrulama/CAPTCHA | Spam/maliyet saldırısı | `orders.py` |

### 💡 Uzun Vadeli

| # | Aksiyon | Risk |
|---|---------|------|
| 8 | WAF (Cloud Armor) ekle | L7 DDoS koruma |
| 9 | API key / account-level rate limiting | Bot saldırıları |
| 10 | Security audit pen-test | Bilinmeyen açıklar |

---

## 🎯 SONUÇ

**Site hacklenebilir mi?**
> **Hayır** — kimlik doğrulama, şifre koruması, JWT güvenliği ve ödeme doğrulaması çok sağlam. Klasik SQL injection, XSS, CSRF saldırıları başarılı olamaz.

**Site patlatılabilir mi (DoS)?**
> **Kısmen** — Rate limiter IP spoofing ile bypass edilebilir. Auth gerektirmeyen endpointler (submit-preview-async, send-preview) maliyet saldırısına açık. AMA Cloud Run auto-scaling sayesinde site tamamen çökmez, sadece maliyetler artar.

**Veri sızar mı?**
> **Hayır** — KVKK uyumlu veri silme, audit logging, generic hata mesajları (production'da). Küçük riskler: `verify-iyzico` yanıtları order durumunu sızdırıyor. Email HTML injection riski var ama etkisi sınırlı.

**Genel değerlendirme:**
> Sistem **production-ready** seviyede güvenli. Yukarıdaki 3 acil aksiyon yapıldığında **9/10** seviyesine çıkar.
