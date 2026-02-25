"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Star,
  Sparkles,
  BookOpen,
  Heart,
  Shield,
  Users,
  Brain,
  ChevronLeft,
  ChevronRight,
  Check,
  X,
  Wand2,
  Flame,
  Clock,
  Gift,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ScenarioDetailModal from "@/components/ScenarioDetailModal";

// Hook for detecting mobile viewport
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  return isMobile;
}

// Types — API returns snake_case (gallery_images); detail panel uses galleryImages
interface Scenario {
  id: string;
  name: string;
  description: string | null;
  theme?: string;
  thumbnail_url: string;
  /** API: kitaptan kareler (backend gallery_images) */
  gallery_images?: string[];
  // V2 fields
  story_prompt_tr?: string | null;
  location_en?: string | null;
  default_page_count?: number | null;
  flags?: Record<string, boolean> | null;
  custom_inputs_schema?: unknown[];
  // Marketing fields from backend
  marketing_video_url?: string | null;
  marketing_gallery?: string[];
  marketing_price_label?: string | null;
  marketing_features?: string[];
  marketing_badge?: string | null;
  age_range?: string | null;
  estimated_duration?: string | null;
  tagline?: string | null;
  rating?: number | null;
  review_count?: number | null;
  // Extended fields for detail panel (merged in getExtendedScenario)
  videoUrl?: string;
  galleryImages?: string[];
  learningOutcomes?: string[];
  reviewCount?: number;
  features?: string[];
}

interface AdventureSelectorProps {
  scenarios: Scenario[];
  selectedScenario: string;
  onSelect: (scenarioId: string) => void;
  onContinue: () => void;
  onBack?: () => void;
  childName?: string;
}

