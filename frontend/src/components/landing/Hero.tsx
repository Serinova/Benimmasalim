import Link from "next/link";
import { Button } from "@/components/ui/button";
import { BookOpen, Sparkles, ArrowRight } from "lucide-react";
import ShowcaseBook from "./ShowcaseBook";

interface HeroData {
  badge?: string;
  primary_cta_text?: string;
  primary_cta_url?: string;
  secondary_cta_text?: string;
  secondary_cta_url?: string;
  micro_trust?: string;
  showcase_pages?: string[];
  [key: string]: unknown;
}

interface HeroProps {
  title?: string;
  subtitle?: string;
  data?: HeroData;
}

const DEFAULTS = {
  title: "Çocuğunuzun Adıyla Yazılan Kişiye Özel Masal Kitabı",
  subtitle:
    "Yapay zeka ile çocuğunuzun fotoğrafı ve adını kullanarak tamamen özgün, eğitici değerler içeren profesyonel basılı hikaye kitapları oluşturun. Hediye çocuk kitabı için en özel seçim.",
  badge: "Yapay Zeka Destekli",
  primary_cta_text: "Masalını Oluştur",
  primary_cta_url: "/create",
  secondary_cta_text: "Nasıl Çalışır?",
  secondary_cta_url: "#nasil-calisir",
  micro_trust: "Kredi kartı gerekmez \u2022 2-3 iş günü teslimat \u2022 KVKK uyumlu",
};

export default function Hero({ title, subtitle, data }: HeroProps) {
  const h1 = title ?? DEFAULTS.title;
  const sub = subtitle ?? DEFAULTS.subtitle;
  const badge = data?.badge ?? DEFAULTS.badge;
  const primaryCtaText = data?.primary_cta_text ?? DEFAULTS.primary_cta_text;
  const primaryCtaUrl = data?.primary_cta_url ?? DEFAULTS.primary_cta_url;
  const secondaryCtaText = data?.secondary_cta_text ?? DEFAULTS.secondary_cta_text;
  const secondaryCtaUrl = data?.secondary_cta_url ?? DEFAULTS.secondary_cta_url;
  const microTrust = data?.micro_trust ?? DEFAULTS.micro_trust;
  const showcasePages = (data?.showcase_pages ?? []).filter((u) => u && u.length > 0);

  const words = h1.split(" ");
  const midpoint = Math.ceil(words.length / 2);
  const h1Part1 = words.slice(0, midpoint).join(" ");
  const h1Part2 = words.slice(midpoint).join(" ");

  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />

      <div className="container relative flex flex-col items-center gap-8 pb-16 pt-20 text-center md:pb-24 md:pt-28 lg:flex-row lg:gap-12 lg:text-left">
        <div className="flex max-w-2xl flex-1 flex-col items-center gap-6 lg:items-start">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
            <Sparkles className="h-4 w-4" />
            <span>{badge}</span>
          </div>

          <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl">
            {h1Part1}{" "}
            <span className="bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
              {h1Part2}
            </span>
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground md:text-xl">
            {sub}
          </p>

          <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
            <Link href={primaryCtaUrl}>
              <Button size="lg" className="magic-button gap-2 text-base">
                <BookOpen className="h-5 w-5" />
                {primaryCtaText}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href={secondaryCtaUrl}>
              <Button size="lg" variant="outline" className="gap-2 text-base">
                {secondaryCtaText}
              </Button>
            </a>
          </div>

          <p className="text-sm text-muted-foreground">{microTrust}</p>
        </div>

        {/* Right side: Showcase Book or Placeholder */}
        <div className="flex flex-1 items-center justify-center">
          {showcasePages.length > 0 ? (
            <ShowcaseBook pages={showcasePages} />
          ) : (
            <div
              className="relative flex h-[320px] w-[280px] items-center justify-center rounded-2xl border-2 border-dashed border-primary/20 bg-gradient-to-br from-primary/5 to-purple-100/50 sm:h-[400px] sm:w-[340px]"
              aria-hidden="true"
            >
              <div className="flex flex-col items-center gap-4 text-primary/40">
                <BookOpen className="h-16 w-16" />
                <span className="max-w-[200px] text-center text-sm font-medium">
                  Çocuğunuzun kahramanı olduğu kişiye özel kitap
                </span>
              </div>
              <div className="absolute -right-3 -top-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="absolute -bottom-2 -left-2 rounded-full bg-purple-100 px-3 py-1 text-xs font-semibold text-primary shadow">
                %100 Özgün
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
