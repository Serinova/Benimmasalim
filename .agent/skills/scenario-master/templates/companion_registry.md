# 🦊 Companion Kayıt Defteri

> Sistemde tanımlı tüm companion'lar ve pipeline bağlantıları.
> Yeni companion eklendiğinde bu tablo + kod sözlükleri güncellenmelidir.

---

## 📦 Kayıtlı Companion'lar

| Senaryo | Companion TR | Companion EN | Species | Appearance (EN) | `_COMPANION_MAP` | `_TR_TO_EN` |
|---------|-------------|-------------|---------|-----------------|-------------------|-------------|
| Kapadokya | Cesur Yılkı Atı | brave wild Cappadocian horse | wild horse | small brown wild Cappadocian horse with flowing dark mane | ✅ | ✅ |
| Kapadokya | Sevimli Kapadokya Tilkisi | — | — | — | ❌ EKLE | ❌ EKLE |
| Göbeklitepe | Cesur Step Tilkisi | brave steppe fox | fox | small reddish-brown steppe fox with bushy tail and bright eyes | ✅ | ✅ |
| Göbeklitepe | Sevimli Step Tavşanı | — | — | — | ❌ EKLE | ❌ EKLE |
| Efes | Antik Roma Kartalı | ancient Roman golden eagle | eagle | majestic golden eagle with sharp talons and piercing amber eyes | ✅ | ✅ |
| Efes | Efes Kedisi | — | — | — | ❌ EKLE | ❌ EKLE |
| Çatalhöyük | Köpek | small friendly dog | dog | small friendly brown and white dog with floppy ears | ✅ | ✅ |
| Sümela | Cesur Dağ Kartalı | brave mountain eagle | eagle | brave dark brown mountain eagle with wide wingspan | ✅ | ✅ |
| Sultanahmet | Minik Beyaz Güvercin | small white dove | dove | small pure white dove with gentle dark eyes | ✅ | ✅ |
| Kudüs | Güvercin Beyazı | small white dove | dove | small pure white dove with gentle dark eyes | ✅ | ✅ |
| Kudüs | Sevimli Zeytin Dalı Serçesi | — | — | — | ❌ EKLE | ❌ EKLE |
| Amazon | Renkli Papağan | colorful macaw parrot | macaw parrot | colorful scarlet macaw parrot with bright red, blue and yellow feathers | ✅ | ✅ |
| Uzay | Gümüş Robot Nova | small silver robot | robot | small silver robot companion with glowing blue LED eyes and smooth rounded body | ✅ | ✅ |
| Oyuncak Dünyası | Pelüş Ayıcık | fluffy teddy bear plushie | teddy bear plushie | soft fluffy brown teddy bear plushie with a red bow tie | ✅ | ✅ |
| Masal Dünyası | Parıltılı Mini Ejderha | tiny sparkling dragon | tiny dragon | tiny sparkling purple dragon with iridescent wings and golden eyes | ✅ | ✅ |
| Masal Dünyası | Konuşan Masal Baykuşu | — | — | — | ❌ EKLE | ❌ EKLE |

---

## ⚠️ Eksik Companion'lar (Aksiyon Gerekli)

Aşağıdaki companion'lar `custom_inputs_schema`'da option olarak var ama
`_COMPANION_MAP` ve `_TR_TO_EN` sözlüklerinde tanımlı DEĞİL:

| TR | Önerilen EN Species | Önerilen Appearance |
|----|---------------------|---------------------|
| Sevimli Kapadokya Tilkisi | fox | small reddish-orange Cappadocian fox with fluffy tail and bright green eyes |
| Sevimli Step Tavşanı | rabbit | small sandy-brown steppe rabbit with long ears and white cotton tail |
| Efes Kedisi | cat | sleek gray and white Ephesus street cat with amber eyes |
| Sevimli Zeytin Dalı Serçesi | sparrow | tiny olive-brown sparrow with a small olive branch in its beak |
| Konuşan Masal Baykuşu | owl | wise small purple owl with golden spectacles and starry feather tips |

---

## 🔧 Yeni Companion Ekleme Adımları

1. Bu tabloya ekle
2. `backend/app/services/ai/_story_blueprint.py` → `_TR_TO_EN` sözlüğüne ekle
3. `backend/app/tasks/generate_book.py` → `_COMPANION_MAP` sözlüğüne ekle
4. Migration ile `custom_inputs_schema` güncelle (gerekiyorsa)
5. Test çalıştır: `python -m pytest tests/test_companion_consistency.py -v`

---

## 📊 Companion'sız Senaryolar

Bu senaryolarda `custom_inputs_schema`'da `animal_friend` yok — companion kullanılmıyor:

| Senaryo | theme_key | Companion Durumu |
|---------|-----------|-----------------|
| Galata | galata | YOK — solo macera |
| Dinozor | dinosaur | YOK — hikayeden organik |
| Umre | umre_pilgrimage | YOK — aile/kafile |
| Okyanus | ocean | YOK — hikayeden organik |
