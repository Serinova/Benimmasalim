# Benim Masalım

Yapay zeka destekli, kişiselleştirilmiş çocuk hikaye kitapları platformu.

## Teknoloji Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Queue**: Google Cloud Tasks
- **Storage**: Google Cloud Storage

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: shadcn/ui + Tailwind CSS
- **State**: TanStack Query + Zustand
- **Auth**: NextAuth.js

### AI Services
- **Text**: Google Gemini 1.5 Pro
- **Image**: Fal.ai (SDXL + InstantID)
- **Voice**: ElevenLabs
- **Face**: InsightFace

## Proje Yapısı

```
benim-masalim/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Security, config
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── tasks/        # Background jobs
│   ├── alembic/          # DB migrations
│   └── tests/
├── frontend/             # Next.js frontend
│   ├── src/
│   │   ├── app/          # App Router pages
│   │   ├── components/   # React components
│   │   ├── lib/          # Utilities
│   │   └── hooks/        # Custom hooks
│   └── public/
├── infra/                # Infrastructure
│   ├── terraform/        # GCP IaC
│   └── docker-compose.yml
└── .cursor/rules/        # AI coding rules
```

## Kurulum

### Gereksinimler
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15

### Local Development

```bash
# 1. Repository'yi klonla
git clone https://github.com/benimmasalim/platform.git
cd benim-masalim

# 2. Environment dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenle

# 3. Docker ile servisleri başlat
docker-compose up -d postgres redis

# 4. Backend kurulumu
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 5. Frontend kurulumu (yeni terminal)
cd frontend
npm install
npm run dev
```

## API Dokümantasyonu

Backend çalışırken:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Önemli Kurallar

1. **Dinamik Boyutlar**: Piksel değerlerini ASLA hard-code etme, `products.width_mm`'den hesapla
2. **State Machine**: Sipariş durumlarını sırayla geçir, atlamak yasak
3. **KVKK**: `DELIVERED` statüsünde 30 gün sonra fotoğraflar silinir
4. **Overlay**: Her görselde `product.has_overlay` kontrolü yap

## Lisans

Proprietary - Tüm hakları saklıdır.
