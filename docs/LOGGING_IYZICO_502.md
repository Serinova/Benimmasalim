# Ödeme 502 Hatası — Iyzico Loglarına Bakma

**TRIAL_IYZICO_CHECKOUT** log’ları, ödeme sayfası oluşturulurken Iyzico’da ne olduğunu gösterir.

## Nereden bakılır?

1. **Google Cloud Console**’u aç: https://console.cloud.google.com/
2. Üstten **projeyi seç**: `gen-lang-client-0784096400` (veya kullandığın proje).
3. Sol menüden **Logging** → **Logs Explorer**’a gir  
   (veya doğrudan: https://console.cloud.google.com/logs/query )
4. **Sorgu kutusuna** şunu yapıştır:

```
resource.type="cloud_run_revision"
resource.labels.service_name="benimmasalim-backend"
jsonPayload.message=~"TRIAL_IYZICO_CHECKOUT"
```

   Veya sadece mesajda geçen kelimeyle ara:

```
TRIAL_IYZICO_CHECKOUT
```

5. **Zaman aralığı**: Sağ üstten son 1 saat / 6 saat / 24 saat seç.
6. **Run query** (Sorguyu çalıştır) de.

## Ne anlama gelir?

- **TRIAL_IYZICO_CHECKOUT_ERROR**: Iyzico API’ye istek atılırken hata (timeout, bağlantı, SSL).  
  `error`, `error_type`, `iyzico_base_url` alanlarına bak.
- **TRIAL_IYZICO_CHECKOUT_FAILED**: Iyzico işlemi yaptı ama başarısız döndü.  
  `error`, `error_code`, `full_response` alanlarına bak.

Bu alanlar 502’nin gerçek nedenini (yanlış anahtar, callback URL, Iyzico limiti vb.) gösterir.
