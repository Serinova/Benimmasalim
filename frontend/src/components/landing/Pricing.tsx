"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  Check,
  ArrowRight,
  BookOpen,
  Mic,
  Star,
  Volume2,
  Truck,
  Palette,
} from "lucide-react";

/* ─── Types ─────────────────────────────────────────────────── */

interface ProductData {
  id: string;
  name: string;
  base_price: number;
  discounted_price: number | null;
  default_page_count: number;
  extra_page_price: number;
  cover_type: string;
  paper_type: string;
  promo_badge: string | null;
  feature_list: string[];
  rating: number | null;
  review_count: number;
  social_proof_text: string | null;
  thumbnail_url: string | null;
  product_type?: string;
}

interface CategorizedProducts {
  storyBooks: ProductData[];
  coloringBooks: ProductData[];
  audioAddons: ProductData[];
  all: ProductData[];
}

interface PricingProps {
  title?: string;
  subtitle?: string;
  products?: CategorizedProducts | ProductData[];
  data?: {
    package_name?: string;
    package_description?: string;
    price_text?: string;
    price_note?: string;
    cta_text?: string;
    cta_url?: string;
    badge_text?: string;
    included?: string[];
  };
}

/* ─── Defaults ──────────────────────────────────────────────── */

const DEFAULT_FEATURES_STORY = [
  "Kişiye özel AI hikaye oluşturma",
  "Çocuğunuzun fotoğrafıyla illüstrasyonlar",
  "Profesyonel kalite baskı",
  "Eğitici değerler içeriği",
  "Sipariş öncesi hikaye önizleme",
  "KVKK uyumlu veri güvenliği",
];

const DEFAULT_FEATURES_COLORING = [
  "Hikayenizdeki karakterler ve sahneler",
  "Profesyonel line-art çizimler",
  "Ayrı fiziksel kitap olarak basılır",
  "Yaratıcılığı geliştiren aktivite",
];

/* ─── Helpers ───────────────────────────────────────────────── */

function fmt(price: number) {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
}

function discountPct(base: number, discounted: number) {
  return Math.round(((base - discounted) / base) * 100);
}

/* ─── Audio prices (dynamic from backend) ───────────────────── */

interface AudioPrices { systemVoice: number; clonedVoice: number }

function useAudioPrices(): AudioPrices {
  const [prices, setPrices] = useState<AudioPrices>({ systemVoice: 150, clonedVoice: 300 });
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "https://benimmasalim-backend-554846094227.europe-west1.run.app/api/v1";
    fetch(`${apiBase}/products?type=audio_addon`)
      .then(r => r.json())
      .then((data: ProductData[]) => {
        if (!Array.isArray(data)) return;
        const sys = data.find(p => p.name?.toLowerCase().includes("sistem") || p.name?.toLowerCase().includes("standart"));
        const cln = data.find(p => p.name?.toLowerCase().includes("klon") || p.name?.toLowerCase().includes("özel"));
        setPrices({
          systemVoice: sys ? (sys.discounted_price ?? sys.base_price) : 150,
          clonedVoice: cln ? (cln.discounted_price ?? cln.base_price) : 300,
        });
      })
      .catch(() => { });
  }, []);
  return prices;
}

/* ─────────────────────────────────────────────────────────────
   COMPONENT: Main Pricing Section
   ──────────────────────────────────────────────────────────── */

