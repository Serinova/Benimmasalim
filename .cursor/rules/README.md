# Cursor Kuralları – Proje Uyumluluk Özeti

Bu klasördeki kurallar proje kod tabanı ile **26.02.2026** itibarıyla karşılaştırıldı ve güncellendi.

## Kural Dosyaları

| Dosya | Açıklama | Uyum |
|-------|----------|------|
| **state-machine.mdc** | Sipariş durum geçişleri, `transition_order`, KVKK, audit log | ✅ Uyumlu. `generate_coloring_book` artık `transition_order` kullanıyor. PROCESSING → CANCELLED eklendi. |
| **backend.mdc** | FastAPI, async SQLAlchemy, Pydantic v2, `/api/v1/` | ✅ Uyumlu. |
| **frontend.mdc** | Next.js 14 App Router, shadcn/ui, TypeScript, Zustand | ✅ Uyumlu. API için hem fetch hem useQuery kabul edilecek şekilde güncellendi. |
| **database.mdc** | UUID PK, timestamp, enum, migration | ✅ Uyumlu. |
| **ai-services.mdc** | Gemini, Imagen, ElevenLabs, InsightFace, `get_image_generator` | ✅ Uyumlu. `backend/app/services/ai/` yapısı mevcut. |
| **g-rsel-retim-kural.mdc** | Görsel tutarlılık, karakter/stil/sahne, çocuk güvenliği | ✅ Genel politika; prompt/pipeline ile uyumlu. |
| **prompt-engine.mdc** | `app/prompt/` (BookContext, PromptComposer) vs legacy `prompt_engine/` | ✅ Uyumlu. V3 pipeline kullanılıyor. |
| **workers.mdc** | ARQ, `benimmasalim:image_gen`, enqueue pattern | ✅ Uyumlu. |

## Yapılan Düzeltmeler

1. **state-machine:** `PROCESSING → CANCELLED` geçişi eklendi (başarısız üretim için). `backend/app/tasks/generate_coloring_book.py` artık doğrudan `order.status` ataması yapmıyor; tüm geçişler `transition_order` ile yapılıyor.
2. **state-machine glob:** `backend/app/tasks/*.py` eklendi.
3. **frontend:** API çağrıları bölümü, projede hem `fetch` hem `useQuery` kullanıldığını yansıtacak şekilde güncellendi.

## Kullanım

- `alwaysApply: true` olanlar: **state-machine**, **g-rsel-retim-kural** (her zaman dikkate alınır).
- Diğerleri: ilgili `globs` ile eşleşen dosyalarda özellikle uygulanır.
