import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Hero from "@/components/landing/Hero";
import TrustBar from "@/components/landing/TrustBar";
import HowItWorks from "@/components/landing/HowItWorks";
import Features from "@/components/landing/Features";
import Preview from "@/components/landing/Preview";
import Testimonials from "@/components/landing/Testimonials";
import Adventures from "@/components/landing/Adventures";
import Pricing from "@/components/landing/Pricing";
import FAQ from "@/components/landing/FAQ";
import { DEFAULT_FAQ_ITEMS, type FAQItem } from "@/lib/homepage-defaults";
import CTABand from "@/components/landing/CTABand";
import Footer from "@/components/landing/Footer";
import { getHomepageSections, findSection, getProducts, getScenarios } from "@/lib/homepage";

/* ─── Force dynamic rendering (homepage fetches from API at request time) ── */
export const dynamic = "force-dynamic";

/* ─── Page-level SEO metadata ─────────────────────────────────────── */

export const metadata: Metadata = {
  title: "Kişiye Özel Çocuk Kitabı | Benim Masalım – Çocuğunuzun Adıyla Masal",
  description:
    "Çocuğunuzun adı ve fotoğrafıyla kişiselleştirilmiş masal kitabı oluşturun. Yapay zeka destekli, eğitici değerler içeren profesyonel baskı. Hediye çocuk kitabı için en özel seçim.",
  keywords: [
    "kişiye özel çocuk kitabı",
    "çocuğun adıyla masal",
    "kişiselleştirilmiş masal",
    "hediye çocuk kitabı",
    "kişiselleştirilmiş çocuk kitabı",
    "yapay zeka çocuk hikayesi",
    "çocuğa özel hikaye kitabı",
    "isimli masal kitabı",
  ],
  alternates: { canonical: "https://www.benimmasalim.com.tr" },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-video-preview": -1, "max-image-preview": "large", "max-snippet": -1 },
  },
  openGraph: {
    title: "Kişiye Özel Çocuk Kitabı | Benim Masalım",
    description: "Çocuğunuzun adı ve fotoğrafıyla kişiselleştirilmiş masal kitabı oluşturun. Yapay zeka destekli, eğitici, profesyonel baskı.",
    url: "https://www.benimmasalim.com.tr",
    siteName: "Benim Masalım",
    locale: "tr_TR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Kişiye Özel Çocuk Kitabı | Benim Masalım",
    description: "Çocuğunuzun adı ve fotoğrafıyla kişiselleştirilmiş masal kitabı. Yapay zeka destekli, eğitici, profesyonel baskı.",
  },
};

/* ─── JSON-LD Structured Data ─────────────────────────────────────── */

function OrganizationJsonLd() {
  const data = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Benim Masalım",
    url: "https://www.benimmasalim.com.tr",
    logo: "https://www.benimmasalim.com.tr/favicon.svg",
    description: "Yapay zeka destekli kişiye özel çocuk kitabı platformu. Çocuğunuzun adıyla masal oluşturun.",
    sameAs: [],
  };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}

function ProductJsonLd() {
  const data = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: "Kişiye Özel Masal Kitabı",
    description: "Çocuğunuzun adı ve fotoğrafıyla AI destekli kişiselleştirilmiş masal kitabı. Profesyonel baskı, eğitici içerik.",
    brand: { "@type": "Brand", name: "Benim Masalım" },
    offers: {
      "@type": "Offer",
      url: "https://www.benimmasalim.com.tr/create",
      priceCurrency: "TRY",
      availability: "https://schema.org/InStock",
      seller: { "@type": "Organization", name: "Benim Masalım" },
    },
    aggregateRating: { "@type": "AggregateRating", ratingValue: "4.9", reviewCount: "150" },
  };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}

function FAQPageJsonLd({ items }: { items: FAQItem[] }) {
  const data = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}

/* ─── Page Component (Server) ─────────────────────────────────────── */

