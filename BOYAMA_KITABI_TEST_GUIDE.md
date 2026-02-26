# Boyama Kitabı Sipariş Test Scripti

## Backend'de boyama kitabı siparişi nasıl oluşturulur:

### 1. Manuel SQL ile Test Siparişi

```sql
-- Önce aktif bir boyama kitabı ürünü olmalı
INSERT INTO products (
    name, slug, product_type, base_price, is_active, 
    type_specific_data, default_page_count, min_page_count, max_page_count
) VALUES (
    'Test Boyama Kitabı', 
    'test-boyama-kitabi',
    'coloring_book',
    199.00,
    true,
    '{"line_art_method": "canny", "edge_threshold_low": 80, "edge_threshold_high": 200}'::jsonb,
    16, 12, 32
) ON CONFLICT (slug) DO NOTHING;

-- Ardından test siparişi (mevcut bir hikaye order'ı olmalı)
-- coloring_book_order_id'yi doldurarak
UPDATE orders 
SET coloring_book_order_id = '<yeni_coloring_order_uuid>'
WHERE id = '<original_story_order_uuid>';

INSERT INTO orders (
    id, user_id, product_id, status, is_coloring_book,
    child_name, child_age, child_gender, total_pages
) VALUES (
    '<yeni_coloring_order_uuid>',
    '<user_id>',
    (SELECT id FROM products WHERE product_type='coloring_book' AND is_active=true LIMIT 1),
    'PAID',
    true,
    'Test',
    5,
    'girl',
    16
);
```

### 2. Task Tetikleme

```python
from app.tasks.generate_coloring_book import generate_coloring_book
await generate_coloring_book(order_id=coloring_order_uuid, db=db)
```

## Sipariş Akışı

```
1. Kullanıcı hikaye kitabı sipariş eder
   ↓
2. Ödeme yapar (status: PAID)
   ↓
3. Hikaye üretilir (status: READY_FOR_PRINT)
   ↓
4. [ŞU AN EKSİK] Kullanıcı "Boyama Kitabı da Ekle" butonu
   ↓
5. Backend yeni Order oluşturur (is_coloring_book=true)
   ↓
6. generate_coloring_book task tetiklenir
   ↓
7. Line-art conversion (products.type_specific_data'dan ayarlar)
   ↓
8. PDF oluşturulur (skip_text=true)
   ↓
9. Status: READY_FOR_PRINT
   ↓
10. Admin /orders panelinde görünür
```

## Admin Panelinde Görüntüleme

Boyama kitabı siparişlerini görmek için:
- **URL:** https://benimmasalim.com.tr/admin/orders
- **Filter:** `is_coloring_book = true` olan siparişler
- **Ayırt Etme:** Sipariş kartında "🎨 Boyama Kitabı" badge'i olmalı

## Eksik API Endpoint'ler

### Kullanıcı için gerekli endpoint:

```python
# POST /api/v1/orders/{order_id}/add-coloring-book
# Mevcut hikaye siparişine boyama kitabı ekler
@router.post("/{order_id}/add-coloring-book")
async def add_coloring_book_to_order(
    order_id: UUID,
    user: CurrentUser,
    db: DbSession
):
    # 1. Original order'ı kontrol et
    # 2. Boyama kitabı ürününü bul
    # 3. Yeni Order oluştur (is_coloring_book=true)
    # 4. Original order'a link et (coloring_book_order_id)
    # 5. Payment URL döndür
    pass
```

## Şu An Test Etmek İçin:

1. **Migration'ları çalıştır:**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Admin'den boyama ürünü ekle:**
   - `/admin/products` → Boyama Kitabı tab
   - Yeni ürün oluştur
   - Active = true yap

3. **Manuel test siparişi oluştur** (SQL ile yukarıdaki gibi)

4. **Task'i tetikle** (Python console ile)

5. **Admin panelinde kontrol et:** `/admin/orders`

## Sonraki Adımlar (Frontend):

- [ ] Ana sayfaya "Boyama Kitabı" bölümü ekle
- [ ] Create page'e product type selector ekle
- [ ] Order detail sayfasına "Boyama Kitabı Ekle" butonu
- [ ] `/api/v1/orders/{order_id}/add-coloring-book` endpoint'i
