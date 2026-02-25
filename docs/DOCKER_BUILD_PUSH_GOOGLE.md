# Docker Build & Push — Google Artifact Registry

Backend ve frontend image'larını build edip Google Artifact Registry'ye push etme.

## Gereksinimler

- **Google Cloud:** Proje açık, Artifact Registry API etkin, `europe-west1` bölgesinde `benimmasalim` repo'su oluşturulmuş olmalı.
- **gcloud CLI:** Kurulu ve `gcloud auth login` + `gcloud config set project PROJE_ID` yapılmış olmalı.
- **Cloud Build (sunucuda build için):** Cloud Build API etkin.
- **Docker (yerel build için):** Yerel Docker + `gcloud auth configure-docker europe-west1-docker.pkg.dev` yapılmış olmalı.

## Yöntem 1: Tek komut (Cloud Build — önerilen)

Build işlemi Google sunucusunda yapılır; sadece kaynak kodu gönderilir.

```bash
# Proje kökünden (BenimMasalim/)
gcloud builds submit --config=cloudbuild.yaml .
```

İsteğe bağlı parametreler (substitutions):

```bash
gcloud builds submit --config=cloudbuild.yaml . \
  --substitutions="_REGION=europe-west1,_REPO=benimmasalim,_TAG=latest"
```

Farklı tag:

```bash
gcloud builds submit --config=cloudbuild.yaml . \
  --substitutions="_TAG=v1.0.0"
```

## Yöntem 2: PowerShell (Windows)

```powershell
# Cloud Build ile (Google'da build)
.\scripts\build-push-google.ps1 -UseCloudBuild

# Proje belirtmek için
.\scripts\build-push-google.ps1 -UseCloudBuild -ProjectId "gen-lang-client-0784096400"

# Yerel Docker ile build + push (önce: gcloud auth configure-docker europe-west1-docker.pkg.dev)
.\scripts\build-push-google.ps1 -ProjectId "gen-lang-client-0784096400"
```

## Yöntem 3: Bash (Linux/macOS)

```bash
chmod +x scripts/build-push-google.sh

# Cloud Build
./scripts/build-push-google.sh --cloud-build

# Yerel Docker
./scripts/build-push-google.sh --project "gen-lang-client-0784096400"
```

## Sadece backend veya sadece frontend

Mevcut ayrı config'ler:

```bash
# Sadece backend
cd backend && gcloud builds submit --config=cloudbuild.yaml .

# Sadece frontend
cd frontend && gcloud builds submit --config=cloudbuild.yaml .
```

Bu dosyalar `europe-west1-docker.pkg.dev/PROJECT_ID/benimmasalim/backend:latest` ve `.../frontend:latest` kullanıyor (PROJECT_ID, `gcloud config get-value project` ile alınır).

## Push sonrası image adresleri

- Backend: `europe-west1-docker.pkg.dev/PROJECT_ID/benimmasalim/backend:latest`
- Frontend: `europe-west1-docker.pkg.dev/PROJECT_ID/benimmasalim/frontend:latest`

Cloud Run veya GKE’de bu image’ları kullanabilirsiniz.

## Artifact Registry repo yoksa

```bash
gcloud artifacts repositories create benimmasalim \
  --repository-format=docker \
  --location=europe-west1 \
  --description="BenimMasalim backend and frontend"
```

## Yerel test (push etmeden)

```bash
docker compose up -d --build
# Backend: http://localhost:8000, Frontend: http://localhost:3001
```