// Mock extended data for scenarios (will be merged with API data)
const scenarioExtendedData: Record<string, Partial<Scenario>> = {
  kapadokya: {
    tagline: "Sihirli balonlarla gökyüzünde bir macera",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/kapadokya-1.jpg",
      "/scenarios/kapadokya-2.jpg",
      "/scenarios/kapadokya-3.jpg",
      "/scenarios/kapadokya-4.jpg",
    ],
    learningOutcomes: ["Cesaret", "Keşfetme", "Özgüven"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "Kapakta çocuğunuzun fotoğrafı",
      "Kapadokya'nın sihirli manzaraları",
      "Özel peri bacası karakterleri",
    ],
    rating: 4.9,
    reviewCount: 1247,
  },
  yerebatan: {
    tagline: "Antik sütunlar arasında gizemli bir keşif",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/yerebatan-1.jpg",
      "/scenarios/yerebatan-2.jpg",
      "/scenarios/yerebatan-3.jpg",
      "/scenarios/yerebatan-4.jpg",
    ],
    learningOutcomes: ["Cesaret", "Tarih Sevgisi", "Keşfetme"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "Gizemli yeraltı dünyası",
      "Antik Medusa başları",
      "Bizans mühendislik harikası",
    ],
    rating: 4.9,
    reviewCount: 1024,
  },
  gobeklitepe: {
    tagline: "12.000 yıllık gizemli dikilitaşların sırrını çöz",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/gobeklitepe-1.jpg",
      "/scenarios/gobeklitepe-2.jpg",
      "/scenarios/gobeklitepe-3.jpg",
      "/scenarios/gobeklitepe-4.jpg",
    ],
    learningOutcomes: ["Merak", "Keşfetme", "Tarih Sevgisi"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "Dünyanın en eski tapınağı",
      "Dikilitaşlardan canlanan hayvanlar",
      "Arkeolojik gizem ve macera",
    ],
    rating: 4.9,
    reviewCount: 987,
  },
  efes: {
    tagline: "Antik dünyanın en görkemli şehrinde bir macera",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/efes-1.jpg",
      "/scenarios/efes-2.jpg",
      "/scenarios/efes-3.jpg",
      "/scenarios/efes-4.jpg",
    ],
    learningOutcomes: ["Merak", "Bilgelik", "Tarih Sevgisi"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "Celsus Kütüphanesi'nin sırları",
      "Antik mozaiklerden canlanan hikayeler",
      "Ege kıyısında arkeolojik macera",
    ],
    rating: 4.9,
    reviewCount: 876,
  },
  catalhoyuk: {
    tagline: "9.000 yıllık insanlığın ilk şehrinde büyülü bir keşif",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/catalhoyuk-1.jpg",
      "/scenarios/catalhoyuk-2.jpg",
      "/scenarios/catalhoyuk-3.jpg",
      "/scenarios/catalhoyuk-4.jpg",
    ],
    learningOutcomes: ["İş Birliği", "Paylaşmak", "Merak"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "Çatıdan girilen gizemli evler",
      "Canlanan duvar resimleri ve Ana Tanrıça",
      "Neolitik dönemde büyülü macera",
    ],
    rating: 4.9,
    reviewCount: 823,
  },
  sumela: {
    tagline: "Kayalıklara oyulmuş gizemli manastırda büyülü bir keşif",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/sumela-1.jpg",
      "/scenarios/sumela-2.jpg",
      "/scenarios/sumela-3.jpg",
      "/scenarios/sumela-4.jpg",
    ],
    learningOutcomes: ["Cesaret", "Azim", "Doğa Sevgisi"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "1.200 metrede kayalara oyulmuş manastır",
      "Canlanan Bizans freskleri",
      "Karadeniz ormanlarında büyülü macera",
    ],
    rating: 4.9,
    reviewCount: 912,
  },
  sultanahmet: {
    tagline: "20.000 mavi çiniyle süslü muhteşem bir macera",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/sultanahmet-1.jpg",
      "/scenarios/sultanahmet-2.jpg",
      "/scenarios/sultanahmet-3.jpg",
      "/scenarios/sultanahmet-4.jpg",
    ],
    learningOutcomes: ["Sabır", "Estetik", "Merak"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "20.000 İznik çinisi ve lale desenleri",
      "Renkli vitray pencerelerden sihirli ışıklar",
      "İstanbul'un kalbinde sanat macerası",
    ],
    rating: 4.9,
    reviewCount: 1156,
  },
  galata: {
    tagline: "700 yıllık kulede 67 metre yükseklikte İstanbul panoraması",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/galata-1.jpg",
      "/scenarios/galata-2.jpg",
      "/scenarios/galata-3.jpg",
      "/scenarios/galata-4.jpg",
    ],
    learningOutcomes: ["Cesaret", "Merak", "Hayal Gücü"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "Hezârfen Ahmed Çelebi'nin uçuş efsanesi",
      "360° panoramik İstanbul manzarası",
      "Spiral merdivende zaman yolculuğu",
    ],
    rating: 4.9,
    reviewCount: 1089,
  },
  kudus: {
    tagline: "5.000 yıllık surlarla çevrili antik şehirde büyülü bir keşif",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/kudus-1.jpg",
      "/scenarios/kudus-2.jpg",
      "/scenarios/kudus-3.jpg",
      "/scenarios/kudus-4.jpg",
    ],
    learningOutcomes: ["Merak", "Farklılıklara Saygı", "Sabır"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "UNESCO Dünya Mirası antik sur şehri",
      "Sihirli baharat çarşısı ve zanaatkâr atölyeleri",
      "Altın rengi Kudüs taşında zaman yolculuğu",
    ],
    rating: 4.9,
    reviewCount: 945,
  },
  abusimbel: {
    tagline: "3.000 yıllık dev firavun heykelleri ve güneşin sırrı",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/abusimbel-1.jpg",
      "/scenarios/abusimbel-2.jpg",
      "/scenarios/abusimbel-3.jpg",
      "/scenarios/abusimbel-4.jpg",
    ],
    learningOutcomes: ["Merak", "Azim", "Cesaret"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "20 metrelik devasa Ramses heykelleri",
      "Güneş ışığının 60 metrelik büyülü yolculuğu",
      "Canlanan hiyeroglifler ve antik Mısır sırları",
    ],
    rating: 4.9,
    reviewCount: 1034,
  },
  tacmahal: {
    tagline: "Beyaz mermerin pembeye, altına ve gümüşe dönüştüğü büyülü dünya",
    videoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    galleryImages: [
      "/scenarios/tacmahal-1.jpg",
      "/scenarios/tacmahal-2.jpg",
      "/scenarios/tacmahal-3.jpg",
      "/scenarios/tacmahal-4.jpg",
    ],
    learningOutcomes: ["Sabır", "Sevgi", "Merak"],
    features: [
      "Çocuğunuzun adı 12 kez geçiyor",
      "Yarı değerli taş kakma sanatı (pietra dura)",
      "Yansıma havuzundaki ayna dünya",
      "Gün ışığıyla renk değiştiren beyaz mermer",
    ],
    rating: 4.9,
    reviewCount: 1178,
  },
};

