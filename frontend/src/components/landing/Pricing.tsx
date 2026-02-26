import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  Check,
  ArrowRight,
  BookOpen,
  Mic,
  Star,
  Sparkles,
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
  products?: CategorizedProducts | ProductData[]; // Support both old and new formats
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

/* ─── Audio Addon Pricing ───────────────────────────────────── */

const AUDIO_ADDONS = [
  {
    id: "system",
    name: "Standart Sesli Kitap",
    price: 150,
    icon: Volume2,
    color: "from-blue-500 to-cyan-500",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    description: "Profesyonel AI ses teknolojisi ile oluşturulan sesli hikaye",
    features: [
      "Kadın veya erkek ses seçeneği",
      "Doğal ve akıcı anlatım",
      "Tüm cihazlarda dinleme",
      "Sınırsız tekrar dinleme",
    ],
  },
  {
    id: "cloned",
    name: "Özel Klon Ses",
    price: 300,
    icon: Mic,
    color: "from-purple-500 to-pink-500",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    badge: "Prömiyem",
    description: "Ebeveynin kendi sesiyle okunan kişiselleştirilmiş hikaye",
    features: [
      "Kendi sesinizle anlatım",
      "AI ses klonlama teknolojisi",
      "Tüm cihazlarda dinleme",
      "En kişisel hediye deneyimi",
    ],
  },
];

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
  "Ayrı fiziksel kitap",
  "Metin yok, sadece boyama",
  "Yaratıcılığı geliştiren aktivite",
  "Hikaye kitabıyla uyumlu",
];

/* ─── Helpers ───────────────────────────────────────────────── */

function formatPrice(price: number): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
}

function discountPercentage(base: number, discounted: number): number {
  return Math.round(((base - discounted) / base) * 100);
}

/* ─── Component ─────────────────────────────────────────────── */

