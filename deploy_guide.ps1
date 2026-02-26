# ============================================================================
# BENİMMASALIM - COLORING BOOK UPDATE + FULL DEPLOYMENT (PowerShell)
# ============================================================================
# Bu script Google Cloud Shell'de çalıştırılmalıdır!
# Cloud Shell kullanımı: https://console.cloud.google.com/
# ============================================================================

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  BENİMMASALIM - COLORING BOOK DEPLOYMENT     ║" -ForegroundColor Blue
Write-Host "║  Docker Build + Google Cloud Run Deploy      ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

Write-Host "⚠️  IMPORTANT: This script must run in Google Cloud Shell!" -ForegroundColor Yellow
Write-Host "   1. Go to: https://console.cloud.google.com/" -ForegroundColor Yellow
Write-Host "   2. Click 'Activate Cloud Shell' (top right)" -ForegroundColor Yellow
Write-Host "   3. Upload this project or clone from Git" -ForegroundColor Yellow
Write-Host "   4. Run: chmod +x deploy_coloring_book.sh" -ForegroundColor Yellow
Write-Host "   5. Run: ./deploy_coloring_book.sh" -ForegroundColor Yellow
Write-Host ""

# GCP Configuration
$PROJECT_ID = "gen-lang-client-0784096400"
$REGION = "europe-west1"

Write-Host "📋 DEPLOYMENT CHECKLIST:" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Frontend Linter Errors Fixed:" -ForegroundColor Green
Write-Host "   - products/page.tsx: Escaped quotes" -ForegroundColor White
Write-Host "   - scenarios/page.tsx: Escaped quotes" -ForegroundColor White
Write-Host ""
Write-Host "✅ Backend Updates:" -ForegroundColor Green
Write-Host "   - Image processing simplified (80/200 thresholds)" -ForegroundColor White
Write-Host "   - Coloring book migration updated" -ForegroundColor White
Write-Host "   - Seed script optimized" -ForegroundColor White
Write-Host ""
Write-Host "✅ Frontend Updates:" -ForegroundColor Green
Write-Host "   - Homepage: Features + Pricing updated" -ForegroundColor White
Write-Host "   - Checkout: Coloring book checkbox" -ForegroundColor White
Write-Host "   - Payment: Iyzico integration" -ForegroundColor White
Write-Host ""

Write-Host "📦 FILES READY FOR DEPLOYMENT:" -ForegroundColor Green
Write-Host "   Backend:" -ForegroundColor White
Write-Host "   - backend/Dockerfile" -ForegroundColor Gray
Write-Host "   - backend/requirements.txt" -ForegroundColor Gray
Write-Host "   - backend/app/ (all Python code)" -ForegroundColor Gray
Write-Host ""
Write-Host "   Frontend:" -ForegroundColor White
Write-Host "   - frontend/Dockerfile" -ForegroundColor Gray
Write-Host "   - frontend/package.json" -ForegroundColor Gray
Write-Host "   - frontend/src/ (all TypeScript code)" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 NEXT STEPS (in Google Cloud Shell):" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Upload project to Cloud Shell:" -ForegroundColor Yellow
Write-Host "   gsutil -m rsync -r . gs://$PROJECT_ID-deployment/latest/" -ForegroundColor White
Write-Host "   OR clone from your Git repo" -ForegroundColor White
Write-Host ""
Write-Host "2. Set GCP project:" -ForegroundColor Yellow
Write-Host "   gcloud config set project $PROJECT_ID" -ForegroundColor White
Write-Host ""
Write-Host "3. Run deployment script:" -ForegroundColor Yellow
Write-Host "   chmod +x deploy_coloring_book.sh" -ForegroundColor White
Write-Host "   ./deploy_coloring_book.sh" -ForegroundColor White
Write-Host ""

