"use client";

import { useState, useRef, forwardRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import HTMLFlipBook from "react-pageflip";
import {
  Check,
  Sparkles,
  FileText,
  Shield,
  Ruler,
  BookOpen,
  Leaf,
  Baby,
  Award,
  Star,
  Crown,
  ChevronRight,
  ChevronLeft,
  Truck,
  Clock,
  Heart,
  Zap,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";

// Types
interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  short_description: string | null;
  cover_width_mm: number | null;
  cover_height_mm: number | null;
  inner_width_mm: number | null;
  inner_height_mm: number | null;
  default_page_count: number;
  base_price: number;
  extra_page_price: number;
  paper_type: string;
  paper_finish?: string;
  cover_type: string;
  thumbnail_url: string | null;
  is_featured: boolean;
  // Extended/Marketing fields
  sample_images?: string[];
  orientation?: "portrait" | "landscape";
  originalPrice?: number;
  badge?: string;
  marketingLine?: string;
  paperWeight?: string;
  coverFinish?: string;
}

interface ProductFormatSelectorProps {
  products: Product[];
  selectedProduct: string;
  onSelect: (productId: string) => void;
  onContinue: () => void;
}

// ============ BOOK PAGE COMPONENT ============
const BookPage = forwardRef<
  HTMLDivElement,
  {
    children: React.ReactNode;
    iscover?: boolean;
    bgColor?: string;
  }
>(({ children, iscover, bgColor }, ref) => {
  return (
    <div
      ref={ref}
      className={`h-full w-full ${iscover ? "" : "bg-white"}`}
      style={{ backgroundColor: bgColor }}
    >
      {children}
    </div>
  );
});
BookPage.displayName = "BookPage";

// ============ INTERACTIVE BOOK PREVIEW ============
function InteractiveBookPreview({
  product,
  isSelected: _isSelected,
  isHovered,
}: {
  product: Product;
  isSelected: boolean;
  isHovered: boolean;
}) {
  // react-page-flip attaches pageFlip() to the div ref
  const bookRef = useRef<
    | (HTMLDivElement & {
        pageFlip?: () => { flip: (n: number) => void; flipNext: () => void; flipPrev: () => void };
      })
    | null
  >(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [isFlipping, setIsFlipping] = useState(false);

  // Calculate dimensions based on product or default to landscape A4
  const width = product.inner_width_mm || 297;
  const height = product.inner_height_mm || 210;
  const isLandscape = width > height;

  // Scale for display (max 280px width for the spread)
  const maxWidth = 260;
  const scale = maxWidth / width;
  const displayWidth = Math.round(width * scale);
  const displayHeight = Math.round(height * scale);

  // Sample pages content
  const samplePages = product.sample_images?.length
    ? product.sample_images
    : [
        null, // Cover
        null, // Page 1
        null, // Page 2
        null, // Page 3
        null, // Back cover
      ];

  // Auto-flip effect on hover
  useEffect(() => {
    if (isHovered && !isFlipping && currentPage === 0) {
      const timer = setTimeout(() => {
        if (bookRef.current?.pageFlip) {
          bookRef.current.pageFlip().flipNext();
          setIsFlipping(true);
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isHovered, isFlipping, currentPage]);

  // Reset when not hovered
  useEffect(() => {
    if (!isHovered && currentPage > 0) {
      const timer = setTimeout(() => {
        bookRef.current?.pageFlip?.().flip(0);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isHovered, currentPage]);

  const handlePageFlip = (e: { data: number }) => {
    setCurrentPage(e.data);
    setIsFlipping(false);
  };

  const flipNext = (e: React.MouseEvent) => {
    e.stopPropagation();
    bookRef.current?.pageFlip?.().flipNext();
  };

  const flipPrev = (e: React.MouseEvent) => {
    e.stopPropagation();
    bookRef.current?.pageFlip?.().flipPrev();
  };

  return (
    <div className="relative flex flex-col items-center">
      {/* Book Container with 3D perspective */}
      <div className="relative" style={{ perspective: "1200px" }}>
        {/* Book Shadow */}
        <div
          className="absolute -bottom-3 left-1/2 -translate-x-1/2 rounded-[50%] opacity-30"
          style={{
            width: displayWidth * 2 + 20,
            height: 16,
            background: "radial-gradient(ellipse at center, rgba(0,0,0,0.6) 0%, transparent 70%)",
            filter: "blur(4px)",
          }}
        />

        {/* Book Spine (when closed) */}
        <motion.div
          animate={{
            scaleX: currentPage > 0 ? 0.5 : 1,
            opacity: currentPage > 0 ? 0.5 : 1,
          }}
          className="absolute left-1/2 top-0 z-20 -translate-x-1/2 rounded-sm bg-gradient-to-r from-amber-800 via-amber-700 to-amber-800"
          style={{
            width: 8,
            height: displayHeight,
            boxShadow: "inset 0 0 8px rgba(0,0,0,0.4)",
          }}
        />

        {/* Flipbook */}
        <div
          className="relative overflow-visible"
          style={{
            transformStyle: "preserve-3d",
          }}
        >
          <HTMLFlipBook
            ref={bookRef}
            width={displayWidth}
            height={displayHeight}
            size="fixed"
            minWidth={displayWidth}
            maxWidth={displayWidth}
            minHeight={displayHeight}
            maxHeight={displayHeight}
            showCover={true}
            mobileScrollSupport={false}
            className="book-preview"
            style={{}}
            startPage={0}
            drawShadow={true}
            flippingTime={600}
            usePortrait={!isLandscape}
            startZIndex={0}
            autoSize={false}
            maxShadowOpacity={0.5}
            showPageCorners={true}
            disableFlipByClick={false}
            swipeDistance={30}
            clickEventForward={false}
            useMouseEvents={true}
            onFlip={handlePageFlip}
          >
            {/* Cover */}
            <BookPage iscover>
              <div
                className="h-full w-full overflow-hidden rounded-r-lg"
                style={{
                  background: product.thumbnail_url
                    ? `url(${product.thumbnail_url}) center/cover`
                    : "linear-gradient(135deg, #9333ea 0%, #ec4899 50%, #f97316 100%)",
                  boxShadow: "inset -2px 0 8px rgba(0,0,0,0.2)",
                }}
              >
                {!product.thumbnail_url && (
                  <div className="flex h-full w-full flex-col items-center justify-center p-4 text-white">
                    <BookOpen className="mb-2 h-8 w-8" />
                    <p className="text-center text-xs font-bold leading-tight">{product.name}</p>
                  </div>
                )}
                {/* Gold foil effect */}
                <div className="absolute bottom-3 left-3 right-3 h-1 rounded-full bg-gradient-to-r from-yellow-400 via-yellow-200 to-yellow-400 opacity-80" />
              </div>
            </BookPage>

            {/* Inner Pages — kapak (index 0) hariç tüm sample_images dinamik olarak göster */}
            {Array.from(
              { length: Math.max(samplePages.length - 1, 4) },
              (_, i) => i + 1
            ).map((pageNum) => (
              <BookPage key={pageNum}>
                <div className="flex h-full w-full flex-col items-center justify-center border-l border-amber-100 bg-amber-50 p-3">
                  {samplePages[pageNum] ? (
                    <img
                      src={samplePages[pageNum] as string}
                      alt={`Sayfa ${pageNum}`}
                      className="h-full w-full rounded object-cover"
                    />
                  ) : (
                    <>
                      <div className="mb-2 flex h-2/3 w-full items-center justify-center rounded-lg bg-gradient-to-br from-purple-100 to-pink-100">
                        <Sparkles className="h-6 w-6 text-purple-300" />
                      </div>
                      <div className="w-full space-y-1.5">
                        <div className="h-2 w-full rounded-full bg-gray-200" />
                        <div className="h-2 w-4/5 rounded-full bg-gray-200" />
                        <div className="h-2 w-3/5 rounded-full bg-gray-200" />
                      </div>
                      <p className="mt-2 text-[8px] text-gray-400">Sayfa {pageNum}</p>
                    </>
                  )}
                </div>
              </BookPage>
            ))}

            {/* Back Cover */}
            <BookPage iscover>
              <div
                className="h-full w-full rounded-l-lg"
                style={{
                  background: "linear-gradient(135deg, #6b21a8 0%, #9333ea 100%)",
                  boxShadow: "inset 2px 0 8px rgba(0,0,0,0.2)",
                }}
              >
                <div className="flex h-full w-full items-center justify-center">
                  <div className="text-center text-xs text-white/60">
                    <Heart className="mx-auto mb-1 h-5 w-5" />
                    <p>BenimMasalım</p>
                  </div>
                </div>
              </div>
            </BookPage>
          </HTMLFlipBook>
        </div>

        {/* Navigation Arrows - visible on hover */}
        <AnimatePresence>
          {isHovered && (
            <>
              <motion.button
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                onClick={flipPrev}
                className="absolute left-0 top-1/2 z-30 flex h-8 w-8 -translate-x-4 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 shadow-lg hover:bg-white"
              >
                <ChevronLeft className="h-4 w-4 text-gray-700" />
              </motion.button>
              <motion.button
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                onClick={flipNext}
                className="absolute right-0 top-1/2 z-30 flex h-8 w-8 -translate-y-1/2 translate-x-4 items-center justify-center rounded-full bg-white/90 shadow-lg hover:bg-white"
              >
                <ChevronRight className="h-4 w-4 text-gray-700" />
              </motion.button>
            </>
          )}
        </AnimatePresence>
      </div>

      {/* Size Badge */}
      <div className="mt-4 flex items-center gap-2">
        <div className="inline-flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-1.5 shadow-sm backdrop-blur-sm">
          <Ruler className="h-3.5 w-3.5 text-purple-500" />
          <span className="text-sm font-medium text-gray-700">
            {Math.round(width / 10)}×{Math.round(height / 10)} cm
          </span>
        </div>
        {isLandscape && (
          <span className="rounded-full bg-purple-100 px-2 py-1 text-xs text-purple-600">
            Yatay
          </span>
        )}
      </div>

      {/* Flip hint */}
      {isHovered && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-2 flex items-center gap-1 text-xs text-gray-400"
        >
          <Eye className="h-3 w-3" />
          Sayfaları çevirmek için tıklayın
        </motion.p>
      )}
    </div>
  );
}

// ============ TRUST BADGE ============
function TrustBadge({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: React.ElementType;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-gray-100 bg-white p-3 shadow-sm">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-green-100 to-emerald-100">
        <Icon className="h-5 w-5 text-green-600" />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-800">{title}</p>
        <p className="text-xs text-gray-500">{subtitle}</p>
      </div>
    </div>
  );
}

// ============ MAIN COMPONENT ============
export default function ProductFormatSelector({
  products,
  selectedProduct,
  onSelect,
  onContinue,
}: ProductFormatSelectorProps) {
  const [hoveredProduct, setHoveredProduct] = useState<string | null>(null);

  // Sort products: featured first
  const sortedProducts = [...products].sort((a, b) => {
    if (a.is_featured && !b.is_featured) return -1;
    if (!a.is_featured && b.is_featured) return 1;
    return 0;
  });

  // Get extended product data with marketing info
  const getExtendedProduct = (product: Product): Product => {
    const isA4 =
      product.name.toLowerCase().includes("a4") || product.name.toLowerCase().includes("dev");
    const _isSquare = product.name.toLowerCase().includes("kare");

    return {
      ...product,
      paperWeight: product.paper_type || (isA4 ? "170gr Premium Saten" : "150gr Saten Mat"),
      coverFinish:
        product.paper_finish ||
        product.cover_type ||
        (isA4 ? "Sert Kapak + Altın Folyo" : "Yumuşak Kapak"),
      marketingLine:
        product.short_description ||
        (isA4 ? "Ömür boyu saklanacak bir hazine" : "Kompakt ve şirin, raf için ideal"),
      originalPrice: isA4 ? 750 : 550,
      badge: product.is_featured ? "En Çok Satan" : undefined,
    };
  };

  return (
    <div className="space-y-4">
      {/* Hero Section */}
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-purple-100 to-pink-100 px-4 py-2"
        >
          <Crown className="h-4 w-4 text-purple-600" />
          <span className="text-sm font-medium text-purple-700">Premium Kalite, El Yapımı</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-r from-gray-800 via-purple-700 to-pink-600 bg-clip-text text-2xl font-bold text-transparent md:text-3xl"
        >
          Kitabınızın Formatını Seçin
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mx-auto mt-3 max-w-lg text-gray-600"
        >
          Her kitap özenle hazırlanır ve kaliteli malzemelerle üretilir. Çocuğunuza özel bir hazine
          yaratın.
        </motion.p>
      </div>

      {/* Products Grid */}
      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-5 lg:grid-cols-2">
        {sortedProducts.map((product, index) => {
          const extended = getExtendedProduct(product);
          const isSelected = selectedProduct === product.id;
          const isHovered = hoveredProduct === product.id;
          const isFeatured = product.is_featured;

          return (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.15 + 0.3 }}
              onMouseEnter={() => setHoveredProduct(product.id)}
              onMouseLeave={() => setHoveredProduct(null)}
              onClick={() => onSelect(product.id)}
              className="relative cursor-pointer"
            >
              {/* Featured Glow */}
              {isFeatured && (
                <div className="absolute -inset-2 rounded-3xl bg-gradient-to-r from-purple-500 via-pink-500 to-orange-400 opacity-20 blur-xl" />
              )}

              <motion.div
                whileHover={{ y: -6 }}
                whileTap={{ scale: 0.98 }}
                className={`relative overflow-hidden rounded-2xl border-2 bg-white transition-all duration-300 ${
                  isSelected
                    ? "border-purple-500 shadow-2xl shadow-purple-200"
                    : isFeatured
                      ? "border-purple-200 shadow-lg hover:border-purple-300 hover:shadow-xl"
                      : "border-gray-200 shadow-md hover:border-gray-300 hover:shadow-lg"
                }`}
              >
                {/* Badge */}
                {extended.badge && (
                  <div className="absolute right-4 top-4 z-10">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.5, type: "spring" }}
                      className="flex items-center gap-1 rounded-full bg-gradient-to-r from-yellow-400 to-orange-400 px-3 py-1 text-xs font-bold text-white shadow-lg"
                    >
                      <Star className="h-3 w-3 fill-current" />
                      {extended.badge}
                    </motion.div>
                  </div>
                )}

                {/* Selected Checkmark */}
                <AnimatePresence>
                  {isSelected && (
                    <motion.div
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0, opacity: 0 }}
                      className="absolute left-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg"
                    >
                      <Check className="h-5 w-5 text-white" strokeWidth={3} />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Book Preview Area */}
                <div
                  className={`relative px-4 py-8 ${
                    isFeatured
                      ? "bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50"
                      : "bg-gradient-to-br from-gray-50 to-gray-100"
                  }`}
                >
                  <InteractiveBookPreview
                    product={product}
                    isSelected={isSelected}
                    isHovered={isHovered}
                  />
                </div>

                {/* Product Info */}
                <div className="p-5">
                  <h3 className={`font-bold ${isFeatured ? "text-xl" : "text-lg"} text-gray-800`}>
                    {product.name}
                  </h3>

                  {extended.marketingLine && (
                    <p
                      className={`mt-1 text-sm ${isFeatured ? "font-medium text-purple-600" : "text-gray-500"}`}
                    >
                      {extended.marketingLine}
                    </p>
                  )}

                  {/* Specs */}
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <div
                        className={`flex h-6 w-6 items-center justify-center rounded-full ${isFeatured ? "bg-purple-100" : "bg-gray-100"}`}
                      >
                        <FileText
                          className={`h-3.5 w-3.5 ${isFeatured ? "text-purple-600" : "text-gray-500"}`}
                        />
                      </div>
                      <span>{extended.paperWeight}</span>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <div
                        className={`flex h-6 w-6 items-center justify-center rounded-full ${isFeatured ? "bg-purple-100" : "bg-gray-100"}`}
                      >
                        <Shield
                          className={`h-3.5 w-3.5 ${isFeatured ? "text-purple-600" : "text-gray-500"}`}
                        />
                      </div>
                      <span>{extended.coverFinish}</span>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <div
                        className={`flex h-6 w-6 items-center justify-center rounded-full ${isFeatured ? "bg-purple-100" : "bg-gray-100"}`}
                      >
                        <BookOpen
                          className={`h-3.5 w-3.5 ${isFeatured ? "text-purple-600" : "text-gray-500"}`}
                        />
                      </div>
                      <span>{product.default_page_count} Sayfa</span>
                      {isFeatured && (
                        <span className="ml-auto rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
                          +8 Ekstra
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Pricing */}
                  <div className="mt-5 border-t border-gray-100 pt-4">
                    <div className="flex items-end justify-between">
                      <div>
                        {extended.originalPrice && extended.originalPrice > product.base_price && (
                          <div className="mb-1 flex items-center gap-2">
                            <span className="text-sm text-gray-400 line-through">
                              {extended.originalPrice} TL
                            </span>
                            <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">
                              %{Math.round((1 - product.base_price / extended.originalPrice) * 100)}{" "}
                              İndirim
                            </span>
                          </div>
                        )}
                        <div className="flex items-baseline gap-1">
                          <span
                            className={`font-bold ${isFeatured ? "text-3xl text-purple-600" : "text-2xl text-gray-800"}`}
                          >
                            {product.base_price}
                          </span>
                          <span className="text-gray-500">TL</span>
                        </div>
                      </div>

                      <motion.div
                        animate={{ scale: isSelected ? 1.1 : 1 }}
                        className={`flex h-10 w-10 items-center justify-center rounded-full transition-colors ${
                          isSelected
                            ? "bg-gradient-to-r from-purple-500 to-pink-500"
                            : isFeatured
                              ? "bg-purple-100 hover:bg-purple-200"
                              : "bg-gray-100 hover:bg-gray-200"
                        }`}
                      >
                        {isSelected ? (
                          <Check className="h-5 w-5 text-white" />
                        ) : (
                          <ChevronRight
                            className={`h-5 w-5 ${isFeatured ? "text-purple-600" : "text-gray-500"}`}
                          />
                        )}
                      </motion.div>
                    </div>
                  </div>

                  {/* Select Button */}
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelect(product.id);
                    }}
                    className={`mt-4 flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 font-semibold transition-all ${
                      isSelected
                        ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-200"
                        : isFeatured
                          ? "bg-purple-100 text-purple-700 hover:bg-purple-200"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    {isSelected ? (
                      <>
                        <Check className="h-5 w-5" />
                        Seçildi
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-5 w-5" />
                        Bu Formatı Seç
                      </>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            </motion.div>
          );
        })}
      </div>

      {/* Trust Badges */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="mx-auto max-w-4xl"
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <TrustBadge
            icon={Leaf}
            title="Çevre Dostu Kağıt"
            subtitle="FSC Sertifikalı, %100 geri dönüştürülebilir"
          />
          <TrustBadge
            icon={Baby}
            title="Çocuk Güvenli Mürekkep"
            subtitle="Toksik olmayan, EN71 onaylı"
          />
          <TrustBadge
            icon={Award}
            title="%100 Memnuniyet"
            subtitle="Beğenmezseniz iade garantisi"
          />
        </div>
      </motion.div>

      {/* Additional Info Strip */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="flex flex-wrap justify-center gap-6 text-sm text-gray-500"
      >
        <div className="flex items-center gap-2">
          <Truck className="h-4 w-4" />
          <span>Ücretsiz Kargo</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          <span>3-5 İş Günü Teslimat</span>
        </div>
        <div className="flex items-center gap-2">
          <Heart className="h-4 w-4" />
          <span>Elle Paketlenir</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4" />
          <span>Aynı Gün Üretim</span>
        </div>
      </motion.div>

      {/* Continue Button */}
      <div className="flex justify-center pt-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="w-full max-w-md"
        >
          <Button
            onClick={onContinue}
            disabled={!selectedProduct}
            className="w-full bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 py-6 text-lg font-bold shadow-lg shadow-purple-200 hover:from-purple-700 hover:via-pink-600 hover:to-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {selectedProduct ? (
              <>
                Devam Et
                <ChevronRight className="ml-2 h-5 w-5" />
              </>
            ) : (
              "Bir Format Seçin"
            )}
          </Button>

          {selectedProduct && (
            <p className="mt-3 text-center text-sm text-gray-500">
              Seçiminizi sonraki adımlarda değiştirebilirsiniz
            </p>
          )}
        </motion.div>
      </div>
    </div>
  );
}
