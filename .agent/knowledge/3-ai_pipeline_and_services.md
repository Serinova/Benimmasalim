# Yapay Zeka Servisleri ve V3 Pipeline (Prompt Engine)

## 1. Servis Mimari Özeti (AI Services)
Antigravity, tüm dış yapay zeka entegrasyonlarını `.cursor/rules/ai-services.mdc` kurallarına uygun olarak yürütür:

- **Metin Üretimi (Story Context)**: Google Gemini API
- **Görsel/Kitap Sahnesi Üretimi**: Google Imagen 3 API veya muadili (örn. OpenAI DALL-E) `get_image_generator` aracı ile soyutlanmış (abstract) olarak çağrılır.
- **Seslendirme/Audio**: ElevenLabs veya Google TTS Entegrasyonları
- **Yüz Eşleştirme (İsteğe Bağlı)**: InsightFace ile çocuk karakter tasarımı

## 2. Ortak Hata Yönetimi
Bu servislerde oluşacak herhangi bir hata (Rate Limit, Invalid Request, Connection Timeout) KESİNLİKLE özel olarak tasarlanmış olan `AIServiceError` exception'u ile fırlatılarak loglara işlenir ve retry mekanizması tetiklenecekse buna göre işlem sırasına alınır.

## 3. The BookContext (V3 Pipeline)
Projeye önceden (Legacy) `V2 pipeline` mantığı hakimdi ve bu kodlar spagetti idi. Şuan tüm sistem `V3 Pipeline` olan **BookContext / PromptComposer** yapısı üzerinden yürümelidir.
- Metin içerikleri defalarca kez hardcode string değiştirerek oluşturulamaz.
- Promptlar modülerdir (`app/prompt/` modüllerinden çekilir).
- Bir senaryoda "korsan" macerası varsa bile child-safety nedeniyle "savaş, kavga, silah" kelimeleri yasaklanmış, "hazine arama, takım çalışması" gibi soft kelimelerle prompt engine beslenir.

**Karakter ve Sahne Tutarlılığı**
- Tüm görseller tek bir çocuğa / ana karaktere ait hikaye satırlarını temsil etmektedir.
- Görsel üretimi (Imagen 3) için prompt tasarlarken, ilk oluşturulan ana karakter seed'inin / tanımının hikayenin tüm sahnelerinde devam ettiğinden ("Sahne tutarlılığı" ve "Karakter devamlılığı") emin olmalısınız.
