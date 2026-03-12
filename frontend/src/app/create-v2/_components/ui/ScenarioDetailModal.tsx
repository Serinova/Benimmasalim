"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import Image from "next/image";
import type { Scenario } from "@/lib/api";

interface ScenarioDetailModalProps {
  scenario: Scenario | null;
  isOpen: boolean;
  onClose: () => void;
  onSelect: () => void;
}

export default function ScenarioDetailModal({
  scenario,
  isOpen,
  onClose,
  onSelect,
}: ScenarioDetailModalProps) {
  if (!scenario) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-x-4 top-[10%] z-50 max-h-[80vh] overflow-y-auto rounded-2xl bg-white shadow-2xl sm:inset-x-auto sm:left-1/2 sm:w-full sm:max-w-md sm:-translate-x-1/2"
          >
            {/* Close button */}
            <button
              type="button"
              onClick={onClose}
              className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-white/80 shadow-sm"
            >
              <X className="h-4 w-4 text-slate-500" />
            </button>

            {/* Cover image */}
            {scenario.thumbnail_url && (
              <div className="relative h-44 w-full overflow-hidden rounded-t-2xl">
                <Image
                  src={scenario.thumbnail_url}
                  alt={scenario.name}
                  fill
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
              </div>
            )}

            <div className="p-5 space-y-3">
              <h3 className="text-lg font-bold text-slate-800">{scenario.name}</h3>

              {scenario.description && (
                <p className="text-sm text-slate-600 leading-relaxed">
                  {scenario.description}
                </p>
              )}

              {/* Select button */}
              <button
                type="button"
                onClick={onSelect}
                className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 py-3 text-sm font-bold text-white shadow-lg shadow-violet-200 transition-transform active:scale-[0.98]"
              >
                Bu Senaryoyu Seç
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
