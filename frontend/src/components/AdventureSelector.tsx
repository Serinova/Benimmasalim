"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Info, CheckCircle2, Search, X } from "lucide-react";
import ScenarioDetailModal from "@/components/ScenarioDetailModal";
import type { Scenario } from "@/lib/api";

interface AdventureSelectorProps {
  scenarios: Scenario[];
  selectedScenario: string;
  onSelect: (id: string) => void;
  onContinue?: () => void;
  onBack?: () => void;
  childName?: string;
}

// Theme tags extracted from scenario names/flags
function getTheme(s: Scenario): string {
  const name = (s.name || "").toLowerCase();
  if (name.includes("uzay") || name.includes("gezegen") || name.includes("güneş")) return "Uzay";
  if (name.includes("orman") || name.includes("doğa") || name.includes("amazon")) return "Doğa";
  if (name.includes("tarih") || name.includes("kapadok") || name.includes("yerebatan") || name.includes("sarnıç")) return "Tarih";
  if (name.includes("deniz") || name.includes("okyanus") || name.includes("su")) return "Deniz";
  if (name.includes("spor") || name.includes("futbol") || name.includes("koş")) return "Spor";
  if (name.includes("bilim") || name.includes("robot") || name.includes("teknoloj")) return "Bilim";
  return "Macera";
}

