import Link from "next/link";
import Image from "next/image";
import { BookOpen } from "lucide-react";

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
  };
}

const DEFAULT_NAV: FooterNavSection[] = [
  {
    title: "Ürün",
    links: [
      { label: "Kitap Oluştur", href: "/create-v2" },
      { label: "Nasıl Çalışır?", href: "#nasil-calisir" },
      { label: "Örnek Sayfalar", href: "#ornekler" },
      { label: "Fiyatlandırma", href: "#fiyat" },
    ],
  },
  {
    title: "Kurumsal",
    links: [
      { label: "Hakkımızda", href: "/about" },
      { label: "Sıkça Sorulan Sorular", href: "#sss" },
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

/** Links that must always appear regardless of API data */
const REQUIRED_LINKS: FooterLink[] = [
  { label: "Hakkımızda", href: "/about" },
  { label: "Gizlilik Politikası", href: "/privacy", rel: "nofollow" },
  { label: "Kullanım Şartları", href: "/terms", rel: "nofollow" },
  { label: "Mesafeli Satış Sözleşmesi", href: "/distance-sales", rel: "nofollow" },
  { label: "Teslimat ve İade Şartları", href: "/delivery", rel: "nofollow" },
  { label: "KVKK Aydınlatma Metni", href: "/kvkk", rel: "nofollow" },
];

/** Redirect mailto "İletişim" links to the /contact page */
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

const SELLER_INFO = {
  name: "Abdullah Alpaslan",
  businessName: "Benim Masalım",
  taxOffice: "İkitelli",
  vkn: "16106557652",
  kep: "abdullah.alpaslan.2@hs01.kep.tr",
  chamber: "İstanbul Matbaacılar Odası (istanbulmatbaacilar.org.tr)",
};

export default function Footer({ data }: FooterProps) {
  const brandDesc = data?.brand_description ?? DEFAULT_BRAND;
  const rawSections = (data?.nav_sections ?? DEFAULT_NAV) as FooterNavSection[];
  const navSections = ensureRequiredLinks(rawSections);
  const bottomText = data?.bottom_text ?? "Türkiye'de sevgiyle yapıldı";

  return (
    <footer className="border-t bg-muted/30">
      <div className="container py-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <Link href="/" className="flex items-center gap-2" aria-label="Ana Sayfa">
              <BookOpen className="h-6 w-6 text-primary" />
              <span className="text-lg font-bold">Benim Masalım</span>
            </Link>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{brandDesc}</p>
          </div>

          {navSections.map((section) => (
            <div key={section.title}>
              <h3 className="mb-4 text-sm font-semibold">{section.title}</h3>
              <ul className="space-y-2">
                {section.links.map((link) => {
                  const isExternal = link.href.startsWith("mailto:") || link.href.startsWith("http");
                  const isAnchor = link.href.startsWith("#");

                  if (isExternal) {
                    return (
                      <li key={link.label}>
                        <a href={link.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground" rel={link.rel}>
                          {link.label}
                        </a>
                      </li>
                    );
                  }
                  if (isAnchor) {
                    return (
                      <li key={link.label}>
                        <a href={link.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                          {link.label}
                        </a>
                      </li>
                    );
                  }
                  return (
                    <li key={link.label}>
                      <Link href={link.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground" rel={link.rel}>
                        {link.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {/* Satıcı Bilgileri */}
        <div className="mt-10 border-t pt-6">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Satıcı Bilgileri
          </h3>
          <div className="grid gap-x-8 gap-y-1 text-xs text-muted-foreground sm:grid-cols-2 lg:grid-cols-3">
            <p><span className="font-medium">Ad Soyad:</span> {SELLER_INFO.name}</p>
            <p><span className="font-medium">İşletme:</span> {SELLER_INFO.businessName}</p>
            <p><span className="font-medium">Vergi Dairesi / VKN:</span> {SELLER_INFO.taxOffice} / {SELLER_INFO.vkn}</p>
            <p><span className="font-medium">KEP:</span> {SELLER_INFO.kep}</p>
            <p><span className="font-medium">Meslek Odası:</span> {SELLER_INFO.chamber}</p>
          </div>
        </div>

        <div className="mt-6 flex flex-col items-center justify-between gap-4 border-t pt-6 md:flex-row">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Benim Masalım. Tüm hakları saklıdır.
          </p>
          <div className="flex items-center gap-4">
            <Image
              src="/images/payment/logo_band_colored.svg"
              alt="iyzico ile güvenli ödeme - Visa, Mastercard, Troy"
              width={215}
              height={16}
              className="h-4 w-auto"
            />
            <p className="text-xs text-muted-foreground">{bottomText}</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
