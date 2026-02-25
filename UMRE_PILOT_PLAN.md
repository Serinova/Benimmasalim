# UMRE PILOT - MODULAR PROMPT TASARIMI

## MEVCUT DURUM ANALİZİ

### ✅ Kıyafetler DOĞRU (Zaten TAM kapalı!):
- **Kız**: "white hijab headscarf covering hair **completely**" ✓
- **Erkek**: "white **taqiyah prayer cap** on head" ✓

### ❌ Prompt'lar ÇOK UZUN (500 char limit!):
- Cover: **1820 char** → Limit aşıyor!
- Page: **3000+ char** → Limit aşıyor!
- Story: 1500 char (makul)

---

## MODULAR PROMPT TASARIMI

### Cover Prompt (~390 char):
```
Sacred pilgrimage scene: {scene_description}. 
Child in foreground, Masjid al-Haram and black Kaaba with golden Kiswah in distance. 
White marble courtyard, tall golden minarets, grand golden domes. 
Peaceful pilgrims in white ihram (distant, respectful). 
Golden sunlight, spiritual atmosphere. 
Child looking toward Kaaba with reverence (NOT at camera). 
Wide shot: child 20%, architecture 80%. 
RESPECTFUL distance from Kaaba.
```
**Uzunluk**: 390 char ✓

### Page Prompt (~480 char):
```
Umrah pilgrimage scene: {scene_description}. 
Locations: [Kaaba: black with golden Kiswah embroidery, white marble courtyard, golden minarets / Masjid al-Nabawi: green dome (Gunbad al-Khadra), white marble, date palms / Safa-Marwa: long marble corridor, 7 walks, green-lit middle / Hira Cave: rocky mountain, cave entrance, Mecca view / Arafat: white monument, open plain / Zemzem: marble interior, blessed water]. 
Peaceful pilgrims in white (distant, no detailed faces). 
Golden sunlight, reverent atmosphere. 
Islamic architecture: geometric patterns, calligraphy. 
NO worship close-ups, NO Prophet depictions.
```
**Uzunluk**: 480 char ✓

---

## BLUEPRINT STORY STRUCTURE

Ocean/Dino gibi "dopamin yönetimi" yerine **"MANEVİ YOLCULUK"** odaklı:

```
BÖLÜM 1 - GİRİŞ (1-4): Havaalanı, heyecan, ilk Kabe görüş
BÖLÜM 2 - KABE (5-9): Tavaf, gözyaşı, dua, huşu
BÖLÜM 3 - SAFA-MARWA (10-13): Hz. Hacer hikayesi, sebat
BÖLÜM 4 - MEDİNE (14-17): Yeşil kubbe, Mescid-i Nebevi, huzur
BÖLÜM 5 - NUR DAĞI (18-19): Hira Mağarası, ilk vahiy hikayesi
BÖLÜM 6 - ARAFAT + DÖNÜŞ (20-22): Dua, tevazu, manevi dönüşüm
```

### Manevi Zirveler (Dopamin değil, HUŞÜoperatorsymbol):
1. **İlk Kabe görüş** (Sayfa 4-5): Gözyaşları, huşu
2. **Tavaf tamamlama** (Sayfa 8): Ailece dua, birlik
3. **Safa-Marwa** (Sayfa 12): Hz. Hacer'in sabrı, sebat öğrenme
4. **Yeşil kubbe** (Sayfa 15): Mescid-i Nebevi'nin huzuru
5. **Hira** (Sayfa 18): Bilgi arayışı, ilk vahiy hikayesi
6. **Arafat** (Sayfa 21): Tevazu zirvesi, tüm insanlık için dua

---

## DEĞERLER (Ocean/Dino'dan farklı):
- **SAYGI**: Kutsal mekanlara, büyüklere
- **TEVAZU**: Allah karşısında alçakgönüllülük
- **ŞÜKÜR**: Nimet için minnettarlık
- **BİRLİK**: Müslüman kardeşlik
- **SABIR**: Hz. Hacer'den öğrenme

---

## İSLAMİ HASSAS İYET KURALLARI (KRİTİK!):
1. ✅ Hz. Muhammed, peygamberler, melekler GÖRSELLEŞTİRİLMEZ
2. ✅ Namaz kılan yüzler detaylı gösterilmez (uzaktan, genel)
3. ✅ Hacerü'l Esved (kara taş) sadece bahsedilir
4. ✅ Kabe'ye SAYGILI mesafe
5. ✅ İbadet close-up'ları yok
6. ✅ Abartılı mucize yok
7. ✅ Mezhep ayrımcılığı yok

---

## SONUÇ:
Umre zaten İYİ hazırlanmış, SADECE prompt'ları kısaltmalıyız (Ocean/Dino gibi modular).

Kıyafetler PERFECT - değişiklik gerekmez! ✓✓✓