export default function Pricing({ title, subtitle, products, data }: PricingProps) {
  const audioPrices = useAudioPrices();

  const heading = title ?? "Fiyatlandırma";
  const sub = subtitle ?? "Tek paket, eksiksiz deneyim. Ek ücret veya gizli maliyet yok.";

  // Infer product type from name when product_type is missing
  const inferType = (p: ProductData): string => {
    if (p.product_type) return p.product_type;
    const n = (p.name || "").toLowerCase();
    if (n.includes("boyama")) return "coloring_book";
    if (n.includes("sesli") || n.includes("ses")) return "audio_addon";
    return "story_book";
  };

  const categorized: CategorizedProducts = Array.isArray(products)
    ? {
      storyBooks: products.filter(p => inferType(p) === "story_book"),
      coloringBooks: products.filter(p => inferType(p) === "coloring_book"),
      audioAddons: products.filter(p => inferType(p) === "audio_addon"),
      all: products,
    }
    : (products ?? { storyBooks: [], coloringBooks: [], audioAddons: [], all: [] });

  const storyBook = categorized.storyBooks[0];
  const coloringBook = categorized.coloringBooks[0];

  // Get audio prices from API products, fallback to hook
  const sysAddon = categorized.audioAddons.find(p => p.name?.toLowerCase().includes("sistem"));
  const clnAddon = categorized.audioAddons.find(p => p.name?.toLowerCase().includes("klon"));
  const finalAudioPrices = {
    systemVoice: sysAddon ? (sysAddon.discounted_price ?? sysAddon.base_price) : audioPrices.systemVoice,
    clonedVoice: clnAddon ? (clnAddon.discounted_price ?? clnAddon.base_price) : audioPrices.clonedVoice,
  };

  return (
    <section id="fiyat" className="scroll-mt-20 bg-gradient-to-b from-slate-50/50 to-white py-20">
      <div className="container">
        {/* Header */}
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
        </div>

        {storyBook ? (
          <div className="mx-auto max-w-6xl">
            {/* 3-COLUMN GRID: Story | Audio (stacked) | Coloring */}
            <div className="grid items-stretch gap-5 lg:grid-cols-3">

              {/* ── COL 1: Story Book ── */}
              <div className="relative flex flex-col overflow-hidden rounded-2xl border-2 border-purple-200 bg-white shadow-xl">
                {/* Top badge strip */}
                <div className="bg-gradient-to-r from-purple-600 to-pink-500 px-4 py-2.5 text-center text-sm font-bold text-white">
                  {storyBook.promo_badge || "⭐ En Popüler Seçim"}
                </div>

                <div className="flex flex-1 flex-col p-6">
                  {/* Title */}
                  <div className="mb-4">
                    <div className="mb-1 flex items-center gap-2">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-100">
                        <BookOpen className="h-5 w-5 text-purple-600" />
                      </div>
                      <h3 className="text-xl font-bold">{storyBook.name}</h3>
                    </div>
                    <p className="ml-11 text-xs text-muted-foreground">
                      {storyBook.default_page_count} Sayfa • {storyBook.cover_type} • {storyBook.paper_type}
                    </p>
                    {(storyBook.rating ?? 0) > 0 && (
                      <div className="ml-11 mt-2 flex items-center gap-1.5">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star key={i} className={`h-3.5 w-3.5 ${i < Math.round(storyBook.rating ?? 0) ? "fill-amber-400 text-amber-400" : "text-slate-200"}`} />
                        ))}
                        <span className="text-xs text-slate-500">{storyBook.rating?.toFixed(1)} ({storyBook.review_count})</span>
                      </div>
                    )}
                    {storyBook.social_proof_text && (
                      <p className="ml-11 mt-1 text-xs font-medium text-emerald-600">{storyBook.social_proof_text}</p>
                    )}
                  </div>

                  {/* Price */}
                  <div className="mb-4">
                    {storyBook.discounted_price && (
                      <div className="mb-1 flex items-center gap-2">
                        <span className="text-base text-muted-foreground line-through">{fmt(storyBook.base_price)}</span>
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-600">
                          %{discountPct(storyBook.base_price, storyBook.discounted_price)} İndirim
                        </span>
                      </div>
                    )}
                    <div className="text-4xl font-bold tracking-tight text-purple-600">
                      {fmt(storyBook.discounted_price ?? storyBook.base_price)}
                    </div>
                    {storyBook.extra_page_price > 0 && (
                      <p className="mt-0.5 text-xs text-muted-foreground">Ek sayfa: +{fmt(storyBook.extra_page_price)} / sayfa</p>
                    )}
                  </div>

                  {/* Features */}
                  <ul className="mb-4 flex-1 space-y-1.5">
                    {(storyBook.feature_list.length > 0 ? storyBook.feature_list : DEFAULT_FEATURES_STORY).map(f => (
                      <li key={f} className="flex items-start gap-2 text-sm">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" /><span>{f}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Shipping */}
                  <div className="mb-4 flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700">
                    <Truck className="h-3.5 w-3.5 flex-shrink-0" />
                    Ücretsiz kargo ile kapınıza kadar teslimat
                  </div>

                  {/* CTA */}
                  <Link href="/create-v2">
                    <Button className="w-full gap-2 bg-gradient-to-r from-purple-600 to-pink-500 text-base font-bold shadow-lg shadow-purple-200 hover:from-purple-700 hover:to-pink-600">
                      Hemen Sipariş Ver <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>

                {/* Bottom strip */}
                <div className="bg-gradient-to-r from-purple-600 to-pink-500 px-4 py-1.5 text-center text-[11px] font-medium text-white/80">
                  Profesyonel baskı • 2-3 iş günü teslimat
                </div>
              </div>

              {/* ── COL 2: Audio Cards (stacked, same total height as story) ── */}
              <div className="flex flex-col gap-4">
                {/* System Voice Card */}
                <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border-2 border-blue-200 bg-white shadow-xl">
                  {/* Top strip */}
                  <div className="bg-gradient-to-r from-blue-500 to-cyan-500 px-4 py-2 text-center text-sm font-bold text-white">
                    🎧 Sesli Okuma
                  </div>
                  <div className="flex flex-1 flex-col p-5">
                    <div className="mb-3 flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-100">
                        <Volume2 className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold">Sistem Sesi</h4>
                        <p className="text-[11px] text-muted-foreground">AI profesyonel ses teknolojisi</p>
                      </div>
                    </div>
                    <div className="mb-3">
                      <span className="text-3xl font-bold text-blue-600">+{fmt(finalAudioPrices.systemVoice)}</span>
                      <span className="ml-1 text-xs text-muted-foreground">/ kitap</span>
                    </div>
                    <ul className="flex-1 space-y-1.5">
                      {["Kadın veya erkek ses seçeneği", "Doğal ve akıcı AI anlatım", "Tüm cihazlarda dinleme", "Sınırsız tekrar dinleme"].map(f => (
                        <li key={f} className="flex items-center gap-1.5 text-xs">
                          <Check className="h-3.5 w-3.5 shrink-0 text-blue-500" />{f}
                        </li>
                      ))}
                    </ul>
                  </div>
                  {/* Bottom strip */}
                  <div className="bg-gradient-to-r from-blue-500 to-cyan-500 px-4 py-1 text-center text-[11px] font-medium text-white/80">
                    Sipariş sırasında eklenebilir
                  </div>
                </div>

                {/* Cloned Voice Card */}
                <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border-2 border-purple-200 bg-white shadow-xl">
                  {/* Top strip */}
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-2 text-center text-sm font-bold text-white">
                    🎤 Klon Ses · Prömiyem
                  </div>
                  <div className="flex flex-1 flex-col p-5">
                    <div className="mb-3 flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-100">
                        <Mic className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold">Özel Klon Ses</h4>
                        <p className="text-[11px] text-muted-foreground">Kendi sesinizle anlatım</p>
                      </div>
                    </div>
                    <div className="mb-3">
                      <span className="text-3xl font-bold text-purple-600">+{fmt(finalAudioPrices.clonedVoice)}</span>
                      <span className="ml-1 text-xs text-muted-foreground">/ kitap</span>
                    </div>
                    <ul className="flex-1 space-y-1.5">
                      {["Kendi sesinizle hikaye okuma", "AI ses klonlama teknolojisi", "Tüm cihazlarda dinleme", "En kişisel hediye deneyimi"].map(f => (
                        <li key={f} className="flex items-center gap-1.5 text-xs">
                          <Check className="h-3.5 w-3.5 shrink-0 text-purple-500" />{f}
                        </li>
                      ))}
                    </ul>
                  </div>
                  {/* Bottom strip */}
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-1 text-center text-[11px] font-medium text-white/80">
                    Sipariş sırasında eklenebilir
                  </div>
                </div>
              </div>

              {/* ── COL 3: Coloring Book ── */}
              {coloringBook ? (
                <div className="relative flex flex-col overflow-hidden rounded-2xl border-2 border-emerald-200 bg-white shadow-xl">
                  {/* Top strip */}
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-2.5 text-center text-sm font-bold text-white">
                    {coloringBook.promo_badge || "🎨 Boyama Kitabı"}
                  </div>

                  <div className="flex flex-1 flex-col p-6">
                    <div className="mb-4">
                      <div className="mb-1 flex items-center gap-2">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-100">
                          <Palette className="h-5 w-5 text-emerald-600" />
                        </div>
                        <h3 className="text-xl font-bold">{coloringBook.name}</h3>
                      </div>
                      <p className="ml-11 text-xs font-medium text-emerald-600">✨ Hikaye kitabından türetilir</p>
                      <p className="ml-11 mt-0.5 text-xs text-muted-foreground">
                        {coloringBook.default_page_count} Sayfa • {coloringBook.cover_type}
                      </p>
                    </div>

                    {/* Price */}
                    <div className="mb-4">
                      {coloringBook.discounted_price && (
                        <div className="mb-1 flex items-center gap-2">
                          <span className="text-base text-muted-foreground line-through">{fmt(coloringBook.base_price)}</span>
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-600">
                            %{discountPct(coloringBook.base_price, coloringBook.discounted_price)} İndirim
                          </span>
                        </div>
                      )}
                      <div className="text-4xl font-bold tracking-tight text-emerald-600">
                        {fmt(coloringBook.discounted_price ?? coloringBook.base_price)}
                      </div>
                      <p className="mt-0.5 text-xs text-muted-foreground">Hikaye kitabına ek olarak</p>
                    </div>

                    {/* Features */}
                    <ul className="mb-4 flex-1 space-y-1.5">
                      {(coloringBook.feature_list.length > 0 ? coloringBook.feature_list : DEFAULT_FEATURES_COLORING).map(f => (
                        <li key={f} className="flex items-start gap-2 text-sm">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" /><span>{f}</span>
                        </li>
                      ))}
                    </ul>

                    {/* CTA */}
                    <Link href="/create-v2">
                      <Button variant="outline" className="w-full gap-2 border-emerald-300 text-emerald-700 font-bold hover:bg-emerald-50">
                        Beraber Sipariş Ver <ArrowRight className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>

                  {/* Bottom strip */}
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-1.5 text-center text-[11px] font-medium text-white/80">
                    Sipariş sırasında hikaye kitabına eklenir
                  </div>
                </div>
              ) : (
                /* Fallback: Boyama kitabı yoksa placeholder */
                <div className="relative flex flex-col overflow-hidden rounded-2xl border-2 border-emerald-200 bg-white shadow-xl">
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-2.5 text-center text-sm font-bold text-white">
                    🎨 Boyama Kitabı
                  </div>
                  <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
                    <Palette className="mb-3 h-12 w-12 text-emerald-400" />
                    <p className="font-semibold text-emerald-700">Boyama Kitabı</p>
                    <p className="mt-1 text-sm text-muted-foreground">Yakında eklenecek</p>
                  </div>
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-1.5 text-center text-[11px] font-medium text-white/80">
                    Çok yakında
                  </div>
                </div>
              )}
            </div>

            <p className="mt-6 text-center text-xs text-muted-foreground">
              Sesli okuma ve boyama kitabı, sipariş sırasında hikaye kitabına ek olarak seçilebilir. Tüm fiyatlar KDV dahildir.
            </p>
          </div>
        ) : (
          /* Fallback: old single product card */
          <div className="mx-auto mb-16 max-w-2xl">
            <div className="relative overflow-hidden rounded-2xl border-2 border-primary/20 bg-card shadow-xl">
              <div className="bg-primary px-4 py-2 text-center text-sm font-semibold text-primary-foreground">
                {data?.badge_text || "En Popüler Seçim"}
              </div>
              <div className="p-8">
                <div className="mb-4 flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-primary" />
                  <h3 className="text-2xl font-bold">{data?.package_name ?? "Kişiye Özel Masal Kitabı"}</h3>
                </div>
                <div className="text-3xl font-bold">{data?.price_text ?? "Uygun fiyatlarla"}</div>
                <div className="mt-6 grid gap-2 sm:grid-cols-2">
                  {(data?.included ?? DEFAULT_FEATURES_STORY).map(item => (
                    <div key={item} className="flex items-start gap-2.5 text-sm">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" /><span>{item}</span>
                    </div>
                  ))}
                </div>
                <Link href={data?.cta_url ?? "/create-v2"} className="mt-6 block">
                  <Button size="lg" className="magic-button w-full gap-2 text-base">
                    {data?.cta_text ?? "Hemen Sipariş Ver"} <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Payment methods */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Image src="/images/payment/iyzico_ile_ode_colored.svg" alt="iyzico" width={80} height={28} className="h-7 w-auto" />
          </div>
          <div className="flex items-center gap-2">
            <Image src="/images/payment/logo_band_colored.svg" alt="Visa, Mastercard, Troy" width={160} height={16} className="h-4 w-auto" />
          </div>
          <span>256-bit SSL ile korunan güvenli ödeme</span>
          <span className="text-xs">Tüm fiyatlar KDV dahil Türk Lirası (TL) cinsindendir.</span>
        </div>
      </div>
    </section>
  );
}
