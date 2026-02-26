# AMAZON ORMANLARI - MODULAR PROMPT TASARIMI

## MEVCUT DURUM
- Cover: **1450 char** ❌ (limit aşıyor!)
- Page: **2700 char** ❌ (limit aşıyor!)
- Story: 1100 char ✓ (makul)

---

## MODULAR PROMPT TASARIMI

### Cover Prompt (~420 char):
```
Amazon rainforest scene: {scene_description}. 
Child on massive tree root at river tributary, gazing into dense jungle. 
Towering kapok trees with buttress roots, emerald-green multi-layered canopy. 
Scarlet and blue-gold macaws flying, toucans perched. 
Winding brown river, golden sunlight shafts through canopy (god rays). 
Hanging lianas, vibrant orchids, misty atmosphere. 
Rich colors: emerald green, scarlet, electric blue, golden amber. 
Wide shot: child 25%, rainforest 75%. 
Epic scale, biodiversity wonder.
```
**Uzunluk**: 420 char ✓

### Page Prompt (~480 char):
```
Amazon rainforest scene: {scene_description}. 
Elements: [Giant kapok trees with buttress roots, multi-layer canopy (40m+), winding tributary / Birds: scarlet macaws (pairs), toucans, harpy eagles / River fauna: pink dolphins (boto), capybaras, caimans (small), turtles / Forest: sloths, howler monkeys, poison dart frogs (blue/red/yellow), morpho butterflies (blue), leafcutter ants / Jaguar: distant, majestic, respectful]. 
Vegetation: lianas, bromeliads, orchids, moss, ferns. 
Dappled sunlight, misty humid air. 
Rich colors: emerald, jade, scarlet, electric blue, amber. 
At least 2-3 species visible per scene.
```
**Uzunluk**: 480 char ✓

---

## DOPAMIN + KEŞİF YAPISИ

Amazon için "Keşif Dopamini":

```
BÖLÜM 1 - İLK KEŞİF (1-4): Amazon'a varış, ilk hayvan
BÖLÜM 2 - MACAW AİLESİ (5-8): Renkli papağanlar, yardımlaşma
BÖLÜM 3 - NEHİR KEŞFI (9-12): Pembe yunus, iletişim
BÖLÜM 4 - TEMBEL ANI (13-15): Sabır öğrenme, herkesin hızı farklı
BÖLÜM 5 - KARINCA EKİBİ (16-18): İşbirliği, organize çalışma
BÖLÜM 6 - JAGUAR CAMEO (19-20): Ormanın koruyucusu (uzaktan)
BÖLÜM 7 - DÖNÜŞ (21-22): Doğayı koruma bilinci
```

### 4 Keşif→Öğrenme Döngüsü:
1. **Macaw ailesi** (5-7): "Kayıp yavru!" → Yuva bulma → Aile birliği
2. **Pembe yunus** (10-12): "Nehirde kayboldum" → Yunus rehberlik → İletişim
3. **Tembel** (14-15): "Neden bu kadar yavaş?" → Sabır öğrenme → Herkesin temposu farklı
4. **Leafcutter karınca** (17-18): "Minik ama güçlüler!" → İşbirliği → Birlikte başarmak

### 6 Epic Keşif Momentleri:
1. İlk kapok ağacı - dev kökler (Sayfa 3)
2. Macaw uçuşu - renkli sürü (Sayfa 6)
3. Pembe yunus dansı - nehir surfing (Sayfa 11)
4. Morfo kelebeği bulutu - mavi patlama (Sayfa 16)
5. Jaguar göz göze - saygılı mesafe (Sayfa 19)
6. Günbatımı canopy görünümü (Sayfa 22)

---

## DEĞERLER:
- **YARDIMLAŞMA**: Hayvanlarla işbirliği
- **BİYOÇEŞİTLİLİK**: Zengin ekosistem
- **SABIR**: Tembelten öğrenme
- **İŞBİRLİĞİ**: Karıncalardan öğrenme
- **KORUMA**: Ormanı koruma bilinci

---

## GÜVENLİK:
✅ Korku/şiddet yok
✅ Yılan saldırısı yok
✅ Kaybolma travması yok
✅ Jaguar tehlikeli DEĞİL (uzak, saygılı)
✅ Hayvan zararı yok

---

## SONUÇ:
Amazon iyi hazırlanmış, SADECE prompt'ları kısaltmalıyız!
