# BENİM MASALIM - ANTIGRAVITY GENERAL RULES AND PRINCIPLES

Bu dosya "Benim Masalım" projesinin Antigravity (yapay zeka asistanın) üzerinden hatasız, güvenli ve Google Cloud canlı ortamından kopmayacak şekilde yönetilmesini sağlayan kurallar bütünüdür. 

## 🏗️ 1. Proje Mimarisi
- **Yazılım Dili:** TypeScript (Next.js - Frontend), Python 3.11+ (FastAPI - Backend)
- **Veritabanı ve Kuyruk:** PostgreSQL 15, Redis 7 (Arq)
- **Host / Deployment:** Google Cloud Platform (Cloud Run, Cloud SQL, Cloud Storage, Artifact Registry)
- **Canlı (Production) Veritabanı Tüneli:** `cloud-sql-proxy.exe` (127.0.0.1:5433)

## 🤖 2. Antigravity MCP ve Tool Yönetimi (Asistan Kuralları)
Antigravity, standart yapay zeka araçlarından (Cursor vb.) farklı olarak sisteme aracı bir *Model Context Protocol (MCP)* indirmeye gerek duymaz. Tarayıcı entegrasyonu (Browser API), Local CLI (Terminal) ve Dosya (FS) okuma/yazma sistemlerini otonom kullanır.
Özel MCP veya plugin ekosistemi kurmaya gerek yoktur, komutları asistan doğrudan PowerShell veya gcloud CLI üzerinden çalıştırır.

### Kurallar:
1. **Dosya Değişiklikleri:** Otonom çalışırken kodları satır satır grep_search ile arayıp noktasal (`multi_replace_file_content`) değişiklik yapmalısın. Dosya büyüklüğünün (Page Composer, vs.) bilincinde olarak tüm dosyayı override atmaktan kaçın.
2. **Bash ve Terminal Kullanımı:** Windows ortamındasın (PowerShell). Terminal çalıştırırken komutların Windows Powershell'e uyumlu (`.\venv\Scripts\python.exe` gibi) olduğundan her zaman emin ol.
3. **Database (Migration):**
   - Canlı ortamda işlem yaparken DB'ye bağlanan scriptlerde mutlaka `PYTHONIOENCODING="utf8"` kullan.
   - Her Alembic migration sonrasında muhakkak `cloud-sql-proxy` tünelinin çalışıp çalışmadığını verify et. Yıkıcı (DROP/DELETE) işlemleri asla kullanıcı ($YUSUF) onayı (SafeToAutoRun: false) olmadan yapma.

## 🚀 3. Otonom Geliştirme Yaşam Döngüsü (Workflow)
Sıradan bir görevi yerine getirirken her defasında şu yaşam döngüsü izlenir:
1. **İnceleme:** Problemi anlamak için backend (`app/`) veya frontend (`src/`) klasörlerine `find_by_name` veya `grep_search` atılır. 
2. **Local Test (Mock):** Eğer AI promptlarında (Promt_engine) bir değişlik yapılacaksa test scripti oluşturulup (`inspect_...py`) DB'ye yazılmadan ekrana bastırılarak validasyon yapılır.
3. **Gerçekleme:** Değişiklik uygulanır.
4. **Deploy:** `deploy_production.sh` gibi GCP scriptleri tetiklenerek kod buluta fırlatılır.

## 🎨 4. Frontend & Tasarım Felsefesi (Glassmorphism & Dopamin)
Kullanıcılar (ve ebeveynler) görsel mükemmellik bekler.
- CSS olarak **Tailwind** kullanılır ama sadece utility sınıflarıyla yetinilmez. Framer Motion ile scroll/animasyon destekleri zorunludur.
- Tasarımda zayıf, basit veya ruhsuz görünümler (düz beyaz/gri kutular) KESİNLİKLE kabul edilemez. Canlı gradients, glassmorphism (`backdrop-blur`) ve shadow derinliklerine dikkat edilmelidir.

## ⚠️ 5. Canlı Ortama Saygı
Bu proje **AKTİF SUNUCUDA** müşterilere hizmet vermektedir.
- Müşterinin (User'ın) kişisel fotoğrafları ve oluşturduğu kitap PDF'leri KVKK (GDPR) yasasına tabidir (`main.py` deki cron job'lara dokunma). GCS Bucket nesneleri izin olmadan silinmez veya fetch edilemez.
- Backend API (`8000`) kapandığı an sipariş akışı kırılır. Uygulamayı asla tam teste sokmadan deploy etmeyiz!

Bu yönergeler Antigravity tarafından referans alınacak yegane kurallardır. Her sorunda buraya döneriz.
