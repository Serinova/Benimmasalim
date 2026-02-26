# "Benim Masalım" Proje Mimarisi ve Teknoloji Yığını

## 1. Genel Bakış
"Benim Masalım", kullanıcılara özelleştirilmiş çocuk masalları ve boyama kitapları üreten, yapay zeka destekli bir e-ticaret platformudur. Proje, frontend tarafında modern React (Next.js) çerçevesiyle, backend tarafında ise asenkron Python (FastAPI) altyapısıyla çalışmaktadır.

## 2. Teknoloji Yığını (Tech Stack)

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Dil:** TypeScript (Strict Mode)
- **Stil & UI:** TailwindCSS, shadcn/ui bileşenleri
- **State Yönetimi:** Zustand ve React Query
- **Özellikler:** Duyarlı tasarım (Responsive), Rich Aesthetics (göz alıcı renk paletleri, pürüzsüz animasyonlar ve çocuk dostu UI).

### Backend
- **Framework:** FastAPI
- **Dil:** Python (Asynchronous I/O)
- **Veri Doğrulama:** Pydantic v2
- **Veritabanı ORM:** SQLAlchemy (Asenkron - asyncpg)
- **Veritabanı Migration:** Alembic

### Veritabanı
- **Tip:** PostgreSQL
- **Barındırma:** Google Cloud SQL
- **Mimari:** Güvenli, ölçeklenebilir yapı, birincil anahtarlar her zaman UUID olarak tasarlanmıştır.

### Arka Plan İşlemleri (Workers & Queues)
- **Kuyruk Yöneticisi:** ARQ (Redis tabanlı asenkron görev kuyruğu)
- **Kullanım Amacı:** Metin üretimi, görsel oluşturma (Imagen 3), PDF derleme işlemleri ve uzun süren yapay zeka görevlerinin asenkron işlenmesi.

## 3. DevOps & Dağıtım (Deployment)
- **Bulut Platformu:** Google Cloud Platform (GCP)
- **Containerization:** Docker & Google Cloud Run
- **İş Akışı (CI/CD):** `.agent/workflows/deploy.md` üzerinden Antigravity ile otonom olarak veya özel bash scriptler ile yönetilir. Cloud SQL proxy ile güvenli veritabanı bağlantısı kurulur.
