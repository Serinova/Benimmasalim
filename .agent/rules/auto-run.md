---
description: Komut çalıştırma otomasyonu — silme dışındaki komutları otomatik çalıştır
---

# Auto-Run Kuralı

Aşağıdaki kategorilerdeki komutlar `SafeToAutoRun: true` olarak çalıştırılmalıdır (kullanıcıdan onay istenmez):

## ✅ Otomatik Çalıştırılacak Komutlar

- **Sunucu/Cloud komutları**: `gcloud`, `gsutil`, `cloud-sql-proxy`, `kubectl` vb.
  - `gcloud run services describe`, `gcloud run services list`
  - `gcloud run revisions list`, `gcloud run revisions describe`
  - `gcloud run services logs read`, `gcloud logging read`
  - `gcloud builds list`, `gcloud builds describe`
  - `gcloud run services update`, `gcloud run services update-traffic`
  - `gcloud secrets versions access`, `gcloud secrets list`
  - `gsutil ls`, `gsutil cp`, `gsutil cat`, `gsutil stat`
- **Deploy komutları**: `gcloud run deploy`, `gcloud builds submit` vb.
- **Dosya okuma/listeleme**: `cat`, `type`, `dir`, `ls`, `tree`, `Get-Content`, `Select-String` vb.
- **Git okuma komutları**: `git status`, `git log`, `git diff`, `git branch` vb.
- **Git yazma komutları**: `git add`, `git commit`, `git push`, `git pull` vb.
- **Paket yönetimi**: `npm install`, `pip install`, `npm run dev`, `npm run build` vb.
- **Script çalıştırma**: `python`, `node`, `bash`, `powershell` script'leri
- **İndirme/ağ komutları**: `curl`, `wget`, `Invoke-WebRequest`, `Invoke-RestMethod` vb.
- **Veritabanı komutları**: `alembic upgrade`, `alembic downgrade`, migration komutları
- **Ortam değişkenleri**: `$env:` atamaları, `set` komutları
- **Docker komutları**: `docker build`, `docker run`, `docker ps`, `docker logs` vb.

## ❌ Onay Gerektiren Komutlar (Otomatik Çalıştırılmaz)

- **Dosya/dizin silme**: `rm`, `del`, `Remove-Item`, `rmdir`, `rd` vb.
- **Toplu silme**: `git clean`, `docker system prune`, `docker image prune` vb.
- **Geri alınamaz işlemler**: Veritabanı drop/truncate, bucket silme vb.
