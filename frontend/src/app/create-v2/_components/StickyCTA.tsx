"use client";

import { motion } from "framer-motion";
import { Loader2, ChevronLeft } from "lucide-react";
import TrustBadges from "./ui/TrustBadges";

interface StickyCTAProps {
  primaryLabel: string;
  onPrimary: () => void;
  primaryDisabled?: boolean;
  primaryLoading?: boolean;
  secondaryLabel?: string;
  onSecondary?: () => void;
  extraContent?: React.ReactNode;
  hideTrust?: boolean;
}

export default function StickyCTA({
  primaryLabel,
  onPrimary,
  primaryDisabled = false,
  primaryLoading = false,
  secondaryLabel,
  onSecondary,
  extraContent,
  hideTrust = false,
}: StickyCTAProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed bottom-0 left-0 right-0 z-[60] border-t border-slate-100 bg-white/95 px-3 py-2 backdrop-blur-md sm:px-4 sm:py-2.5"
      style={{ paddingBottom: "max(0.5rem, env(safe-area-inset-bottom, 0px))" }}
    >
      <div className="mx-auto max-w-lg space-y-1.5">
        {/* Trust badges row */}
        {!hideTrust && (
          <TrustBadges className="pt-0.5" />
        )}

        {extraContent}

        <div className="flex gap-2 sm:gap-3">
          {secondaryLabel && onSecondary && (
            <button
              type="button"
              onClick={onSecondary}
              className="flex h-11 items-center gap-1 rounded-xl border-2 border-slate-200 px-3 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50 active:bg-slate-100 sm:h-12 sm:px-4"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline">{secondaryLabel.replace("←", "").trim()}</span>
              <span className="sm:hidden">Geri</span>
            </button>
          )}
          <motion.button
            type="button"
            whileTap={!primaryDisabled && !primaryLoading ? { scale: 0.97 } : undefined}
            onClick={onPrimary}
            disabled={primaryDisabled || primaryLoading}
            aria-busy={primaryLoading}
            className={`
              flex h-11 flex-1 items-center justify-center gap-2 rounded-xl font-bold text-sm shadow-lg transition-all sm:h-12 sm:text-base
              ${
                primaryDisabled || primaryLoading
                  ? "cursor-not-allowed bg-slate-200 text-slate-400 shadow-none"
                  : "bg-gradient-to-r from-violet-600 to-pink-500 text-white shadow-violet-200/60 hover:shadow-xl hover:shadow-violet-200/80 active:shadow-md"
              }
            `}
          >
            {primaryLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
                <span className="sr-only">İşleniyor…</span>
              </>
            ) : (
              primaryLabel
            )}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
