# Gemini / Fal Rollback – Özet ve Dikkat Edilecekler

Bu dosya `cursor_project_plan_execution.md` chat'indeki işler ve dosyaları geri aldıktan sonra dikkat etmeniz gereken noktaları toplar.

---

## Chat'te Yapılanlar (Kısa)

1. **Gemini entegrasyonu:** Fal ile aynı imzada `GeminiConsistentImageService`, dispatcher, Admin’de Fal/Gemini seçimi.
2. **Prompt tarafı:** Önce Gemini’ye özel talimatlar (GEMINI_VISUAL_INSTRUCTION, kapak/iç sayfa ayrımı, referans vurgusu) eklendi; sonra “resimler kötüleşti” denilerek **Gemini = Fal’ın prompt’unu kullan** kararı alındı.
3. **Fal tarafı:** `LIKENESS_HINT_WHEN_REFERENCE` uzatıldı, Fal bozuldu; sonra **kısa orijinal metne** geri alındı.
4. **Diğer:** id_weight sadece stilde, test ekranında full prompt + Fal params, max_sequence_length 512, start_step 2, hikaye aile yasağı, Canlı Anime stilleri, lint/Prettier, placeholder 404, story timeout.

---

## Geri Aldığınızda Kontrol Listesi

### 1. `backend/app/prompt_engine/constants.py`

- **LIKENESS_HINT_WHEN_REFERENCE** – Şu an **kısa** (Fal’ın iyi çalıştığı hali):
  - `"Same face and hair every page as reference. Art style only on line, shading, background."`
- Uzun “same face, same hair color and style, same skin tone…” metni **olmamalı**; varsa Fal çıktısı yine bozulabilir.

### 2. `backend/app/services/ai/gemini_consistent_image.py`

- **Mevcut durum:** Gemini’ye hâlâ ekstra talimat gidiyor:
  - “Generate a single children's book illustration. Use the reference image... full bleed... Do not add border... **Scene description:** ” + full_prompt
- **Chat’teki son karar:** “Prompt yönetimini Fal’a ver; Gemini sadece Fal’ın full_prompt + negative’i ile resim üretsin.”
- Yani tam rollback istiyorsanız: Gemini’ye giden metni **sadece** `full_prompt + ". Avoid in the image: " + full_negative` yapın; baştaki “Generate a single… Scene description: ” blokunu kaldırın.

### 3. Veritabanı (migration’lar)

- Chat’te **029_seed_gemini_visual_instruction** ve **030_seed_gemini_visual_instruction_inner** geçiyor; bu workspace’te bu migration dosyaları **yok** (revert edilmiş veya hiç eklenmemiş).
- Eğer başka bir ortamda bu migration’ları çalıştırdıysanız, DB’de `GEMINI_VISUAL_INSTRUCTION` / `GEMINI_VISUAL_INSTRUCTION_INNER` kayıtları olabilir. Kodda bu key’lere referans **yok**; yani şu an kullanılmıyor, sadece tabloda kalıntı olabilir.

### 4. Hikaye / aile kuralları (chat’ten kalanlar)

- **STORY_NO_FIRST_DEGREE_FAMILY_TR** ve **NO_FAMILY_BANNED_WORDS_TR** constants’ta duruyor; hikayede 1. derece aile yasağı ve ihlal kontrolü chat’te eklenmişti.
- Bunları **tutmak** istiyorsanız değişiklik yok. Tamamen eski haline döndürmek isterseniz story prompt ve `gemini_service` içindeki aile ihlal kontrolünü kaldırmanız gerekir.

### 5. Admin prompt kartları (Fal.ai / Gemini badge)

- Chat’te COVER/INNER ve GEMINI_VISUAL_* kartlarına “Fal.ai” / “Gemini” badge’leri eklenmişti. Kodda `GEMINI_VISUAL_INSTRUCTION` kullanımı yok; badge’ler sadece etiket.
- Frontend’i tam revert ettiyseniz bu badge’ler de gitmiş olabilir; kalması zararsız.

### 6. Diğer dosyalar (chat’e göre “değiştirme” denmişti)

- **compliance.py**, **fal_request_builder.py**, **negative_prompt_builder.py** – Chat’te sadece inceleme yapıldı, LIKENESS düzeltmesi constants’ta yapıldı. Bu üç dosyada ekstra değişiklik beklenmez; özellikle Fal prompt’unu **bu dosyalarda** kısaltmayın.

---

## Özet Tablo

| Konu | Şu an (kontrol edin) | Öneri |
|------|----------------------|--------|
| LIKENESS_HINT (constants) | Kısa metin | Uzun metin varsa kısaya dönün (Fal için). |
| Gemini’ye giden metin | Ekstra talimat + “Scene description: ” + full_prompt | Tam Fal uyumu için sadece full_prompt + negative kullanın. |
| DB GEMINI_VISUAL_* | Migration 029/030 bu repoda yok | Başka ortamda migration çalıştıysanız kayıtlar kalabilir; kod kullanmıyor. |
| Hikaye aile yasağı | constants + gemini_service’te var | Tutmak istiyorsanız bırakın; tam eski hal için kaldırın. |
| Fal / Gemini badge (admin) | İsteğe bağlı | İsterseniz bırakın, rollback’te kaldırılmış olabilir. |

---

## Sonuç

- **Fal’ın iyi çalışması:** `LIKENESS_HINT_WHEN_REFERENCE` kısa olmalı (şu an öyle).
- **Gemini’nin Fal ile aynı prompt’u kullanması:** `gemini_consistent_image.py` içinde Gemini’ye giden metni yalnızca **Fal’dan gelen full_prompt + negative** yapın; ek “Generate a single… Scene description: ” bloğunu kaldırın.
- Geri aldığınız dosyalar dışında: DB migration kalıntıları ve hikaye aile kurallarının tutulup tutulmayacağına karar vermeniz yeterli.
