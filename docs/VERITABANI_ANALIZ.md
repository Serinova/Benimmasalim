# Veritabanı Analizi – Tek Kaynak, Karmaşıklık Yok

## Kaç tane veritabanı var?

**Mantıksal:** Projede tek bir uygulama veritabanı var: **benimmasalim** (database adı).

**Fiziksel (nerede çalışıyor):**

| Nerede çalışıyor? | DATABASE_URL kullanılan yer | Bağlandığı yer |
|-------------------|-----------------------------|----------------|
| **Docker backend** (docker compose) | `postgres:5432` (docker-compose'ta sabit) | Docker içindeki Postgres container (**postgres_data** volume) |
| **Bilgisayardan** (alembic, script, veya `py -m uvicorn`) | `.env` → `localhost:5432` | Host'taki 5432 portu → Genelde **aynı** Docker Postgres (port map) |

Özet:  
- Backend’i **Docker** ile çalıştırıyorsan → her zaman **Docker Postgres** (postgres_data).  
- Script / alembic’i **bilgisayardan** çalıştırıyorsan → `localhost:5432` kullanılıyor; Docker çalışıyorsa bu da **Docker Postgres**’e gider (5432 host’a map’li).  
- Bilgisayarda **ayrıca** PostgreSQL kuruluysa ve o da 5432 kullanıyorsa → port çakışması veya yanlış instance’a bağlanma riski var; o zaman gerçekten **iki farklı** veritabanı gibi davranır.

## Neden “yeni veritabanına geçtik” hissi oluştu?

- Veritabanını **değiştiren** bir kod/komut yazmadık.  
- Yapılanlar:  
  - FAL için **.env**’e `FAL_API_KEY` eklendi (sadece env).  
  - Container’lar **yeniden oluşturuldu** (`docker rm` + `docker compose up`); **volume silinmedi**, veri aynı kaldı.  
  - Admin girişi: Docker backend **hep** `postgres:5432` (Docker Postgres) kullanıyor; admin bazen host’tan script ile **localhost:5432**’de oluşturulduğu için, eğer localhost farklı bir Postgres’e gidiyorsa (veya ilk kez Docker DB’de admin yoktu) giriş “çalışmıyor” gibi göründü.  
Yani “yeni veritabanı” değil, **aynı projede iki farklı bağlantı hedefi** (Docker vs localhost) karıştı.

## Tek veritabanı stratejisi (önerilen)

1. **Tek PostgreSQL = Docker Postgres**  
   - Tüm geliştirme için sadece `docker compose` ile açtığın Postgres kullanılsın.  
   - Veri: `postgres_data` volume; container silinse bile veri durur (volume silinmedikçe).

2. **Backend her zaman aynı DB’ye bağlansın**  
   - Docker ile çalıştırıyorsan: docker-compose’taki `DATABASE_URL=...@postgres:5432/...` zaten bunu sağlıyor.  
   - Bilgisayardan script/alembic çalıştırıyorsan: `DATABASE_URL=...@localhost:5432/...` kullan; Docker çalışırken bu, map’lenen port üzerinden **aynı** Docker Postgres’e gider.

3. **Admin / migration hep aynı DB’de**  
   - Migration: `docker exec benimmasalim-backend python -m alembic upgrade head` → Docker Postgres.  
   - Admin oluşturma: `docker exec benimmasalim-backend python -m scripts.create_admin_user` → Docker Postgres.  
   Böylece giriş ve veri hep aynı instance’da kalır.

4. **Bilgisayarda ayrı PostgreSQL varsa**  
   - Ya sadece Docker Postgres kullan (önerilen), ya da Docker’daki postgres portunu değiştir (örn. 5433) ve .env’deki `localhost:5432`’yi sadece o tek instance için kullan.

## Özet tablo

| Ne yapıyorsun? | Hangi DB? | Komut / ayar |
|----------------|-----------|--------------|
| Backend (Docker) | Docker Postgres | docker-compose → `postgres:5432` |
| Alembic (migration) | Aynı DB | `docker exec benimmasalim-backend python -m alembic upgrade head` |
| Admin oluşturma | Aynı DB | `docker exec benimmasalim-backend python -m scripts.create_admin_user` |
| Backend’i bilgisayardan çalıştırma | localhost:5432 (Docker map) | Kök veya backend `.env` → `localhost:5432` |

Bu stratejiyle **tek veritabanı** kullanılır ve “yine yeni veritabanına geçtik” karmaşası olmaz.