export default async function HomePage() {
  // Fetch sections + products + scenarios in parallel
  const [sections, products, scenarios] = await Promise.all([
    getHomepageSections(),
    getProducts(),
    getScenarios(),
  ]);

  // Helper to get section data by type
  const s = (type: string) => findSection(sections, type);

  // Build visible section set for conditional rendering
  const visibleTypes = new Set(sections.map((sec) => sec.section_type));
  // If API returned nothing, show all sections with defaults
  const showAll = sections.length === 0;
  const isVisible = (type: string) => showAll || visibleTypes.has(type);

  // Get FAQ items for JSON-LD
  const faqSection = s("FAQ");
  const faqItems: FAQItem[] = (faqSection?.data?.items as FAQItem[] | undefined) ?? DEFAULT_FAQ_ITEMS;

  return (
    <>
      <OrganizationJsonLd />
      <ProductJsonLd />
      <FAQPageJsonLd items={faqItems} />

      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        İçeriğe geç
      </a>

      <div className="flex min-h-screen flex-col">
        <Header />

        <main id="main-content">
          {isVisible("HERO") && (
            <Hero
              title={s("HERO")?.title ?? undefined}
              subtitle={s("HERO")?.subtitle ?? undefined}
              data={s("HERO")?.data as Record<string, unknown> | undefined}
            />
          )}

          {isVisible("TRUST_BAR") && (
            <TrustBar data={s("TRUST_BAR")?.data as { items?: { icon: string; label: string; description: string }[] } | undefined} />
          )}

          {isVisible("HOW_IT_WORKS") && (
            <HowItWorks
              title={s("HOW_IT_WORKS")?.title ?? undefined}
              subtitle={s("HOW_IT_WORKS")?.subtitle ?? undefined}
              data={s("HOW_IT_WORKS")?.data as { steps?: { number: string; icon: string; title: string; description: string }[] } | undefined}
            />
          )}

          {isVisible("FEATURES") && (
            <Features
              title={s("FEATURES")?.title ?? undefined}
              subtitle={s("FEATURES")?.subtitle ?? undefined}
              data={s("FEATURES")?.data as { items?: { icon: string; title: string; description: string }[] } | undefined}
            />
          )}

          {isVisible("PREVIEW") && (
            <Preview
              title={s("PREVIEW")?.title ?? undefined}
              subtitle={s("PREVIEW")?.subtitle ?? undefined}
              data={s("PREVIEW")?.data as { items?: { title: string; description: string; color: string }[] } | undefined}
            />
          )}

          {isVisible("TESTIMONIALS") && (
            <Testimonials
              title={s("TESTIMONIALS")?.title ?? undefined}
              subtitle={s("TESTIMONIALS")?.subtitle ?? undefined}
              data={s("TESTIMONIALS")?.data as { items?: { name: string; badge: string; rating: number; text: string }[] } | undefined}
            />
          )}

          {/* Adventures / Scenarios section — always visible when scenarios exist */}
          <Adventures
            title={s("ADVENTURES")?.title ?? undefined}
            subtitle={s("ADVENTURES")?.subtitle ?? undefined}
            scenarios={scenarios}
          />

          {isVisible("PRICING") && (
            <Pricing
              title={s("PRICING")?.title ?? undefined}
              subtitle={s("PRICING")?.subtitle ?? undefined}
              data={s("PRICING")?.data as Record<string, unknown> | undefined}
              products={products}
            />
          )}

          {isVisible("FAQ") && (
            <FAQ
              title={s("FAQ")?.title ?? undefined}
              subtitle={s("FAQ")?.subtitle ?? undefined}
              data={s("FAQ")?.data as { items?: FAQItem[] } | undefined}
            />
          )}

          {isVisible("CTA_BAND") && (
            <CTABand
              title={s("CTA_BAND")?.title ?? undefined}
              subtitle={s("CTA_BAND")?.subtitle ?? undefined}
              data={s("CTA_BAND")?.data as { cta_text?: string; cta_url?: string } | undefined}
            />
          )}
        </main>

        {isVisible("FOOTER") && (
          <Footer data={s("FOOTER")?.data as Record<string, unknown> | undefined} />
        )}
      </div>
    </>
  );
}