// Helper: Product Card Component
function ProductCard({
  product,
  badge,
  icon: Icon,
  parentInfo,
  defaultFeatures,
}: {
  product: ProductData;
  badge?: string;
  icon: any;
  parentInfo?: string;
  defaultFeatures: string[];
}) {
  const displayPrice = product.discounted_price ?? product.base_price;
  const originalPrice = product.discounted_price ? product.base_price : null;
  const features = product.feature_list.length > 0 ? product.feature_list : defaultFeatures;

  return (
    <div className="relative overflow-hidden rounded-2xl border-2 border-primary/20 bg-card shadow-xl">
      {/* Badge */}
      <div className="bg-primary px-4 py-2 text-center text-sm font-semibold text-primary-foreground">
        {badge || product.promo_badge || "Özel Ürün"}
      </div>

      <div className="p-8">
        <div className="mb-6">
          {/* Icon & Title */}
          <div className="mb-2 flex items-center gap-2">
            <Icon className="h-5 w-5 text-primary" />
            <h3 className="text-2xl font-bold">{product.name}</h3>
          </div>

          {/* Parent Info (for coloring book) */}
          {parentInfo && (
            <p className="mb-2 text-sm text-purple-600 font-medium">{parentInfo}</p>
          )}

          <p className="text-sm text-muted-foreground">
            {product.default_page_count} Sayfa • {product.cover_type} • {product.paper_type}
          </p>

          {/* Rating */}
          {(product.rating ?? 0) > 0 && (
            <div className="mt-3 flex items-center gap-2">
              <div className="flex items-center gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className={`h-4 w-4 ${i < Math.round(product.rating ?? 0)
                        ? "fill-amber-400 text-amber-400"
                        : "text-slate-200"
                      }`}
                  />
                ))}
              </div>
              <span className="text-sm font-medium text-slate-600">
                {product.rating?.toFixed(1)}
              </span>
              {product.review_count > 0 && (
                <span className="text-sm text-muted-foreground">
                  ({product.review_count} değerlendirme)
                </span>
              )}
            </div>
          )}

          {/* Social proof */}
          {product.social_proof_text && (
            <p className="mt-2 text-sm font-medium text-emerald-600">
              {product.social_proof_text}
            </p>
          )}
        </div>

        {/* Price */}
        <div className="mb-6">
          {originalPrice && (
            <div className="mb-1">
              <span className="text-lg text-muted-foreground line-through">
                {formatPrice(originalPrice)}
              </span>
              <span className="ml-2 inline-block rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-600">
                %{discountPercentage(originalPrice, displayPrice)} İndirim
              </span>
            </div>
          )}
          <div className="text-4xl font-bold tracking-tight text-primary">
            {formatPrice(displayPrice)}
          </div>
          {product.extra_page_price > 0 && (
            <p className="mt-1 text-xs text-muted-foreground">
              Ek sayfa: +{formatPrice(product.extra_page_price)} / sayfa
            </p>
          )}
        </div>

        {/* Features */}
        <div className="mb-6 space-y-2">
          {features.map((item) => (
            <div key={item} className="flex items-start gap-2.5 text-sm">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
              <span>{item}</span>
            </div>
          ))}
        </div>

        {/* Free shipping */}
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-700">
          <Truck className="h-4 w-4" />
          Ücretsiz kargo ile kapınıza kadar teslimat
        </div>

        {/* CTA */}
        <Link href="/create-v2">
          <Button size="lg" className="magic-button w-full gap-2 text-base">
            Hemen Sipariş Ver
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </div>
  );
}

export default function Pricing({ title, subtitle, products, data }: PricingProps) {
  const heading = title ?? "Fiyatlandırma";
  const sub =
    subtitle ??
    "Şeffaf fiyatlandırma, gizli maliyet yok. Çocuğunuza özel bir hikaye kitabı oluşturun.";

  // Handle both old (array) and new (categorized) product formats
  const categorized: CategorizedProducts = Array.isArray(products)
    ? {
      storyBooks: products.filter(p => p.product_type === 'story_book' || !p.product_type),
      coloringBooks: products.filter(p => p.product_type === 'coloring_book'),
      audioAddons: products.filter(p => p.product_type === 'audio_addon'),
      all: products,
    }
    : (products ?? { storyBooks: [], coloringBooks: [], audioAddons: [], all: [] });

  const storyBook = categorized.storyBooks[0];
  const coloringBook = categorized.coloringBooks[0];
  const hasProducts = storyBook || coloringBook;

  return (
    <section id="fiyat" className="scroll-mt-20 bg-gradient-to-b from-slate-50/50 to-white py-20">
      <div className="container">
        {/* Header */}
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
        </div>

        {/* ── Main Products Grid (Story + Coloring) ──────────────── */}
        {hasProducts ? (
          <div className="mx-auto mb-16 max-w-6xl">
            <div className="grid gap-8 lg:grid-cols-2">
              {/* Story Book Card */}
              {storyBook && (
                <ProductCard
                  product={storyBook}
                  badge="En Popüler"
                  icon={BookOpen}
                  defaultFeatures={DEFAULT_FEATURES_STORY}
                />
              )}

              {/* Coloring Book Card */}
              {coloringBook && (
                <ProductCard
                  product={coloringBook}
                  badge="Yeni!"
                  icon={Palette}
                  parentInfo="✨ Hikaye kitabından türetilir"
                  defaultFeatures={DEFAULT_FEATURES_COLORING}
                />
              )}
            </div>
          </div>
        ) : (
          /* Fallback: Old single product card */
          <div className="mx-auto mb-16 max-w-2xl">
            <div className="relative overflow-hidden rounded-2xl border-2 border-primary/20 bg-card shadow-xl">
              <div className="bg-primary px-4 py-2 text-center text-sm font-semibold text-primary-foreground">
                {data?.badge_text || "En Popüler Seçim"}
              </div>
              <div className="p-8 sm:p-10">
                <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <div className="mb-2 flex items-center gap-2">
                      <BookOpen className="h-5 w-5 text-primary" />
                      <h3 className="text-2xl font-bold">
                        {data?.package_name ?? "Kişiye Özel Masal Kitabı"}
                      </h3>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {data?.package_description ?? "Çocuğunuzun kahramanı olduğu benzersiz hikaye kitabı"}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold tracking-tight">
                      {data?.price_text ?? "Uygun fiyatlarla"}
                    </div>
                  </div>
                </div>
                <div className="mt-8 grid gap-2 sm:grid-cols-2">
                  {(data?.included ?? DEFAULT_FEATURES_STORY).map((item) => (
                    <div key={item} className="flex items-start gap-2.5 text-sm">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
                <Link href={data?.cta_url ?? "/create"} className="mt-6 block">
                  <Button size="lg" className="magic-button w-full gap-2 text-base">
                    {data?.cta_text ?? "Hemen Sipariş Ver"}
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* ── Audio Addon Section ──────────────────────────────── */}
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-purple-100">
              <Sparkles className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-2xl font-bold">Ek Seçenekler</h3>
            <p className="mt-2 text-muted-foreground">
              Kitabınıza ekstra özellikler ekleyerek deneyimi zenginleştirin
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
            {/* Audio Addons */}
            {AUDIO_ADDONS.map((addon) => {
              const Icon = addon.icon;
              return (
                <div
                  key={addon.id}
                  className={`relative overflow-hidden rounded-xl border-2 ${addon.borderColor} bg-card shadow-md transition-transform hover:scale-[1.02]`}
                >
                  {addon.badge && (
                    <div className={`bg-gradient-to-r ${addon.color} px-4 py-1.5 text-center text-xs font-semibold text-white`}>
                      {addon.badge}
                    </div>
                  )}

                  <div className="p-6">
                    <div className="mb-4 flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${addon.bgColor}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="font-bold">{addon.name}</h4>
                        <p className="text-xs text-muted-foreground">{addon.description}</p>
                      </div>
                    </div>

                    <div className="mb-4">
                      <span className="text-3xl font-bold tracking-tight">
                        +{formatPrice(addon.price)}
                      </span>
                      <span className="ml-1 text-sm text-muted-foreground">/ kitap başı</span>
                    </div>

                    <ul className="space-y-2">
                      {addon.features.map((f) => (
                        <li key={f} className="flex items-start gap-2 text-sm">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            Tüm eklentiler sipariş sırasında seçilebilir. İsteğe bağlıdır.
          </p>
        </div>

        {/* ── Payment security ─────────────────────────────────── */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Image
              src="/images/payment/iyzico_ile_ode_colored.svg"
              alt="iyzico ile güvenli ödeme"
              width={80}
              height={28}
              className="h-7 w-auto"
            />
          </div>
          <div className="flex items-center gap-2">
            <Image
              src="/images/payment/logo_band_colored.svg"
              alt="Visa, Mastercard, Troy"
              width={160}
              height={16}
              className="h-4 w-auto"
            />
          </div>
          <span>256-bit SSL ile korunan güvenli ödeme</span>
          <span className="text-xs">Tüm fiyatlar KDV dahil Türk Lirası (TL) cinsindendir.</span>
        </div>
      </div>
    </section>
  );
}