export default function AdventureSelector({
  scenarios,
  selectedScenario,
  onSelect,
  onContinue,
  onBack,
  childName,
}: AdventureSelectorProps) {
  const [detailScenario, setDetailScenario] = useState<Scenario | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTheme, setActiveTheme] = useState<string | null>(null);

  // Collect unique themes
  const themes = Array.from(new Set(scenarios.map(getTheme)));

  // Filter scenarios
  const filtered = scenarios.filter((s) => {
    const matchesSearch = !searchQuery || s.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTheme = !activeTheme || getTheme(s) === activeTheme;
    return matchesSearch && matchesTheme;
  });

  const selectedObj = scenarios.find((s) => s.id === selectedScenario);

  return (
    <div className="space-y-4 px-1 pt-2 pb-4">

      {/* ── Header ── */}
      <div>
        <p className="text-xs font-semibold text-purple-500 uppercase tracking-wider mb-1">🗺️ Macera Seç</p>
        <h2 className="text-xl font-bold text-gray-800 leading-tight">
          {childName
            ? <><span className="text-purple-600">{childName}</span>&apos;ın Macerası</>
            : "Hangi Macera?"
          }
        </h2>
        <p className="text-sm text-gray-400 mt-0.5">{scenarios.length} harika hikayeden birini seç</p>
      </div>

      {/* ── Search ── */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Macera ara..."
          className="w-full rounded-2xl border-2 border-gray-100 bg-white pl-10 pr-4 py-3 text-sm text-gray-700 outline-none focus:border-purple-300 transition-colors"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* ── Theme Filter Pills ── */}
      {themes.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => setActiveTheme(null)}
            className={`flex-shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition-all ${!activeTheme
                ? "bg-purple-600 text-white shadow-sm"
                : "bg-gray-100 text-gray-600"
              }`}
          >
            Tümü
          </button>
          {themes.map((theme) => (
            <button
              key={theme}
              onClick={() => setActiveTheme(activeTheme === theme ? null : theme)}
              className={`flex-shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition-all ${activeTheme === theme
                  ? "bg-purple-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-600"
                }`}
            >
              {theme}
            </button>
          ))}
        </div>
      )}

      {/* ── Scenario Grid ── */}
      <div className="grid grid-cols-2 gap-3">
        <AnimatePresence>
          {filtered.map((scenario, i) => {
            const isSelected = selectedScenario === scenario.id;
            const theme = getTheme(scenario);
            const themeColors: Record<string, string> = {
              Uzay: "from-indigo-400 to-purple-600",
              Doğa: "from-green-400 to-emerald-600",
              Tarih: "from-amber-400 to-orange-600",
              Deniz: "from-cyan-400 to-blue-600",
              Spor: "from-red-400 to-rose-600",
              Bilim: "from-teal-400 to-cyan-600",
              Macera: "from-purple-400 to-pink-600",
            };
            const gradient = themeColors[theme] || "from-purple-400 to-pink-600";

            return (
              <motion.div
                key={scenario.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.04 }}
                className="relative"
              >
                <motion.button
                  type="button"
                  whileTap={{ scale: 0.97 }}
                  onClick={() => onSelect(scenario.id)}
                  className={`
                    relative w-full overflow-hidden rounded-2xl text-left transition-all duration-200
                    ${isSelected
                      ? "ring-3 ring-purple-500 shadow-xl shadow-purple-200"
                      : "shadow-sm hover:shadow-md"
                    }
                  `}
                >
                  {/* Thumbnail */}
                  <div className="aspect-[4/3] relative overflow-hidden">
                    {scenario.thumbnail_url ? (
                      <img
                        src={scenario.thumbnail_url}
                        alt={scenario.name}
                        className="h-full w-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    ) : null}
                    {/* Always-visible gradient bg */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${gradient} ${scenario.thumbnail_url ? "opacity-40" : "opacity-100"}`} />

                    {/* Theme badge */}
                    <div className="absolute top-2 left-2">
                      <span className="rounded-lg bg-black/30 backdrop-blur-sm px-2 py-0.5 text-white text-[10px] font-semibold">
                        {theme}
                      </span>
                    </div>

                    {/* Info button */}
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setDetailScenario(scenario); }}
                      className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/30 backdrop-blur-sm flex items-center justify-center transition-all hover:bg-black/50"
                    >
                      <Info className="h-3.5 w-3.5 text-white" />
                    </button>

                    {/* Selected overlay */}
                    <AnimatePresence>
                      {isSelected && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="absolute inset-0 bg-purple-600/20 flex items-center justify-center"
                        >
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center shadow-lg"
                          >
                            <CheckCircle2 className="h-6 w-6 text-white" />
                          </motion.div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Card body */}
                  <div className={`px-3 py-3 ${isSelected ? "bg-purple-50" : "bg-white"}`}>
                    <p className={`text-sm font-bold leading-tight ${isSelected ? "text-purple-700" : "text-gray-800"}`}>
                      {scenario.name}
                    </p>
                    {(scenario.rating || scenario.age_range) && (
                      <div className="mt-1.5 flex items-center gap-2">
                        {scenario.rating && (
                          <span className="flex items-center gap-0.5 text-xs text-amber-500 font-semibold">
                            ⭐ {typeof scenario.rating === "number" ? scenario.rating.toFixed(1) : scenario.rating}
                          </span>
                        )}
                        {scenario.age_range && (
                          <span className="text-[10px] text-gray-400">{scenario.age_range}</span>
                        )}
                      </div>
                    )}
                    {scenario.tagline && (
                      <p className="mt-1 text-[11px] text-gray-500 line-clamp-2 leading-snug">
                        {scenario.tagline}
                      </p>
                    )}
                  </div>
                </motion.button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {filtered.length === 0 && (
        <div className="py-12 text-center">
          <p className="text-4xl mb-3">🔍</p>
          <p className="text-gray-500 text-sm">Arama sonucu bulunamadı</p>
          <button
            onClick={() => { setSearchQuery(""); setActiveTheme(null); }}
            className="mt-3 text-purple-600 text-sm font-medium"
          >
            Filtreleri temizle
          </button>
        </div>
      )}

      {/* ── Sticky Bottom CTA ── */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-gray-100 px-4 pt-3 pb-safe-4">
        <div className="mx-auto flex max-w-lg gap-3 pb-2">
          <button
            type="button"
            onClick={onBack}
            className="h-14 px-5 rounded-2xl border-2 border-gray-200 text-gray-600 font-semibold text-sm flex items-center gap-1"
          >
            ← Geri
          </button>
          <motion.button
            type="button"
            whileTap={{ scale: 0.98 }}
            onClick={() => selectedScenario && onContinue?.()}
            disabled={!selectedScenario}
            className={`
              h-14 flex-1 rounded-2xl font-bold text-base transition-all duration-200
              ${selectedScenario
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-200"
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
              }
            `}
          >
            {selectedObj
              ? <span className="flex items-center justify-center gap-2">
                <CheckCircle2 className="h-5 w-5" />
                {selectedObj.name} Seçildi →
              </span>
              : "Bir Macera Seç"
            }
          </motion.button>
        </div>
      </div>

      {/* ── Detail Modal ── */}
      {detailScenario && (
        <ScenarioDetailModal
          scenario={{
            id: detailScenario.id,
            name: detailScenario.name,
            description: detailScenario.description,
            thumbnail_url: detailScenario.thumbnail_url,
            tagline: detailScenario.tagline,
            age_range: detailScenario.age_range,
            rating: detailScenario.rating,
            review_count: detailScenario.review_count,
            marketing_features: detailScenario.marketing_features,
            marketing_video_url: detailScenario.marketing_video_url,
            marketing_gallery: detailScenario.marketing_gallery,
            marketing_price_label: detailScenario.marketing_price_label,
            videoUrl: detailScenario.marketing_video_url ?? undefined,
            galleryImages: detailScenario.gallery_images ?? detailScenario.marketing_gallery,
            features: detailScenario.marketing_features,
            reviewCount: detailScenario.review_count ?? undefined,
          }}
          isOpen={true}
          onSelect={() => { onSelect(detailScenario.id); setDetailScenario(null); }}
          onClose={() => setDetailScenario(null)}
        />
      )}
    </div>
  );
}
