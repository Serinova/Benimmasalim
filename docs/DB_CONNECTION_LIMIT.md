# PostgreSQL Bağlantı Limiti (TooManyConnectionsError)

## Limiti kim koyuyor?

- **PostgreSQL sunucusu**: `max_connections` parametresi (`postgresql.conf`). Varsayılan genelde **100**.
- **Google Cloud SQL**: Instance ayarlarında yönetilir; küçük instance’larda bu limit daha düşük olabilir.
- PostgreSQL, replication ve **superuser** için bir miktar slot ayırır. Kalan slotlar dolunca normal kullanıcılar şu hatayı alır:
  `remaining connection slots are reserved for non-replication superuser connections`

Yani limiti koyan **veritabanı sunucusunun konfigürasyonu** (kendi PostgreSQL’iniz veya Cloud SQL).

## Ne yapmalı?

1. **Diğer bağlantıları azaltın**
   - Backend uygulamasını durdurun.
   - Açık IDE/DB istemcilerini (DBeaver, pgAdmin, vs.) kapatın.
   - Worker / arka plan işleri aynı DB’ye bağlıysa onları da geçici durdurun.

2. **Migration’ı tekrar çalıştırın**
   ```powershell
   cd backend
   alembic upgrade head
   ```

3. **Cloud SQL kullanıyorsanız**
   - [Cloud SQL Console](https://console.cloud.google.com/sql) → Instance → Configuration.
   - Bazı planlarda `max_connections` artırılabilir (veya instance büyütülür).

4. **Lokal PostgreSQL ise**
   - `postgresql.conf` içinde `max_connections` değerini artırıp servisi yeniden başlatın.
