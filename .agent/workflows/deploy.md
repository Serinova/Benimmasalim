---
description: Projeyi baştan sona (Frontend veya Backend) Google Cloud'a yayımlama (Deploy) yönergesi
---
Bu workflow, "Benim Masalım" projesinin Backend (Cloud Run) veya Frontend (Vercel/Static) kısımlarını canlıya (Production) almak için gerekli adımları içermektedir.

**Nasıl Kullanılır:**
Kullanıcı chat üzerine `/deploy` veya `/yayinla` yazdığında Antigravity (asistan), sırasıyla bu adımları izleyecek ve sistemi yayına alacaktır.

// turbo
1. Kullanıcıdan hangi kısmı yayına alacağının onayını al: Sadece Backend mi, Sadece Frontend mi, yoksa İkisi birden mi (Full Deploy)?

// turbo
2. **Eğer Backend seçildiyse;**
  - Projenin `backend` klasöründe veritabanı değişiklikleri olup olmadığını kontrol et (Alembic versions).
  - Tünelin (`cloud-sql-proxy.exe`) açık olduğundan emin ol. Mümkün değilse kullanıcıdan açmasını iste.
  - Sadece Backend'i güncelleyen `deploy_backend_only.sh` (veya ilgili bash) dosyasını powershell üzerinden çalıştır.

// turbo
3. **Eğer Frontend seçildiyse;**
  - Proje kök dizinindeki veya `frontend/` içerisindeki arayüz bileşenlerinin hatasız (`npm run build`) derlendiğinden emin olmak için basit bir pre-check çalıştır.
  - Vercel (veya projenin kullandığı sistem üzerinden) frontend deploy işlemlerini başlat. (Not: Genelde GitHub üzerinden Vercel otomatik deploy alır. Eğer öyleyse, kullanıcıya "Kodları git push komutuyla GitHub'a gönderiyorum, Vercel otomatik olarak siteyi güncelleyecektir" bilgisini ver ve Push et).

// turbo
4. **Eğer Tam (Full) Deploy seçildiyse;**
  - `deploy_full.sh` veya `deploy_production.sh` dosyasını çalıştırarak önce backend'i sonra da frontend'i güncellemeye yarayan işlemleri başlat.

// turbo
5. Süreç bitiminde logları (Deployment Success/Failed Message) kontrol et ve web sitelerinin erişilebilir (Status: 200 OK) URL'lerini kullanıcıyla paylaş. Hata varsa hataların en altındaki kırmızı satırları kullanıcıya Türkçe özetle.