Write-Host "📚 OR use gcloud commands directly:" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Backend Deploy" -ForegroundColor Yellow
Write-Host "cd backend" -ForegroundColor White
Write-Host "gcloud builds submit --tag gcr.io/$PROJECT_ID/benimmasalim-backend:latest" -ForegroundColor White
Write-Host "gcloud run deploy benimmasalim-backend \" -ForegroundColor White
Write-Host "  --image gcr.io/$PROJECT_ID/benimmasalim-backend:latest \" -ForegroundColor White
Write-Host "  --region $REGION \" -ForegroundColor White
Write-Host "  --allow-unauthenticated" -ForegroundColor White
Write-Host ""
Write-Host "# Frontend Deploy" -ForegroundColor Yellow
Write-Host "cd ../frontend" -ForegroundColor White
Write-Host "gcloud builds submit --tag gcr.io/$PROJECT_ID/benimmasalim-frontend:latest" -ForegroundColor White
Write-Host "gcloud run deploy benimmasalim-frontend \" -ForegroundColor White
Write-Host "  --image gcr.io/$PROJECT_ID/benimmasalim-frontend:latest \" -ForegroundColor White
Write-Host "  --region $REGION \" -ForegroundColor White
Write-Host "  --allow-unauthenticated" -ForegroundColor White
Write-Host ""

Write-Host "✅ Local changes are ready!" -ForegroundColor Green
Write-Host "   Now deploy from Google Cloud Shell for production." -ForegroundColor White
Write-Host ""

# Create deployment guide file
$guideContent = @"
# BOYAMA KİTABI DEPLOYMENT KILAVUZU

## Önkoşullar
- Google Cloud Shell erişimi
- Project: $PROJECT_ID
- Region: $REGION

## Adım 1: Cloud Shell'i Aç
1. https://console.cloud.google.com/ adresine git
2. Sağ üstten "Activate Cloud Shell" butonuna tıkla
3. Terminal açılacak

## Adım 2: Projeyi Yükle
```bash
# Git ile (önerilen)
git clone YOUR_REPO_URL
cd benimmasalim

# Veya dosyaları manuel yükle (Cloud Shell'in Upload özelliğini kullan)
```

## Adım 3: GCP Projesi Ayarla
```bash
gcloud config set project $PROJECT_ID
gcloud auth login  # Gerekirse
```

## Adım 4: Deployment Script'ini Çalıştır
```bash
chmod +x deploy_coloring_book.sh
./deploy_coloring_book.sh
```

## Deployment İçeriği
✅ Linter hataları düzeltildi
✅ Backend: Image processing basitleştirildi
✅ Frontend: Homepage + Checkout güncellendi
✅ Database: Coloring book migration
✅ Docker: Backend + Frontend build
✅ Cloud Run: Production deployment

## Test
```bash
# Backend health
curl https://benimmasalim-backend-HASH.run.app/health

# Coloring book API
curl https://benimmasalim-backend-HASH.run.app/api/v1/coloring-books/active

# Frontend
curl https://benimmasalim-frontend-HASH.run.app
```

## Troubleshooting

### Build Timeout
```bash
gcloud builds submit --timeout=30m
```

### Memory Issues
```bash
gcloud run deploy ... --memory 4Gi
```

### Migration Issues
```bash
# SSH to Cloud SQL
gcloud sql connect benimmasalim-db --user=postgres

# Run migration manually
cd backend
alembic upgrade head
```

## Rollback
```bash
# List revisions
gcloud run revisions list --service benimmasalim-backend

# Rollback
gcloud run services update-traffic benimmasalim-backend \
  --to-revisions REVISION_NAME=100
```

## Monitoring
```bash
# Logs
gcloud run services logs read benimmasalim-backend --region $REGION

# Metrics
https://console.cloud.google.com/run?project=$PROJECT_ID
```
"@

Set-Content -Path "DEPLOYMENT_GUIDE.md" -Value $guideContent -Encoding UTF8

Write-Host "📄 Deployment guide created: DEPLOYMENT_GUIDE.md" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Sistem hazır! Google Cloud Shell'den deploy edin." -ForegroundColor Green
