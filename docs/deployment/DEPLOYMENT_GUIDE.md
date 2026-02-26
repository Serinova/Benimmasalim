# BOYAMA KÄ°TABI DEPLOYMENT KILAVUZU

## Ã–nkoÅŸullar
- Google Cloud Shell eriÅŸimi
- Project: 
- Region: 

## AdÄ±m 1: Cloud Shell'i AÃ§
1. https://console.cloud.google.com/ adresine git
2. SaÄŸ Ã¼stten "Activate Cloud Shell" butonuna tÄ±kla
3. Terminal aÃ§Ä±lacak

## AdÄ±m 2: Projeyi YÃ¼kle
`ash
# Git ile (Ã¶nerilen)
git clone YOUR_REPO_URL
cd benimmasalim

# Veya dosyalarÄ± manuel yÃ¼kle (Cloud Shell'in Upload Ã¶zelliÄŸini kullan)
`

## AdÄ±m 3: GCP Projesi Ayarla
`ash
gcloud config set project 
gcloud auth login  # Gerekirse
`

## AdÄ±m 4: Deployment Script'ini Ã‡alÄ±ÅŸtÄ±r
`ash
chmod +x deploy_coloring_book.sh
./deploy_coloring_book.sh
`

## Deployment Ä°Ã§eriÄŸi
âœ… Linter hatalarÄ± dÃ¼zeltildi
âœ… Backend: Image processing basitleÅŸtirildi
âœ… Frontend: Homepage + Checkout gÃ¼ncellendi
âœ… Database: Coloring book migration
âœ… Docker: Backend + Frontend build
âœ… Cloud Run: Production deployment

## Test
`ash
# Backend health
curl https://benimmasalim-backend-HASH.run.app/health

# Coloring book API
curl https://benimmasalim-backend-HASH.run.app/api/v1/coloring-books/active

# Frontend
curl https://benimmasalim-frontend-HASH.run.app
`

## Troubleshooting

### Build Timeout
`ash
gcloud builds submit --timeout=30m
`

### Memory Issues
`ash
gcloud run deploy ... --memory 4Gi
`

### Migration Issues
`ash
# SSH to Cloud SQL
gcloud sql connect benimmasalim-db --user=postgres

# Run migration manually
cd backend
alembic upgrade head
`

## Rollback
`ash
# List revisions
gcloud run revisions list --service benimmasalim-backend

# Rollback
gcloud run services update-traffic benimmasalim-backend \
  --to-revisions REVISION_NAME=100
`

## Monitoring
`ash
# Logs
gcloud run services logs read benimmasalim-backend --region 

# Metrics
https://console.cloud.google.com/run?project=
`
