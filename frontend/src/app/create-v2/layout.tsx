import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Kişiye Özel Çocuk Kitabı Oluştur | Benim Masalım",
  description:
    "Çocuğunuzun adı, fotoğrafı ve seçtiğiniz hikaye ile kişiselleştirilmiş masal kitabı oluşturun. Yapay zeka destekli, eğitici, profesyonel baskı. 5 kolay adımda hazır!",
  keywords: [
    "kişiye özel çocuk kitabı oluştur",
    "kişiselleştirilmiş masal kitabı",
    "çocuk hikaye kitabı sipariş",
    "yapay zeka çocuk kitabı",
    "hediye çocuk kitabı",
  ],
  alternates: { canonical: "https://benimmasalim.com.tr/create" },
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: "Kişiye Özel Çocuk Kitabı Oluştur | Benim Masalım",
    description:
      "5 kolay adımda çocuğunuza özel hikaye kitabı oluşturun. Yapay zeka destekli, profesyonel baskı, ücretsiz kargo.",
    url: "https://benimmasalim.com.tr/create",
    siteName: "Benim Masalım",
    locale: "tr_TR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Kişiye Özel Çocuk Kitabı Oluştur | Benim Masalım",
    description:
      "5 kolay adımda çocuğunuza özel hikaye kitabı. Yapay zeka destekli, eğitici, profesyonel baskı.",
  },
};

export default function CreateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* JSON-LD structured data for the product creation page */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Product",
            name: "Kişiye Özel Masal Kitabı",
            description:
              "Çocuğunuzun adı ve fotoğrafıyla AI destekli kişiselleştirilmiş masal kitabı. Profesyonel baskı, eğitici içerik, ücretsiz kargo.",
            brand: { "@type": "Brand", name: "Benim Masalım" },
            offers: {
              "@type": "Offer",
              url: "https://benimmasalim.com.tr/create",
              priceCurrency: "TRY",
              availability: "https://schema.org/InStock",
              seller: {
                "@type": "Organization",
                name: "Benim Masalım",
              },
            },
            aggregateRating: {
              "@type": "AggregateRating",
              ratingValue: "4.9",
              reviewCount: "150",
            },
          }),
        }}
      />
      {/* robots: noindex for personalized funnel steps (handled client-side) */}
      {children}
    </>
  );
}
