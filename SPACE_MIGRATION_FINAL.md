# GUNES SISTEMI MACERASI - MODULAR PROMPT UPDATE

## OZET
- Cover: 339 char ✓
- Page: 418 char ✓
- Story: ~2500 char (blueprint + dopamin) ✓

## PROMPT DETAYLARI

### Cover Prompt (339 char):
```
Epic space scene: {scene_description}. 
Modular space station orbiting Earth. 
Friendly AI robot companion beside child. 
8 planets visible: Mercury (small), Venus (cloudy), Mars (red), Jupiter (MASSIVE, Great Red Spot), Saturn (rings), Uranus, Neptune (distant blue). 
Child TINY in vast cosmos. 
Starfield, nebula hints. 
Adventure atmosphere.
```

### Page Prompt (418 char):
```
Space scene: {scene_description}. 
AI robot companion (friendly guide). 
Planets: [Mercury: cratered, extreme heat / Venus: thick clouds, volcanic / Moon: gray cratered / Mars: red surface, rovers / Jupiter: MASSIVE (1300 Earths), Great Red Spot, child TINY / Saturn: iconic rings (ice) / Uranus: ice giant, tilted / Neptune: distant blue]. 
Spacecraft, space station. 
Deep space black, stars. 
Child TINY, cosmos VAST.
```

### Story Prompt (blueprint):
- 8 Gezegen progression (Merkur→Neptün)
- 4 Endişe→Başarı döngüsü
- 6 Epic moment
- Dopamin merdiveni tasarımı
- Robot {robot_name} arkadaşlık

## SQL MIGRATION

Space senaryosunu veritabanında güncellemek için:

```sql
-- GCP Cloud SQL Query Editor'de çalıştır

UPDATE scenarios
SET 
  cover_prompt_template = 'Epic space scene: {scene_description}. 
Modular space station orbiting Earth. 
Friendly AI robot companion beside child. 
8 planets visible: Mercury (small), Venus (cloudy), Mars (red), Jupiter (MASSIVE, Great Red Spot), Saturn (rings), Uranus, Neptune (distant blue). 
Child TINY in vast cosmos. 
Starfield, nebula hints. 
Adventure atmosphere.',
  
  page_prompt_template = 'Space scene: {scene_description}. 
AI robot companion (friendly guide). 
Planets: [Mercury: cratered, extreme heat / Venus: thick clouds, volcanic / Moon: gray cratered / Mars: red surface, rovers / Jupiter: MASSIVE (1300 Earths), Great Red Spot, child TINY / Saturn: iconic rings (ice) / Uranus: ice giant, tilted / Neptune: distant blue]. 
Spacecraft, space station. 
Deep space black, stars. 
Child TINY, cosmos VAST.',
  
  updated_at = NOW()
WHERE theme_key = 'solar_systems_space' 
   OR name ILIKE '%Güneş Sistemi%'
   OR name ILIKE '%Uzay%';
```

## TEST PLANI

1. Migration çalıştır
2. Frontend'den yeni kitap oluştur:
   - Çocuk: Ayşe, 7 yaş
   - Robot: NOVA
   - Favori: Jupiter
3. Sayfa 13-15 kontrol (Jupiter doruk):
   - "DEVASA", "1300 Dünya" kelimeleri var mı?
   - Kırmızı Leke bahsediliyor mu?
   - Scale (çocuk TINY) vurgulanıyor mu?

## TAMAMLANDI

✅ Cover prompt modular (339 char)
✅ Page prompt modular (418 char)
✅ Story blueprint hazır
✅ SQL migration hazır

Kullanıcı migrationı çalıştırınca test edebilir!
