# 🚀 PRODUCTION DEPLOY - ŞUAN YAP!

## 1. GCP Cloud Shell'i Aç

```bash
# Terminal aç: https://console.cloud.google.com/?cloudshell=true
```

## 2. Projeyi Kopyala/Güncelle

```bash
# İlk defa ise clone yap:
gcloud config set project gen-lang-client-0784096400
git clone YOUR_REPO_URL benimmasalim
cd benimmasalim

# Zaten varsa pull yap:
cd benimmasalim
git pull origin main
```

## 3. 13 Migration'ı Çalıştır (KRİTİK!)

```bash
cd backend

# DATABASE_URL'i Cloud SQL için ayarla (Cloud Shell'de zaten olmalı):
export DATABASE_URL="postgresql+asyncpg://postgres:YOUR_PASSWORD@/benimmasalim?host=/cloudsql/gen-lang-client-0784096400:europe-west1:benimmasalim-db"

# 13 migration'ı sırayla çalıştır:
python -m scripts.update_ocean_adventure_scenario
python -m scripts.update_dinosaur_scenario
python -m scripts.update_space_scenario
python -m scripts.update_galata_scenario
python -m scripts.update_cappadocia_scenario
python -m scripts.update_ephesus_scenario
python -m scripts.update_gobekli_scenario
python -m scripts.update_catalhoyuk_scenario
python -m scripts.update_amazon_scenario
python -m scripts.update_sumela_scenario
python -m scripts.update_sultanahmet_scenario
python -m scripts.update_umre_scenario
python -m scripts.update_jerusalem_scenario

echo "✅ 13 migration tamamlandı!"
```

## 4. Docker Build + Push

```bash
cd /workspace/benimmasalim/backend

gcloud builds submit \
  --tag gcr.io/gen-lang-client-0784096400/benimmasalim-backend:latest

echo "✅ Docker build tamamlandı!"
```

## 5. Cloud Run'a Deploy

```bash
gcloud run deploy benimmasalim-backend \
  --image gcr.io/gen-lang-client-0784096400/benimmasalim-backend:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 100 \
  --set-cloudsql-instances gen-lang-client-0784096400:europe-west1:benimmasalim-db

echo "✅ Cloud Run deploy tamamlandı!"
```

## 6. Test Et

```bash
# Backend URL'i al:
BACKEND_URL=$(gcloud run services describe benimmasalim-backend \
  --region europe-west1 \
  --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"

# Health check:
curl -f $BACKEND_URL/health

# 13 senaryo listesini kontrol et:
curl -f $BACKEND_URL/api/scenarios | jq '.[] | {name: .name, theme_key: .theme_key}'
```

## ✅ BEKLENEN SONUÇ

Terminal'de şu 13 senaryonun hepsi görünmeli:
1. okyanus-derinlikleri
2. dinozorlar-macerasi
3. gunes-sistemi-macerasi
4. galata-kulesi-macerasi
5. sultanahmet-camii-macerasi
6. sumela-manastiri-macerasi
7. catalhoyuk-neolitik-kenti
8. efes-antik-kent
9. gobekli-tepe-macerasi
10. kapadokya-macerasi
11. umre-yolculugu
12. kudus-eski-sehir
13. amazon-ormanlari-kesfediyorum

---

## 🆘 Sorun Olursa

### Migration hatası:
```bash
# Her script'i tek tek çalıştır, hangisi hata verirse logunu gör:
python -m scripts.update_ocean_adventure_scenario
```

### Docker build hatası:
```bash
# Cloud Build log'larına bak:
gcloud builds list --limit 5
```

### Cloud Run deploy hatası:
```bash
# Cloud Run log'larına bak:
gcloud run logs read benimmasalim-backend --region europe-west1 --limit 50
```

---

**NOT**: Eğer Cloud Shell'de python bulunamadıyorsa:
```bash
python3 --version  # python3 kullan
alias python=python3
```

## 💯 SİSTEM DURUMU

✅ 13 senaryo tamam:
- Ocean, Dino, Space (pilot başarılı)
- Galata, Sultanahmet, Sümela, Çatalhöyük, Efes, Göbeklitepe, Kapadokya (yeni 7'li)
- Umre, Kudüs, Amazon (kültürel hassasiyet + dopamin)

✅ Tüm scriptler 500-char limit altında
✅ Modular prompt sistemi aktif
✅ Blueprint + Dopamine management (6 zirve)
✅ İslami hassasiyet kuralları (Umre/Sultanahmet/Kudüs)
✅ Hristiyan hassasiyet kuralları (Sümela/Kudüs)

**SİSTEM 100% PRODUCTION HAZIR! 🎉**