// Learning outcome icons
const outcomeIcons: Record<string, React.ReactNode> = {
  Cesaret: <Shield className="h-4 w-4" />,
  Arkadaşlık: <Users className="h-4 w-4" />,
  Yardımlaşma: <Heart className="h-4 w-4" />,
  Merak: <Sparkles className="h-4 w-4" />,
  Keşfetme: <BookOpen className="h-4 w-4" />,
  Özgüven: <Star className="h-4 w-4" />,
  "Bilim Sevgisi": <Brain className="h-4 w-4" />,
  "Problem Çözme": <Brain className="h-4 w-4" />,
  "Doğa Sevgisi": <Heart className="h-4 w-4" />,
  Keşif: <BookOpen className="h-4 w-4" />,
  "Çevre Bilinci": <Heart className="h-4 w-4" />,
};

// Mobile Bottom Sheet Component
function MobileBottomSheet({
  isOpen,
  onClose,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
          />
          {/* Sheet */}
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50 max-h-[90vh] overflow-y-auto rounded-t-3xl bg-white"
          >
            {/* Handle */}
            <div className="sticky top-0 z-10 rounded-t-3xl bg-white pb-2 pt-3">
              <div className="mx-auto h-1.5 w-12 rounded-full bg-gray-300" />
            </div>
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Detail Panel Content Component - Shared between Desktop and Mobile
function DetailPanelContent({
  expandedData,
  galleryIndex,
  setGalleryIndex,
  onContinue,
  isMobile = false,
}: {
  expandedData: Scenario;
  galleryIndex: number;
  setGalleryIndex: (idx: number) => void;
  onContinue: () => void;
  isMobile?: boolean;
}) {
  return (
    <div className={`${isMobile ? "p-3 pb-6" : "p-4 md:p-5"}`}>
      <div
        className={`grid ${isMobile ? "grid-cols-1 gap-4" : "grid-cols-1 gap-5 lg:grid-cols-2"}`}
      >
        {/* Left Column - Visuals */}
        <div className="space-y-3">
          {/* Promo Banner - show only if badge or price label exists */}
          {(expandedData.marketing_badge || expandedData.marketing_price_label) && (
            <div className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-orange-500 to-pink-500 p-2.5 text-white">
              <Flame className="h-5 w-5" />
              <span className="text-sm font-medium">
                {expandedData.marketing_badge || expandedData.marketing_price_label}
              </span>
              {expandedData.estimated_duration && (
                <>
                  <Clock className="ml-auto h-4 w-4" />
                  <span className="text-xs">{expandedData.estimated_duration}</span>
                </>
              )}
            </div>
          )}

          {/* Video Preview */}
          <div className="relative aspect-video overflow-hidden rounded-2xl bg-gradient-to-br from-purple-200 to-pink-200 shadow-inner">
            {expandedData.videoUrl ? (
              <iframe
                src={expandedData.videoUrl}
                className="h-full w-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="flex h-full w-full flex-col items-center justify-center text-purple-400">
                <div className="mb-3 flex h-16 w-16 cursor-pointer items-center justify-center rounded-full bg-white/50 shadow-lg transition hover:bg-white/70">
                  <Play className="ml-1 h-8 w-8 text-purple-500" />
                </div>
                <p className="text-sm font-medium">Hikaye Tanıtımını İzle</p>
              </div>
            )}
          </div>

          {/* Image Gallery */}
          <div className="space-y-3">
            <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700">
              <Sparkles className="h-4 w-4 text-purple-500" />
              Kitaptan Kareler
            </h4>
            <div className="relative">
              {/* Main Gallery Image */}
              <div className="aspect-[4/3] overflow-hidden rounded-xl bg-gradient-to-br from-purple-100 to-pink-100">
                {expandedData.galleryImages?.[galleryIndex] ? (
                  <img
                    src={expandedData.galleryImages[galleryIndex]}
                    alt={`Galeri ${galleryIndex + 1}`}
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "/placeholder.svg";
                    }}
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <span className="text-6xl">
                      {galleryIndex === 0
                        ? "📖"
                        : galleryIndex === 1
                          ? "🎨"
                          : galleryIndex === 2
                            ? "✨"
                            : "🌟"}
                    </span>
                  </div>
                )}
              </div>

              {/* Gallery Navigation */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setGalleryIndex(Math.max(0, galleryIndex - 1));
                }}
                className="absolute left-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 shadow-md backdrop-blur-sm transition hover:bg-white disabled:opacity-50"
                disabled={galleryIndex === 0}
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setGalleryIndex(
                    Math.min((expandedData.galleryImages?.length || 1) - 1, galleryIndex + 1)
                  );
                }}
                className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 shadow-md backdrop-blur-sm transition hover:bg-white disabled:opacity-50"
                disabled={galleryIndex === (expandedData.galleryImages?.length || 1) - 1}
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>

            {/* Gallery Thumbnails */}
            <div className="flex justify-center gap-2">
              {expandedData.galleryImages?.map((_, idx) => (
                <button
                  key={idx}
                  onClick={(e) => {
                    e.stopPropagation();
                    setGalleryIndex(idx);
                  }}
                  className={`h-2 w-2 rounded-full transition-all ${
                    idx === galleryIndex ? "w-6 bg-purple-500" : "bg-gray-300 hover:bg-purple-300"
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Info & CTA */}
        <div className="space-y-5">
          {/* Title & Rating */}
          <div>
            <h3
              className={`${isMobile ? "text-lg" : "text-xl md:text-2xl"} bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text font-bold text-transparent`}
            >
              {expandedData.name}
            </h3>
            <p className="mt-1 text-sm text-gray-600">{expandedData.tagline}</p>

            {/* Rating */}
            <div className="mt-3 flex items-center gap-2">
              <div className="flex">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`h-4 w-4 ${
                      star <= Math.floor(expandedData.rating || 0)
                        ? "fill-yellow-400 text-yellow-400"
                        : "text-gray-300"
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm font-semibold">{expandedData.rating}</span>
              <span className="text-xs text-gray-500">
                ({expandedData.reviewCount?.toLocaleString()} aile)
              </span>
            </div>
          </div>

          {/* Description */}
          <div className="rounded-xl border border-purple-100 bg-white/60 p-3 backdrop-blur-sm">
            <p className="text-sm leading-relaxed text-gray-700">{expandedData.description}</p>
          </div>

          {/* Learning Outcomes */}
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <Brain className="h-4 w-4 text-purple-500" />
              Bu Hikayede Öğrenecekleri
            </h4>
            <div className="flex flex-wrap gap-2">
              {expandedData.learningOutcomes?.map((outcome, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-purple-100 to-pink-100 px-2.5 py-1 text-xs font-medium text-purple-700"
                >
                  {outcomeIcons[outcome] || <Sparkles className="h-3 w-3" />}
                  {outcome}
                </span>
              ))}
            </div>
          </div>

          {/* Features */}
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <BookOpen className="h-4 w-4 text-purple-500" />
              Kitabın İçinde
            </h4>
            <ul className="space-y-1.5">
              {expandedData.features?.map((feature, idx) => (
                <li key={idx} className="flex items-center gap-2 text-gray-600">
                  <div className="flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full bg-green-100">
                    <Check className="h-2.5 w-2.5 text-green-600" />
                  </div>
                  <span className="text-xs">{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Gift Badge */}
          <div className="flex items-center gap-2 rounded-xl border border-purple-100 bg-purple-50 p-2.5">
            <Gift className="h-5 w-5 text-purple-500" />
            <div>
              <p className="text-xs font-medium text-purple-700">Hediye Paketi Dahil</p>
              <p className="text-[10px] text-purple-500">Özel kutu ve teşekkür kartı</p>
            </div>
          </div>

          {/* Social Proof */}
          <div className="flex items-center gap-2 rounded-xl border border-yellow-200 bg-yellow-50 p-2.5 text-sm text-gray-500">
            <div className="flex -space-x-2">
              {["👧", "👦", "👧", "👦"].map((emoji, idx) => (
                <div
                  key={idx}
                  className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-yellow-200 bg-white text-xs"
                >
                  {emoji}
                </div>
              ))}
            </div>
            <span className="ml-1 text-xs">
              <strong className="text-yellow-700">
                {expandedData.reviewCount?.toLocaleString()}+
              </strong>{" "}
              aile bayıldı!
            </span>
          </div>

          {/* CTA Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={(e) => {
              e.stopPropagation();
              onContinue();
            }}
            className={`w-full ${isMobile ? "py-3" : "py-3"} bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 px-5 font-bold text-white ${isMobile ? "text-sm" : "text-base"} flex items-center justify-center gap-2 rounded-xl shadow-lg shadow-purple-300 transition-all hover:shadow-xl hover:shadow-purple-400`}
          >
            <Wand2 className="h-5 w-5" />
            Bu Maceraya Başla
            <Sparkles className="h-5 w-5" />
          </motion.button>
        </div>
      </div>
    </div>
  );
}

export default function AdventureSelector({
  scenarios,
  selectedScenario,
  onSelect,
  onContinue,
  onBack,
  childName = "Çocuğunuz",
}: AdventureSelectorProps) {
  const [expandedScenario, setExpandedScenario] = useState<string | null>(null);
  const [galleryIndex, setGalleryIndex] = useState(0);
  const [modalScenarioId, setModalScenarioId] = useState<string | null>(null);
  const detailRef = useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();

  // Get extended data for a scenario - API marketing fields take priority over mock data
  const getExtendedScenario = (scenario: Scenario): Scenario => {
    // Fallback to mock data only if API marketing fields are missing
    const key = scenario.name.toLowerCase().includes("kapadokya")
      ? "kapadokya"
      : scenario.name.toLowerCase().includes("yerebatan")
        ? "yerebatan"
        : scenario.name.toLowerCase().includes("gobeklitepe") || scenario.name.toLowerCase().includes("göbeklitepe")
          ? "gobeklitepe"
          : scenario.name.toLowerCase().includes("efes")
            ? "efes"
            : scenario.name.toLowerCase().includes("catalhoyuk") || scenario.name.toLowerCase().includes("çatalhöyük")
              ? "catalhoyuk"
              : scenario.name.toLowerCase().includes("sümela") || scenario.name.toLowerCase().includes("sumela")
                ? "sumela"
                : scenario.name.toLowerCase().includes("sultanahmet")
                  ? "sultanahmet"
                  : scenario.name.toLowerCase().includes("galata")
                    ? "galata"
                    : scenario.name.toLowerCase().includes("kudüs") || scenario.name.toLowerCase().includes("kudus")
                      ? "kudus"
                      : scenario.name.toLowerCase().includes("abu simbel") || scenario.name.toLowerCase().includes("abusimbel")
                        ? "abusimbel"
                        : scenario.name.toLowerCase().includes("tac mahal") || scenario.name.toLowerCase().includes("tacmahal")
                          ? "tacmahal"
                          : "";

    const mockData = scenarioExtendedData[key] || {};

    // Gallery: marketing_gallery > gallery_images > mock > thumbnail
    const galleryImages =
      (Array.isArray(scenario.marketing_gallery) && scenario.marketing_gallery.length > 0)
        ? scenario.marketing_gallery
        : (Array.isArray(scenario.gallery_images) && scenario.gallery_images.length > 0)
          ? scenario.gallery_images
          : mockData.galleryImages ?? [scenario.thumbnail_url];

    return {
      ...scenario,
      tagline: scenario.tagline || mockData.tagline || scenario.description || undefined,
      videoUrl: scenario.marketing_video_url || mockData.videoUrl,
      galleryImages,
      learningOutcomes: mockData.learningOutcomes || ["Cesaret", "Arkadaşlık"],
      features: (scenario.marketing_features && scenario.marketing_features.length > 0)
        ? scenario.marketing_features
        : mockData.features || [
            "Çocuğunuzun adı hikayede geçiyor",
            "Özel tasarım kapak",
            "Eğitici içerik",
          ],
      rating: scenario.rating ?? mockData.rating ?? 4.8,
      reviewCount: scenario.review_count ?? mockData.reviewCount ?? 500,
    };
  };

  // Handle card click
  const handleCardClick = (scenarioId: string) => {
    onSelect(scenarioId);
    if (expandedScenario === scenarioId) {
      setExpandedScenario(null);
    } else {
      setExpandedScenario(scenarioId);
      setGalleryIndex(0);
      // Scroll to detail panel after animation
      setTimeout(() => {
        detailRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, 100);
    }
  };

  // Close detail panel
  const handleCloseDetail = () => {
    setExpandedScenario(null);
  };

  // Get expanded scenario data
  const expandedData = expandedScenario
    ? getExtendedScenario(scenarios.find((s) => s.id === expandedScenario)!)
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-4 text-center">
        <h2 className="bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 bg-clip-text text-xl font-bold text-transparent">
          Macera Seçin
        </h2>
        <p className="mt-1 text-sm text-gray-600">{childName} için büyülü bir dünya seçin</p>
      </div>

      {/* Boş macera listesi */}
      {scenarios.length === 0 && (
        <div className="rounded-xl border-2 border-dashed border-purple-200 bg-purple-50/50 p-5 text-center">
          <BookOpen className="mx-auto mb-4 h-14 w-14 text-purple-400" />
          <h3 className="mb-2 font-semibold text-gray-800">Henüz macera yok</h3>
          <p className="mx-auto max-w-md text-sm text-gray-600">
            Şu an seçilebilecek macera eklenmemiş. Yönetici panelinden <strong>Senaryo &amp; İçerik</strong> bölümüne
            macera eklenmesi gerekiyor. Lütfen daha sonra tekrar deneyin veya site yöneticisi ile iletişime geçin.
          </p>
        </div>
      )}

      {/* Adventure Grid - Big Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {scenarios.map((scenario) => {
          const isSelected = selectedScenario === scenario.id;
          const isExpanded = expandedScenario === scenario.id;
          const extended = getExtendedScenario(scenario);

          return (
            <motion.div
              key={scenario.id}
              layoutId={`card-${scenario.id}`}
              onClick={() => handleCardClick(scenario.id)}
              className={`group relative cursor-pointer overflow-hidden rounded-2xl bg-white transition-all duration-300 ${
                isSelected
                  ? "shadow-xl shadow-purple-200 ring-4 ring-purple-500 ring-offset-2"
                  : "shadow-md hover:shadow-xl"
              } ${isExpanded ? "ring-4 ring-purple-500 ring-offset-2" : ""}`}
              whileHover={{ y: -6 }}
              whileTap={{ scale: 0.98 }}
            >
              {/* Card Image */}
              <div className="relative aspect-[4/3] overflow-hidden bg-gradient-to-br from-purple-100 via-pink-50 to-orange-50">
                {scenario.thumbnail_url ? (
                  <img
                    src={scenario.thumbnail_url}
                    alt={scenario.name}
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "/placeholder.svg";
                    }}
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <BookOpen className="h-16 w-16 text-purple-300" />
                  </div>
                )}

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />

                {/* Marketing Badge */}
                {scenario.marketing_badge && (
                  <div className="absolute left-3 top-3 rounded-full bg-gradient-to-r from-orange-500 to-pink-500 px-2.5 py-1 text-xs font-bold text-white shadow-lg">
                    {scenario.marketing_badge}
                  </div>
                )}

                {/* Rating Badge */}
                <div className="absolute right-3 top-3 flex items-center gap-1 rounded-full bg-white/90 px-2 py-1 shadow-md backdrop-blur-sm">
                  <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                  <span className="text-xs font-bold">{typeof extended.rating === 'number' ? extended.rating.toFixed(1) : extended.rating}</span>
                </div>

                {/* Selected Checkmark */}
                {isSelected && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute bottom-3 right-3 flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg"
                  >
                    <Check className="h-5 w-5 text-white" strokeWidth={3} />
                  </motion.div>
                )}

                {/* Video indicator */}
                {extended.videoUrl && (
                  <div className="absolute bottom-3 left-3 flex items-center gap-1 rounded-full bg-black/60 px-2 py-1 text-[10px] text-white backdrop-blur-sm">
                    <Play className="h-3 w-3 fill-white" />
                    Video
                  </div>
                )}
              </div>

              {/* Card Content */}
              <div className="p-4">
                <h3 className="mb-1 text-base font-bold text-gray-900">{scenario.name}</h3>
                <p className="mb-3 line-clamp-2 text-xs leading-relaxed text-gray-500">
                  {extended.tagline || scenario.description}
                </p>

                {/* Meta info row */}
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  {scenario.age_range && (
                    <span className="flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700">
                      <Clock className="h-3 w-3" />
                      {scenario.age_range}
                    </span>
                  )}
                  {scenario.estimated_duration && (
                    <span className="flex items-center gap-1 rounded-full bg-purple-50 px-2 py-0.5 text-[11px] font-medium text-purple-700">
                      <Clock className="h-3 w-3" />
                      {scenario.estimated_duration}
                    </span>
                  )}
                  {scenario.marketing_price_label && (
                    <span className="flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-[11px] font-medium text-green-700">
                      {scenario.marketing_price_label}
                    </span>
                  )}
                </div>

                {/* Features preview */}
                {extended.features && extended.features.length > 0 && (
                  <ul className="mb-3 space-y-1">
                    {extended.features.slice(0, 2).map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-1.5 text-[11px] text-gray-600">
                        <div className="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full bg-green-100">
                          <Check className="h-2 w-2 text-green-600" />
                        </div>
                        {feature}
                      </li>
                    ))}
                  </ul>
                )}

                {/* Social proof */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    <span className="font-medium text-gray-600">{(extended.reviewCount || 0).toLocaleString()}+</span>
                    <span>aile</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelect(scenario.id);
                      setModalScenarioId(scenario.id);
                    }}
                    className="rounded-lg bg-gradient-to-r from-purple-600 to-pink-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-all hover:shadow-md"
                  >
                    İncele
                  </button>
                </div>
              </div>

              {/* Selected overlay glow */}
              {isSelected && (
                <div className="pointer-events-none absolute inset-0 rounded-2xl ring-inset ring-4 ring-purple-500/20" />
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Detail Panel Content - Shared between Desktop and Mobile */}
      {expandedData && (
        <>
          {/* Desktop: Inline Expanded Panel */}
          {!isMobile && (
            <AnimatePresence>
              {expandedScenario && (
                <motion.div
                  ref={detailRef}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.4, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <motion.div
                    initial={{ y: 20 }}
                    animate={{ y: 0 }}
                    exit={{ y: 20 }}
                    className="relative overflow-hidden rounded-3xl border border-purple-100 bg-gradient-to-br from-purple-50 via-white to-pink-50 shadow-xl"
                  >
                    {/* Close Button */}
                    <button
                      onClick={handleCloseDetail}
                      className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-white/80 shadow-md backdrop-blur-sm transition hover:bg-white"
                    >
                      <X className="h-4 w-4 text-gray-600" />
                    </button>

                    <DetailPanelContent
                      expandedData={expandedData}
                      galleryIndex={galleryIndex}
                      setGalleryIndex={setGalleryIndex}
                      onContinue={onContinue}
                    />
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          )}

          {/* Mobile: Bottom Sheet */}
          {isMobile && (
            <MobileBottomSheet isOpen={!!expandedScenario} onClose={handleCloseDetail}>
              <DetailPanelContent
                expandedData={expandedData}
                galleryIndex={galleryIndex}
                setGalleryIndex={setGalleryIndex}
                onContinue={onContinue}
                isMobile
              />
            </MobileBottomSheet>
          )}
        </>
      )}

      {/* Bottom Actions */}
      <div className="flex gap-3 pt-2">
        {onBack && (
          <Button variant="outline" onClick={onBack} className="px-6">
            Geri
          </Button>
        )}
        <Button
          className="flex-1 bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600"
          onClick={onContinue}
          disabled={!selectedScenario || scenarios.length === 0}
        >
          {scenarios.length === 0
            ? "Macera yok"
            : selectedScenario
              ? "Devam Et"
              : "Bir Macera Seçin"}
        </Button>
      </div>

      {/* Scenario Detail Modal */}
      <ScenarioDetailModal
        scenario={
          modalScenarioId
            ? getExtendedScenario(scenarios.find((s) => s.id === modalScenarioId)!)
            : null
        }
        isOpen={!!modalScenarioId}
        onClose={() => setModalScenarioId(null)}
        onSelect={() => {
          if (modalScenarioId) {
            onSelect(modalScenarioId);
          }
          setModalScenarioId(null);
          onContinue();
        }}
      />
    </div>
  );
}
