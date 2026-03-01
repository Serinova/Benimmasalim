"use client";

import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

interface StickyCTAProps {
  primaryLabel: string;
  onPrimary: () => void;
  primaryDisabled?: boolean;
  primaryLoading?: boolean;
  secondaryLabel?: string;
  onSecondary?: () => void;
  extraContent?: React.ReactNode;
}

export default function StickyCTA({
  primaryLabel,
  onPrimary,
  primaryDisabled = false,
  primaryLoading = false,
  secondaryLabel,
  onSecondary,
  extraContent,
}: StickyCTAProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-gray-100 px-3 sm:px-4 py-2.5 sm:py-3"
      style={{ paddingBottom: "max(0.625rem, env(safe-area-inset-bottom))" }}
    >
      <div className="mx-auto max-w-lg space-y-1.5">
        {extraContent}
        <div className="flex gap-2 sm:gap-3">
          {secondaryLabel && onSecondary && (
            <button
              type="button"
              onClick={onSecondary}
              className="h-11 sm:h-12 px-3 sm:px-5 rounded-xl border-2 border-gray-200 text-gray-600 font-semibold text-sm flex items-center transition-colors hover:bg-gray-50 active:bg-gray-100"
            >
              {secondaryLabel}
            </button>
          )}
          <motion.button
            type="button"
            whileTap={!primaryDisabled && !primaryLoading ? { scale: 0.97 } : undefined}
            onClick={onPrimary}
            disabled={primaryDisabled || primaryLoading}
            className={`
              h-11 sm:h-12 flex-1 rounded-xl font-bold text-sm sm:text-base shadow-lg shadow-purple-200
              flex items-center justify-center gap-2 transition-all
              ${
                primaryDisabled || primaryLoading
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed shadow-none"
                  : "bg-gradient-to-r from-purple-600 to-pink-500 text-white"
              }
            `}
          >
            {primaryLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              primaryLabel
            )}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
