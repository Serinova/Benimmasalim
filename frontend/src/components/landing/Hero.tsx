import Link from "next/link";
import { Button } from "@/components/ui/button";
import { BookOpen, Sparkles, ArrowRight, CheckCircle2 } from "lucide-react";
import ShowcaseBook from "./ShowcaseBook";

interface HeroData {
  badge?: string;
  highlight?: string;
  primary_cta_text?: string;
  primary_cta_url?: string;
  secondary_cta_text?: string;
  secondary_cta_url?: string;
  micro_trust?: string;
  showcase_pages?: string[];
  trust_items?: string[];
  [key: string]: unknown;
}

interface HeroProps {
  title?: string;
  subtitle?: string;
  data?: HeroData;
}

const DEFAULTS = {
  title: "Çocuğunuzun Adıyla Yazılan",
  highlight: "Kişiye Özel Masal Kitabı",
  subtitle:
    "Yapay zeka ile çocuğunuzun fotoğrafı ve adını kullanarak tamamen özgün, eğitici değerler içeren profesyonel basılı hikaye kitapları oluşturun.",
  badge: "Yapay Zeka Destekli",
  primary_cta_text: "Masalını Oluştur",
  primary_cta_url: "/create-v2",
  secondary_cta_text: "Nasıl Çalışır?",
  secondary_cta_url: "/#nasil-calisir",
  trust_items: ["2–3 iş günü teslimat", "Güvenli ödeme", "KVKK uyumlu"],
};

export default function Hero({ title, subtitle, data }: HeroProps) {
  const titleLine1 = title ?? DEFAULTS.title;
  const highlight = data?.highlight ?? DEFAULTS.highlight;
  const sub = subtitle ?? DEFAULTS.subtitle;
  const badge = data?.badge ?? DEFAULTS.badge;
  const primaryCtaText = data?.primary_cta_text ?? DEFAULTS.primary_cta_text;
  const primaryCtaUrl = data?.primary_cta_url ?? DEFAULTS.primary_cta_url;
  const secondaryCtaText = data?.secondary_cta_text ?? DEFAULTS.secondary_cta_text;
  const secondaryCtaUrl = data?.secondary_cta_url ?? DEFAULTS.secondary_cta_url;
  const trustItems = (data?.trust_items as string[] | undefined) ?? DEFAULTS.trust_items;
  const showcasePages = (data?.showcase_pages ?? []).filter((u) => u && u.length > 0);

  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-purple-50/60 via-white to-white">
      {/* Decorative blobs */}
      <div
        className="pointer-events-none absolute -right-40 -top-40 h-[500px] w-[500px] rounded-full bg-purple-100/40 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -left-20 top-1/2 h-[300px] w-[300px] rounded-full bg-pink-100/30 blur-3xl"
        aria-hidden="true"
      />

      <div className="container relative flex flex-col items-center gap-10 pb-20 pt-16 text-center md:pb-28 md:pt-24 lg:flex-row lg:gap-16 lg:py-28 lg:text-left">
        {/* Left content */}
        <div className="flex max-w-2xl flex-1 flex-col items-center gap-6 lg:items-start">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-purple-200 bg-purple-50 px-4 py-1.5 text-sm font-semibold text-purple-700">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            <span>{badge}</span>
          </div>

          {/* H1 — semantically split: plain line + gradient highlight */}
          <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-5xl md:text-6xl">
            {titleLine1}{" "}
            <span className="bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text text-transparent">
              {highlight}
            </span>
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-slate-600 md:text-xl">
            {sub}
          </p>

          {/* CTAs */}
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:gap-4">
            <Link href={primaryCtaUrl}>
              <Button
                size="lg"
                className="magic-button w-full gap-2 text-base sm:w-auto"
              >
                <BookOpen className="h-5 w-5" aria-hidden="true" />
                {primaryCtaText}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </Link>
            <Link href={secondaryCtaUrl}>
              <Button size="lg" variant="outline" className="w-full gap-2 border-slate-200 text-base text-slate-700 hover:border-purple-200 hover:bg-purple-50 hover:text-purple-700 sm:w-auto">
                {secondaryCtaText}
              </Button>
            </Link>
          </div>

          {/* Trust items */}
          <ul className="flex flex-wrap justify-center gap-x-5 gap-y-2 lg:justify-start" aria-label="Güven bilgileri">
            {trustItems.map((item) => (
              <li key={item} className="flex items-center gap-1.5 text-sm text-slate-500">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Right side: Showcase Book or Placeholder */}
        <div className="flex flex-1 items-center justify-center">
          {showcasePages.length > 0 ? (
            <ShowcaseBook pages={showcasePages} />
          ) : (
            <div
              className="relative flex h-[300px] w-[260px] max-w-full items-center justify-center rounded-3xl border-2 border-dashed border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 shadow-inner sm:h-[380px] sm:w-[320px]"
              aria-hidden="true"
            >
              <div className="flex flex-col items-center gap-4 text-purple-300">
                <BookOpen className="h-14 w-14" />
                <span className="max-w-[180px] text-center text-sm font-medium text-purple-400">
                  Çocuğunuzun kahramanı olduğu kişiye özel kitap
                </span>
              </div>
              <div className="absolute -right-4 -top-4 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-pink-500 text-white shadow-lg">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="absolute -bottom-3 -left-3 rounded-full bg-white px-3 py-1 text-xs font-bold text-purple-700 shadow-md ring-1 ring-purple-100">
                %100 Özgün
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
