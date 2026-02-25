/**
 * FAQ items — shared between server components (JSON-LD) and client components (UI).
 * Kept separate from the "use client" FAQ component to avoid SSR/RSC boundary issues.
 */
export const faqItems = [
  {
    question: "Kitap ne zaman teslim edilir?",
    answer:
      "Siparişiniz onaylandıktan sonra profesyonel baskıya alınır ve 2-3 iş günü içinde kargo ile adresinize teslim edilir. Kargo takip numarası e-posta ile paylaşılır.",
  },
  {
    question: "Çocuğumun fotoğrafı güvende mi?",
    answer:
      "Evet, tamamen güvendedir. KVKK mevzuatına uygun şekilde işlenir ve fotoğraflar sipariş tamamlandıktan 30 gün sonra sunucularımızdan otomatik olarak silinir. Verileriniz üçüncü taraflarla paylaşılmaz.",
  },
  {
    question: "Hangi yaş gruplarına uygun?",
    answer:
      "Kitaplarımız 2-10 yaş arası çocuklar için tasarlanmıştır. Hikaye temaları ve dil seviyesi çocuğunuzun yaşına göre otomatik olarak uyarlanır.",
  },
  {
    question: "Hikayeyi kendim düzenleyebilir miyim?",
    answer:
      "Evet! Yapay zeka hikayeyi oluşturduktan sonra sipariş öncesinde tüm metni inceleyebilir ve dilediğiniz gibi düzenleyebilirsiniz. Tam kontrol sizdedir.",
  },
  {
    question: "Ödeme yöntemleri nelerdir?",
    answer:
      "Kredi kartı ve banka kartı ile güvenli ödeme yapabilirsiniz. Tüm ödemeler 256-bit SSL şifreleme ile korunur.",
  },
  {
    question: "İade politikanız nedir?",
    answer:
      "Ürün kişiye özel üretildiği için standart iade kabul edilmez. Ancak baskı hatası veya hasarlı ürün durumunda ücretsiz yeniden basım yapılır. Memnuniyetiniz bizim için önemlidir.",
  },
];
