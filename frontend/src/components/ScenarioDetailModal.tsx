"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Play,
  Star,
  Check,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  BookOpen,
  Brain,
  Heart,
  Shield,
  Users,
  Clock,
  Wand2,
  Gift,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ScenarioForModal {
  id: string;
  name: string;
  description: string | null;
  thumbnail_url: string;
  gallery_images?: string[];
  // Marketing fields
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
  // Extended (from AdventureSelector mock merge)
  videoUrl?: string;
  galleryImages?: string[];
  learningOutcomes?: string[];
  features?: string[];
  reviewCount?: number;
}

interface ScenarioDetailModalProps {
  scenario: ScenarioForModal | null;
  isOpen: boolean;
  onClose: () => void;
  onSelect: () => void;
}

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
};

export default function ScenarioDetailModal({
  scenario,
  isOpen,
  onClose,
  onSelect,
}: ScenarioDetailModalProps) {
  const [galleryIndex, setGalleryIndex] = useState(0);

  if (!scenario) return null;

  // Resolve gallery: marketing_gallery > gallery_images > extended > thumbnail
  const gallery =
    (scenario.marketing_gallery && scenario.marketing_gallery.length > 0)
      ? scenario.marketing_gallery
      : (scenario.galleryImages && scenario.galleryImages.length > 0)
        ? scenario.galleryImages
        : (scenario.gallery_images && scenario.gallery_images.length > 0)
          ? scenario.gallery_images
          : [scenario.thumbnail_url];

  const videoUrl = scenario.marketing_video_url || scenario.videoUrl;
  const features = (scenario.marketing_features && scenario.marketing_features.length > 0)
    ? scenario.marketing_features
    : scenario.features || [];
  const rating = scenario.rating;
  const reviewCount = scenario.review_count ?? scenario.reviewCount;
  const tagline = scenario.tagline || scenario.description;

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
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-x-4 bottom-4 top-4 z-50 mx-auto max-w-3xl overflow-hidden rounded-3xl bg-white shadow-2xl md:inset-x-auto md:left-1/2 md:w-full md:-translate-x-1/2"
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute right-4 top-4 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/90 shadow-md backdrop-blur-sm transition hover:bg-white"
            >
              <X className="h-5 w-5 text-gray-600" />
            </button>

            <div className="h-full overflow-y-auto">
              <div className="p-4 md:p-6">
                <div className="grid gap-5 md:grid-cols-2">
                  {/* Left Column - Visuals */}
                  <div className="space-y-4">
                    {/* Age range & duration info */}
                    {(scenario.age_range || scenario.estimated_duration) && (
                      <div className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-100 to-pink-100 p-3 text-purple-700">
                        <BookOpen className="h-5 w-5 shrink-0" />
                        <span className="text-sm font-semibold">Hikaye Konusu</span>
                        {scenario.age_range && (
                          <span className="ml-auto rounded-full bg-white/70 px-2 py-0.5 text-xs font-medium">{scenario.age_range}</span>
                        )}
                        {scenario.estimated_duration && (
                          <>
                            <Clock className="h-4 w-4 shrink-0" />
                            <span className="text-xs">{scenario.estimated_duration}</span>
                          </>
                        )}
                      </div>
                    )}

                    {/* Video Player */}
                    <div className="relative aspect-video overflow-hidden rounded-2xl bg-gradient-to-br from-purple-200 to-pink-200 shadow-inner">
                      {videoUrl ? (
                        <iframe
                          src={videoUrl}
                          className="h-full w-full"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                        />
                      ) : (
                        <div className="flex h-full w-full flex-col items-center justify-center text-purple-400">
                          <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-white/50 shadow-lg">
                            <Play className="ml-1 h-8 w-8 text-purple-500" />
                          </div>
                          <p className="text-sm font-medium">Hikaye Tanıtımını İzle</p>
                        </div>
                      )}
                    </div>

                    {/* Gallery */}
                    {gallery.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                          <Sparkles className="h-4 w-4 text-purple-500" />
                          Kitaptan Kareler
                        </h4>
                        <div className="relative">
                          <div className="aspect-[4/3] overflow-hidden rounded-xl bg-gradient-to-br from-purple-100 to-pink-100">
                            {gallery[galleryIndex] ? (
                              <img
                                src={gallery[galleryIndex]}
                                alt={`Galeri ${galleryIndex + 1}`}
                                className="h-full w-full object-cover"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = "/placeholder.svg";
                                }}
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center">
                                <BookOpen className="h-12 w-12 text-purple-300" />
                              </div>
                            )}
                          </div>

                          {gallery.length > 1 && (
                            <>
                              <button
                                onClick={() => setGalleryIndex(Math.max(0, galleryIndex - 1))}
                                disabled={galleryIndex === 0}
                                className="absolute left-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 shadow-md backdrop-blur-sm transition hover:bg-white disabled:opacity-50"
                              >
                                <ChevronLeft className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() =>
                                  setGalleryIndex(Math.min(gallery.length - 1, galleryIndex + 1))
                                }
                                disabled={galleryIndex === gallery.length - 1}
                                className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 shadow-md backdrop-blur-sm transition hover:bg-white disabled:opacity-50"
                              >
                                <ChevronRight className="h-4 w-4" />
                              </button>
                            </>
                          )}
                        </div>

                        {gallery.length > 1 && (
                          <div className="flex justify-center gap-1.5">
                            {gallery.map((_, idx) => (
                              <button
                                key={idx}
                                onClick={() => setGalleryIndex(idx)}
                                className={`h-2 rounded-full transition-all ${idx === galleryIndex
                                  ? "w-6 bg-purple-500"
                                  : "w-2 bg-gray-300 hover:bg-purple-300"
                                  }`}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Right Column - Info & CTA */}
                  <div className="space-y-4">
                    {/* Title & Rating */}
                    <div>
                      <h2 className="bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text text-2xl font-bold text-transparent">
                        {scenario.name}
                      </h2>
                      {tagline && (
                        <p className="mt-1 text-sm text-gray-600">{tagline}</p>
                      )}

                      {rating != null && rating > 0 && (
                        <div className="mt-3 flex items-center gap-2">
                          <div className="flex">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <Star
                                key={star}
                                className={`h-4 w-4 ${star <= Math.floor(rating)
                                  ? "fill-yellow-400 text-yellow-400"
                                  : "text-gray-300"
                                  }`}
                              />
                            ))}
                          </div>
                          <span className="text-sm font-bold">{rating.toFixed(1)}</span>
                          {reviewCount != null && reviewCount > 0 && (
                            <span className="text-xs text-gray-500">
                              ({Number(reviewCount).toLocaleString()} aile)
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Meta badges */}
                    <div className="flex flex-wrap gap-2">
                      {scenario.age_range && (
                        <span className="flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                          <Clock className="h-3 w-3" />
                          {scenario.age_range}
                        </span>
                      )}

                    </div>

                    {/* Description */}
                    {scenario.description && (
                      <div className="rounded-xl border border-purple-100 bg-white/60 p-3 backdrop-blur-sm">
                        <p className="text-sm leading-relaxed text-gray-700">{scenario.description}</p>
                      </div>
                    )}

                    {/* Learning Outcomes */}
                    {scenario.learningOutcomes && scenario.learningOutcomes.length > 0 && (
                      <div>
                        <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-700">
                          <Brain className="h-4 w-4 text-purple-500" />
                          Bu Hikayede Öğrenecekleri
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {scenario.learningOutcomes.map((outcome, idx) => (
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
                    )}

                    {/* Features */}
                    {features.length > 0 && (
                      <div>
                        <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-700">
                          <BookOpen className="h-4 w-4 text-purple-500" />
                          Kitabın İçinde
                        </h4>
                        <ul className="space-y-1.5">
                          {features.map((feature, idx) => (
                            <li key={idx} className="flex items-center gap-2 text-gray-600">
                              <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-green-100">
                                <Check className="h-2.5 w-2.5 text-green-600" />
                              </div>
                              <span className="text-xs">{feature}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Gift Badge */}
                    <div className="flex items-center gap-2 rounded-xl border border-purple-100 bg-purple-50 p-2.5">
                      <Gift className="h-5 w-5 text-purple-500" />
                      <div>
                        <p className="text-xs font-medium text-purple-700">Hediye Paketi Dahil</p>
                        <p className="text-[10px] text-purple-500">Özel kutu ve teşekkür kartı</p>
                      </div>
                    </div>



                    {/* CTA Button */}
                    <Button
                      onClick={() => {
                        onSelect();
                        onClose();
                      }}
                      className="w-full bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 py-6 text-base font-bold shadow-lg shadow-purple-300 hover:shadow-xl hover:shadow-purple-400"
                    >
                      <Wand2 className="mr-2 h-5 w-5" />
                      Bu Konuyu Seç
                      <Sparkles className="ml-2 h-5 w-5" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
