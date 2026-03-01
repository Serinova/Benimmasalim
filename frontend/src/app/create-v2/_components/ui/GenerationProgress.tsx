"use client";

import { motion } from "framer-motion";
import { Loader2, Sparkles, BookOpen, Image as ImageIcon } from "lucide-react";
import type { GenerationProgress as GP } from "@/lib/api";

interface GenerationProgressProps {
  progress: GP | null;
  isLoading: boolean;
}

const STAGE_INFO: Record<string, { icon: React.ReactNode; label: string }> = {
  story_generation: { icon: <BookOpen className="h-5 w-5" />, label: "Hikaye yazılıyor..." },
  image_generation: { icon: <ImageIcon className="h-5 w-5" />, label: "Görseller oluşturuluyor..." },
  preview_generation: { icon: <Sparkles className="h-5 w-5" />, label: "Önizleme hazırlanıyor..." },
};

export default function GenerationProgressUI({
  progress,
  isLoading,
}: GenerationProgressProps) {
  if (!isLoading) return null;

  const stage = progress?.stage || "story_generation";
  const info = STAGE_INFO[stage] || STAGE_INFO.story_generation;
  const current = progress?.current_page ?? 0;
  const total = progress?.total_pages ?? 0;
  const percent = total > 0 ? Math.round((current / total) * 100) : 0;
  const message = progress?.message || info.label;

  return (
    <div className="flex flex-col items-center justify-center py-12 sm:py-20 px-4">
      {/* Animated icon */}
      <motion.div
        animate={{ rotate: [0, 5, -5, 0], scale: [1, 1.05, 1] }}
        transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
        className="mb-6 flex h-20 w-20 sm:h-24 sm:w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-purple-100 to-pink-100 text-purple-600"
      >
        {info.icon}
      </motion.div>

      <h2 className="text-lg sm:text-xl font-bold text-gray-800 mb-2 text-center">
        Sihirli Kalem Çalışıyor...
      </h2>

      <p className="text-sm text-gray-500 mb-6 text-center max-w-sm">
        {message}
      </p>

      {/* Progress bar */}
      {total > 0 ? (
        <div className="w-full max-w-xs space-y-2">
          <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
              initial={{ width: 0 }}
              animate={{ width: `${percent}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <p className="text-xs text-center text-gray-400">
            {current}/{total} sayfa hazırlandı
          </p>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Yaklaşık 1-2 dakika</span>
        </div>
      )}
    </div>
  );
}
