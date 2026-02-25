# Kapak ve 1. Sayfa Metni Analizi

## Hikaye yazma sistemi (kısa)

- **Pass 1 (Pure Author):** `compose_story_prompt` → senaryo + sayfa sayısı + dramatik yay. Çıktı: düz metin hikaye (sayfa 1 = giriş, sayfa N = kapanış). Kapak için ayrı metin talep edilmiyor.
- **Pass 2 (Technical Director):** Ham hikayeyi alır; sayfalara böler + `scene_description` üretir. Talimat: "Kapak (page 0) text = sadece kitap başlığı" (kural 8). Buna rağmen LLM bazen kapak için hikaye metni (giriş) yazıyor; biz kapakta sadece başlık gösterdiğimiz için o metin **kapakta kullanılmıyor ve boşta kalıyor**. Bazı hikayelerde bu giriş olmadığı için **1. sayfadan hikaye başlaması eksik** hissediliyor.
- **Düzeltme (kod):** Blueprint sayfa 0 döngüde atlanıyor → ilk paragraf artık ilk iç sayfada (önceki analiz).
- **Düzeltme (prompt):** Pass 2'de kapak = sadece başlık ve **hikaye metni mutlaka sayfa 1'den başlar** diye netleştirildi (aşağıda).

## Mevcut akış

1. **Blueprint (Pass-2)**  
   LLM şunu üretir:
   - `page_number: 0` (kapak) → `text` = **sadece kitap başlığı** (örn. "Ahsen'in Galata Kulesi Macerası")
   - `page_number: 1, 2, ...` → `text` = **hikaye paragrafı** (Türkçe metin)

2. **V3 pipeline (gemini_service)**  
   - **STEP 1:** Kapak ayrı üretilir → `build_cover_prompt()` (sadece görsel; metin = başlık).  
   - **STEP 2:** Blueprint sayfaları döngüde işlenir; **page_number === 0 atlanır** (kapak zaten STEP 1'de eklendi).  
   - Sonuç: `final_pages = [kapak, blueprint_sayfa_1, blueprint_sayfa_2, ...]` — her iç sayfa tek bir blueprint sayfasından gelir.

3. **Önizleme/PDF**  
   - Kapak sayfasında metin olarak **sadece başlık** kullanılıyor (`story_title`).  
   - İlk hikaye paragrafı **ilk iç sayfada** (final_pages[1]) — metin ile görsel aynı blueprint sayfasından.

## Kapak için ayrı prompt

- **Var:** `app/prompt/cover_builder.py` → `build_cover_prompt()`  
- **V3'te kullanım:** `app/prompt_engine/visual_prompt_builder.py` → `build_cover_prompt()` (BookContext + PromptComposer ile).  
- Kapak görseli bu prompt ile üretiliyor; blueprint'in sayfa 0 sahnesi kapak görseli için **doğrudan** kullanılmıyor (blueprint'ten `cover_scene_en` / `cover_scene` veya `story_title` alınıyor).

## Uygulanan düzeltme

- Blueprint'teki **sayfa 0 döngüde atlanıyor** (`if llm_page_num == 0: continue`).  
- Sonuç: `final_pages = [kapak, sayfa_1, sayfa_2, ...]`; ilk hikaye paragrafı ilk iç sayfada.

## Metin–görsel prompt eşleşmesi

- Her `page_data` için **tek** `FinalPageContent` üretiliyor: **aynı** blueprint sayfasından `text_tr` ve `image_prompt_en` alınıyor.
- Sadece `page_number === 0` atlanıyor; sayfa 1, 2, 3… işlenirken metin ile görsel promptu **hep aynı sayfadan** geliyor. Yani metin kaydırılmıyor: 1. iç sayfa = blueprint sayfa 1 (metin + prompt birlikte), 2. iç sayfa = blueprint sayfa 2 (metin + prompt birlikte). **Hikaye ile resim uyumu korunuyor.**

## İsteğe bağlı: 1. sayfa metnini kapakta göstermek

- Şu an kapak sayfasına sadece **başlık** basılıyor.  
- İlk hikaye paragrafını **kapak görselinin altında** göstermek istersen, bu bir **şablon/PDF davranışı** değişikliği olur (kapak sayfasına hangi `text`'in yazılacağı).  
- Bu ayrı bir özellik olarak template/config ile eklenebilir (örn. "cover_show_first_story_paragraph").
