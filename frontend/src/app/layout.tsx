import type { Metadata, Viewport } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import Script from "next/script";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/toaster";

const GA_ID = "G-M76XHJLF85";

const inter = Inter({ subsets: ["latin"] });
const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://www.benimmasalim.com.tr"),
  title: {
    default: "Benim Masalım – Kişiye Özel Çocuk Kitabı",
    template: "%s | Benim Masalım",
  },
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg", apple: "/favicon.svg" },
  description:
    "Yapay zeka destekli, çocuğunuzun adı ve fotoğrafıyla kişiselleştirilmiş masal kitapları oluşturun. Hediye çocuk kitabı için ideal.",
  keywords: [
    "kişiye özel çocuk kitabı",
    "çocuğun adıyla masal",
    "kişiselleştirilmiş masal",
    "hediye çocuk kitabı",
    "yapay zeka çocuk hikayesi",
    "çocuk kitabı",
  ],
  openGraph: {
    title: "Benim Masalım – Kişiye Özel Çocuk Kitabı",
    description: "Çocuğunuzun adı ve fotoğrafıyla kişiselleştirilmiş masal kitabı oluşturun.",
    url: "https://www.benimmasalim.com.tr",
    siteName: "Benim Masalım",
    locale: "tr_TR",
    type: "website",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Benim Masalım – Kişiye Özel Çocuk Kitabı" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Benim Masalım – Kişiye Özel Çocuk Kitabı",
    description: "Çocuğunuzun adı ve fotoğrafıyla kişiselleştirilmiş masal kitabı.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <head>
        {/* Google Analytics 4 */}
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="ga4-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_ID}');
          `}
        </Script>
      </head>
      <body className={`${inter.className} ${playfair.variable}`}>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}

