"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronUp, ShoppingBag } from "lucide-react";
import { formatPrice } from "../_lib/pricing";
import type { PriceBreakdown } from "../_lib/pricing";

interface OrderSummaryCardProps {
  childName: string;
  storyTitle?: string;
  coverImageUrl?: string | null;
  productName?: string;
  breakdown: PriceBreakdown;
  promoSlot?: React.ReactNode;
  variant?: "sidebar" | "bottom-sheet";
}

export default function OrderSummaryCard({
  childName,
  storyTitle,
  productName,
  breakdown,
  promoSlot,
  variant = "sidebar",
}: OrderSummaryCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (variant === "bottom-sheet") {
    return (
      <div className="lg:hidden fixed bottom-[52px] sm:bottom-[56px] left-0 right-0 z-40">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between bg-white/95 backdrop-blur-md border-t border-gray-100 px-4 py-2.5"
        >
          <div className="flex items-center gap-2">
            <ShoppingBag className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-semibold text-gray-800">
              Sipariş Özeti
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-purple-700">
              {formatPrice(breakdown.total)} ₺
            </span>
            <ChevronUp
              className={`h-4 w-4 text-gray-400 transition-transform ${expanded ? "" : "rotate-180"}`}
            />
          </div>
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden bg-white border-t border-gray-50"
            >
              <div className="px-4 py-3 space-y-3">
                <SummaryLines breakdown={breakdown} productName={productName} />
                {promoSlot}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-5 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <ShoppingBag className="h-4 w-4 text-purple-600" />
        <h3 className="text-sm font-bold text-gray-800">Sipariş Özeti</h3>
      </div>

      {(childName || storyTitle) && (
        <div className="rounded-xl bg-purple-50/50 p-3">
          {storyTitle && (
            <p className="text-sm font-semibold text-gray-800 truncate">{storyTitle}</p>
          )}
          {childName && (
            <p className="text-xs text-gray-500">Kahraman: {childName}</p>
          )}
        </div>
      )}

      <SummaryLines breakdown={breakdown} productName={productName} />

      {promoSlot && <div className="pt-1">{promoSlot}</div>}

      <div className="border-t border-gray-100 pt-3 flex items-center justify-between">
        <span className="text-sm font-bold text-gray-800">Toplam</span>
        <span className="text-lg font-black text-purple-700">
          {formatPrice(breakdown.total)} ₺
        </span>
      </div>
    </div>
  );
}

function SummaryLines({
  breakdown,
  productName,
}: {
  breakdown: PriceBreakdown;
  productName?: string;
}) {
  return (
    <div className="space-y-1.5 text-sm">
      <div className="flex justify-between">
        <span className="text-gray-600">{productName || "Kitap"}</span>
        <span className="font-semibold text-gray-800">{formatPrice(breakdown.basePrice)} ₺</span>
      </div>
      {breakdown.audioPrice > 0 && (
        <div className="flex justify-between">
          <span className="text-gray-600">Sesli Kitap</span>
          <span className="font-semibold text-gray-800">+{formatPrice(breakdown.audioPrice)} ₺</span>
        </div>
      )}
      {breakdown.coloringBookPrice > 0 && (
        <div className="flex justify-between">
          <span className="text-gray-600">Boyama Kitabı</span>
          <span className="font-semibold text-gray-800">+{formatPrice(breakdown.coloringBookPrice)} ₺</span>
        </div>
      )}
      {breakdown.discount > 0 && (
        <div className="flex justify-between text-green-600">
          <span>İndirim {breakdown.promoCode && `(${breakdown.promoCode})`}</span>
          <span className="font-semibold">-{formatPrice(breakdown.discount)} ₺</span>
        </div>
      )}
    </div>
  );
}
