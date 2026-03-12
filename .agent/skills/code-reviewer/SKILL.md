---
name: Code Reviewer
description: >
  Kod kalitesi kontrolü, anti-pattern tespiti ve sistematik review için ZORUNLU beceri.
  "kontrol et", "review", "kod kalitesi", "bu doğru mu" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🧹 Code Reviewer Skill

Kod değişikliklerini sistematik şekilde gözden geçirme rehberi.

## ⚡ Tetikleyiciler

- "Bu kodu kontrol et", "review yap", "bu doğru mu?"
- "Kod kalitesi", "refactor gerekli mi?"
- Büyük PR/değişiklik sonrası

---

## 📋 Review Checklist

### Python (Backend) Kontrol Listesi

| # | Kontrol | Önem |
|---|---------|------|
| 1 | Tüm fonksiyonlar `async` mi? (FastAPI zorunluluğu) | 🔴 Kritik |
| 2 | `await` eksik olan DB çağrısı var mı? | 🔴 Kritik |
| 3 | Error handling: try/except ile uygun hata yakalama | 🟡 Önemli |
| 4 | Structlog ile loglama (`logger.info/warning/error`) | 🟡 Önemli |
| 5 | Type hints tanımlı mı? (`-> ReturnType`, `param: Type`) | 🟢 İyi pratik |
| 6 | Import sıralaması doğru mu? (stdlib → 3rd party → local) | 🟢 İyi pratik |
| 7 | Magic number/string sabit'e çıkarılmış mı? | 🟢 İyi pratik |
| 8 | `settings.xxx` ile config alınıyor mu? (hard-code yok) | 🔴 Kritik |
| 9 | Transaction'lar düzgün kullanılıyor mu? | 🟡 Önemli |
| 10 | Memory cleanup (PIL Image.close(), gc.collect()) | 🟡 Önemli |

### TypeScript/TSX (Frontend) Kontrol Listesi

| # | Kontrol | Önem |
|---|---------|------|
| 1 | `any` type kullanılmamış mı? | 🟡 Önemli |
| 2 | Type assertion (`as`) yerine type guard kullanılıyor mu? | 🟢 İyi pratik |
| 3 | `useEffect` cleanup fonksiyonu var mı? (memory leak engeli) | 🟡 Önemli |
| 4 | Component'ler `'use client'` / `'use server'` doğru mu? | 🔴 Kritik |
| 5 | `key` prop unique mi? (list rendering) | 🟡 Önemli |
| 6 | Error boundary / loading state var mı? | 🟡 Önemli |
| 7 | Accessibility: `aria-label`, semantic HTML | 🟢 İyi pratik |
| 8 | Responsive tasarım: mobile-first? | 🟡 Önemli |
| 9 | Unused import/variable temizlenmiş mi? | 🟢 İyi pratik |
| 10 | Console.log temizlenmiş mi? | 🟡 Önemli |

---

## 🔍 Otomatik Kontrol Komutları

```powershell
# Backend — lint + type check
cd backend
python -m ruff check app/ --select=E,W,F,I
python -m mypy app/ --ignore-missing-imports

# Frontend — tam kontrol
cd frontend
npm run type-check       # TypeScript kontrolü
npm run lint             # ESLint
npm run format:check     # Prettier

# Kullanılmayan import kontrolü
cd backend
python -m ruff check app/ --select=F401    # unused imports
```

---

## 🚫 Yaygın Anti-Pattern'ler

### Python

```python
# ❌ YANLIŞ: Synchronous DB çağrısı
result = db.query(Order).filter_by(id=order_id).first()

# ✅ DOĞRU: Async DB çağrısı
result = await db.execute(select(Order).filter_by(id=order_id))
order = result.scalar_one_or_none()
```

```python
# ❌ YANLIŞ: Bare except
try:
    ...
except:
    pass

# ✅ DOĞRU: Spesifik exception
try:
    ...
except ValueError as e:
    logger.warning("Validation failed", error=str(e))
```

```python
# ❌ YANLIŞ: print() kullanımı
print(f"Order created: {order_id}")

# ✅ DOĞRU: structlog kullanımı
logger.info("Order created", order_id=str(order_id))
```

### TypeScript

```tsx
// ❌ YANLIŞ: any type
const data: any = await fetchOrder();

// ✅ DOĞRU: Interface tanımla
interface OrderData {
  id: string;
  childName: string;
  status: OrderStatus;
}
const data: OrderData = await fetchOrder();
```

```tsx
// ❌ YANLIŞ: useEffect bağımlılık eksik
useEffect(() => {
  fetchData(orderId);
}, []); // orderId eksik!

// ✅ DOĞRU
useEffect(() => {
  fetchData(orderId);
}, [orderId]);
```

---

## 📊 Review Raporu Formatı

```markdown
## 🔍 Kod Review Raporu

**Dosya(lar):** [dosya listesi]
**Toplam Sorun:** X (🔴 Y kritik, 🟡 Z önemli, 🟢 W iyileştirme)

### Kritik Sorunlar (🔴)
1. [dosya.py:42] — `await` eksik DB çağrısı
2. ...

### Önemli Sorunlar (🟡)
1. [component.tsx:15] — `any` type kullanımı
2. ...

### İyileştirme Önerileri (🟢)
1. [service.py:88] — Magic number sabit'e çıkarılabilir
2. ...
```
