import Link from "next/link";
import Image from "next/image";

interface FooterLink {
  label: string;
  href: string;
  rel?: string;
}

interface FooterNavSection {
  title: string;
  links: FooterLink[];
}

interface FooterProps {
  data?: {
    brand_description?: string;
    nav_sections?: FooterNavSection[];
    bottom_text?: string;
    seller_name?: string;
    seller_business_name?: string;
    seller_tax_office?: string;
    seller_vkn?: string;
    seller_kep?: string;
    seller_chamber?: string;
  };
}

const DEFAULT_NAV: FooterNavSection[] = [
  {
    title: "Ürün",
    links: [
      { label: "Kitap Oluştur", href: "/create-v2" },
      { label: "Nasıl Çalışır?", href: "/#nasil-calisir" },
      { label: "Örnek Sayfalar", href: "/#ornekler" },
      { label: "Fiyatlandırma", href: "/#fiyat" },
    ],
  },
  {
    title: "Kurumsal",
    links: [
      { label: "Hakkımızda", href: "/about" },
      { label: "Sıkça Sorulan Sorular", href: "/#sss" },
      { label: "İletişim", href: "/contact" },
    ],
  },
  {
    title: "Yasal",
    links: [
      { label: "KVKK Aydınlatma Metni", href: "/kvkk", rel: "nofollow" },
      { label: "Gizlilik Politikası", href: "/privacy", rel: "nofollow" },
      { label: "Kullanım Şartları", href: "/terms", rel: "nofollow" },
      { label: "Mesafeli Satış Sözleşmesi", href: "/distance-sales", rel: "nofollow" },
      { label: "Teslimat ve İade Şartları", href: "/delivery", rel: "nofollow" },
      { label: "Veri Talebi", href: "/data-request", rel: "nofollow" },
    ],
  },
];

const REQUIRED_LINKS: FooterLink[] = [
  { label: "Hakkımızda", href: "/about" },
  { label: "Gizlilik Politikası", href: "/privacy", rel: "nofollow" },
  { label: "Kullanım Şartları", href: "/terms", rel: "nofollow" },
  { label: "Mesafeli Satış Sözleşmesi", href: "/distance-sales", rel: "nofollow" },
  { label: "Teslimat ve İade Şartları", href: "/delivery", rel: "nofollow" },
  { label: "KVKK Aydınlatma Metni", href: "/kvkk", rel: "nofollow" },
];

function fixContactLinks(sections: FooterNavSection[]): FooterNavSection[] {
  return sections.map((s) => ({
    ...s,
    links: s.links.map((l) =>
      l.label === "İletişim" && l.href.startsWith("mailto:")
        ? { ...l, href: "/contact" }
        : l
    ),
  }));
}

function ensureRequiredLinks(sections: FooterNavSection[]): FooterNavSection[] {
  const fixed = fixContactLinks(sections);
  const allHrefs = new Set(fixed.flatMap((s) => s.links.map((l) => l.href)));
  const missing = REQUIRED_LINKS.filter((rl) => !allHrefs.has(rl.href));
  if (missing.length === 0) return fixed;

  const legalSection = fixed.find((s) => s.title === "Yasal");
  if (legalSection) {
    return fixed.map((s) =>
      s.title === "Yasal" ? { ...s, links: [...s.links, ...missing] } : s
    );
  }
  return [...fixed, { title: "Yasal", links: missing }];
}

const DEFAULT_BRAND =
  "Yapay zeka destekli kişiye özel çocuk kitabı platformu. Çocuğunuzun adıyla masal oluşturun.";

export default function Footer({ data }: FooterProps) {
  const brandDesc = data?.brand_description ?? DEFAULT_BRAND;
  const rawSections = (data?.nav_sections ?? DEFAULT_NAV) as FooterNavSection[];
  const navSections = ensureRequiredLinks(rawSections);
  const bottomText = data?.bottom_text ?? "Türkiye'de sevgiyle yapıldı 🇹🇷";

  const sellerName = data?.seller_name ?? process.env.NEXT_PUBLIC_SELLER_NAME ?? "Abdullah Alpaslan";
  const sellerBusiness = data?.seller_business_name ?? "Benim Masalım";
  const sellerTaxOffice = data?.seller_tax_office ?? "İkitelli";
  const sellerVkn = data?.seller_vkn ?? process.env.NEXT_PUBLIC_SELLER_VKN ?? "16106557652";
  const sellerKep = data?.seller_kep ?? process.env.NEXT_PUBLIC_SELLER_KEP ?? "abdullah.alpaslan.2@hs01.kep.tr";
  const sellerChamber = data?.seller_chamber ?? "İstanbul Matbaacılar Odası";

  return (
    <footer className="border-t bg-slate-50/80">
      <div className="container py-14">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div>
            <Link href="/" className="flex items-center gap-2.5" aria-label="Ana Sayfa — Benim Masalım">
              <Image
                src="/logo.png"
                alt="Benim Masalım"
                width={52}
                height={52}
                className="h-12 w-12 object-contain"
              />
              <span className="text-lg font-bold text-slate-900">
                Benim <span className="text-primary">Masalım</span>
              </span>
            </Link>
            <p className="mt-3 text-sm leading-relaxed text-slate-500">{brandDesc}</p>
          </div>

          {navSections.map((section) => (
            <div key={section.title}>
              <h3 className="mb-4 text-sm font-semibold text-slate-900">{section.title}</h3>
              <ul className="space-y-2">
                {section.links.map((link) => {
                  const isExternal = link.href.startsWith("mailto:") || link.href.startsWith("http");
                  return (
                    <li key={link.label}>
                      {isExternal ? (
                        <a
                          href={link.href}
                          className="text-sm text-slate-500 transition-colors hover:text-primary"
                          rel={link.rel}
                          target="_blank"
                        >
                          {link.label}
                        </a>
                      ) : (
                        <Link
                          href={link.href}
                          className="text-sm text-slate-500 transition-colors hover:text-primary"
                          rel={link.rel}
                        >
                          {link.label}
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {/* Satıcı Bilgileri */}
        <div className="mt-10 border-t pt-6">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Satıcı Bilgileri
          </h3>
          <div className="grid gap-x-8 gap-y-1 text-xs text-slate-500 sm:grid-cols-2 lg:grid-cols-3">
            <p><span className="font-medium text-slate-600">Ad Soyad:</span> {sellerName}</p>
            <p><span className="font-medium text-slate-600">İşletme:</span> {sellerBusiness}</p>
            <p><span className="font-medium text-slate-600">Vergi Dairesi / VKN:</span> {sellerTaxOffice} / {sellerVkn}</p>
            <p><span className="font-medium text-slate-600">KEP:</span> {sellerKep}</p>
            <p><span className="font-medium text-slate-600">Meslek Odası:</span> {sellerChamber}</p>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-6 flex flex-col items-center justify-between gap-4 border-t pt-6 sm:flex-row">
          <p className="text-sm text-slate-500">
            &copy; {new Date().getFullYear()} Benim Masalım. Tüm hakları saklıdır.
          </p>
          <div className="flex items-center gap-4">
            <Image
              src="/images/payment/logo_band_colored.svg"
              alt="iyzico ile güvenli ödeme — Visa, Mastercard, Troy kabul edilir"
              width={180}
              height={20}
              className="h-5 w-auto"
              unoptimized
            />
            <p className="text-xs text-slate-400">{bottomText}</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
