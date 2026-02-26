# BENİM MASALIM - ANTIGRAVITY KAPSAMLI ÇALIŞMA KURALLARI

Bu dosya, yazılım bilgisi olmayan proje sahibi ($YUSUF) ile Antigravity'nin (Yapay Zeka) %100 otonom, hatasız ve halüsinasyonsuz çalışmasını sağlamak için oluşturulmuştur. 

Projeyle ilgili tüm mühendislik detayları (eski Cursor kuralları) `.cursor/rules/` klasöründedir. Geliştirme yaparken bu kurallara KESİNLİKLE uyulacaktır.

## 🧭 1. Mimari ve Geliştirme Standartları (Kurallar Seti)
Antigravity, bir dosyada veya modülde değişiklik yapmadan önce ilgili kural dosyasını referans almalıdır:

- **Frontend (`.cursor/rules/frontend.mdc`):** Next.js 14 App Router, shadcn/ui, TypeScript Strict Mode kullanılacak.
- **Backend (`.cursor/rules/backend.mdc`):** FastAPI, Async SQLAlchemy, Pydantic v2. (Kodlar asenkron yazılacak `await db.execute(select(...))`).
- **Veritabanı (`.cursor/rules/database.mdc`):** PostgreSQL, UUID Primary Key, Alembic migrations. Kesinlikle hardcoded veri (örn. sabit resim boyutu) yazılamaz.
- **AI Entegrasyonları (`.cursor/rules/ai-services.mdc`):** Gemini, Imagen 3, ElevenLabs, InsightFace kullanımları ve Error tipleri (`AIServiceError`).
- **Görsel Üretim (`.cursor/rules/g-rsel-retim-kural.mdc`):** Karakter, stil ve sahne tutarlılığı. Promptlara kesinlikle child-safety ve negative bazlı standartlar uygulanacak.
- **Prompt Altyapısı (`.cursor/rules/prompt-engine.mdc`):** Legacy (eski) V2 pipeline kullanılmayacak. Tüm kodlar V3 pipeline'ı olan `app/prompt/` (BookContext, PromptComposer) üzerinden yürüyecek.
- **Sipariş Durumları (`.cursor/rules/state-machine.mdc`):** Durum geçişleri manuel (`order.status = ...`) YAPILAMAZ! Her zaman `transition_order` kullanılacak.
- **Kuyruk / Job Mimarisi (`.cursor/rules/workers.mdc`):** ARQ Workers üzerinden kuyruk yönetilecek. Limitler ve retry mekanizmaları kurala uygun eklenecek.

## 🤖 2. Otonom Asistan (Antigravity) Çalışma Şartları
Proje sahibi yazılımcı değildir. Bu nedenle kod yazılırken **AI Halüsinasyonu kesinlikle tolere edilemez.**
1. **Araştır ve Doğrula:** Değişiklik yapacağın kodu önce `grep_search` veya `view_file` ile iyice analiz et. Cursor kurallarını akılda tutarak mevcut yapıyı (V3 altyapısı, AsyncDB vs.) bozma.
2. **Düzenleme:** Her zaman `replace_file_content` veya `multi_replace_file_content` kullanarak sadece değiştireceğin veya ekleyeceğin yeri güncelle. Tüm dosyayı yeniden yazmaya kalkma.
3. **Sorun Tespiti:** Eğer backend'de (Python'da) veya frontend'de (TypeScript'te) syntax hatası yaparsan, kullanıcı sana kızmadan önce bunu terminal üzerinden test et ve kendi hatanı kendin onar.

## 🚀 3. Yayınlama (Deployment) Akışı
- Geliştirme ve testler bittiğinde kullanıcı chate sadece `/deploy` veya `/yayinla` yazar.
- Antigravity otomatik olarak `.agents/workflows/deploy.md` iş akışını tetikler ve sistemi güvenle Google Cloud'a yükler. Sunucuyla (Cloud Run, DB Proxy vb.) olan bağlantı otonom yürütülür.

## 🧹 4. Klasör ve Çalışma Alanı Yönetimi (Clean Workspace)
- Projenin kök dizinini (Root Folder) asistan olarak oluşturduğumuz geçici markdown dosyaları, loglar veya asistan ayar dosyalarıyla karmaşıklaştırmak YASAKTIR.
- Workflow (.md), Antigravity talimatları ve projeye yönelik otonom notlar gibi yardımcı tüm dosyalar `.agents/` klasörü içerisinde tutulmalıdır.
- `infra/` klasörü projenin Google Cloud (Terraform) ilk kurulum altyapısını ve yerel `docker-compose.yml` dosyasını içerir. Günlük geliştirmelerde ve deploylarda (Cloud Run vb.) KULLANILMAZ. Sadece referans amaçlıdır. Dokunmayın.
