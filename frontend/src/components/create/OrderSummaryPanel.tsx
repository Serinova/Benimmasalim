"use client";

import { Package, Truck, Shield, Clock, Heart, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface OrderSummaryPanelProps {
  /** Product name to display */
  productName?: string;
  /** Base book price */
  basePrice?: number;
  /** Whether audio book is selected */
  hasAudioBook?: boolean;
  /** Audio addon price */
  audioPrice?: number;
  /** Audio type label */
  audioType?: "system" | "cloned";
  /** Child name */
  childName?: string;
  /** Story title (shown after generation) */
  storyTitle?: string;
  /** Cover preview URL */
  coverImageUrl?: string | null;
  /** Current funnel step (1-5) */
  currentStep: number;
  /** Applied discount amount */
  discountAmount?: number;
  /** Promo code text */
  promoCode?: string | null;
}

export default function OrderSummaryPanel({
  productName,
  basePrice,
  hasAudioBook,
  audioPrice = 0,
  audioType,
  childName,
  storyTitle,
  coverImageUrl,
  currentStep,
  discountAmount = 0,
  promoCode,
}: OrderSummaryPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const shippingCost = 0;
  const rawTotal = (basePrice ?? 0) + (hasAudioBook ? audioPrice : 0) + shippingCost;
  const totalPrice = Math.max(rawTotal - discountAmount, 0);

  // Don't show summary until we have at least a product selected
  if (!productName && currentStep < 2) return null;

  // Estimated delivery
  const getEstimatedDelivery = () => {
    const date = new Date();
    let daysAdded = 0;
    while (daysAdded < 3) {
      date.setDate(date.getDate() + 1);
      if (date.getDay() !== 0 && date.getDay() !== 6) daysAdded++;
    }
    return date.toLocaleDateString("tr-TR", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
  };

  return (
    <>
      {/* Desktop: sticky sidebar */}
      <aside className="sticky top-2 hidden space-y-3 lg:block" aria-label="Sipariş özeti">
        {/* Book preview card */}
        {(storyTitle || childName) && (
          <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
            <div className="relative mb-2 aspect-[3/4] overflow-hidden rounded-md bg-gradient-to-br from-purple-100 to-pink-100">
              {coverImageUrl ? (
                <img
                  src={coverImageUrl}
                  alt="Kitap önizleme"
                  className="h-full w-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center">
                  <Package className="h-8 w-8 text-purple-200" />
                </div>
              )}
            </div>
            {storyTitle && (
              <h3 className="text-center text-xs font-semibold text-gray-800">
                &ldquo;{storyTitle}&rdquo;
              </h3>
            )}
            {childName && (
              <p className="mt-0.5 text-center text-xs text-gray-500">
                {childName} için özel hazırlandı
              </p>
            )}
          </div>
        )}

        {/* Price breakdown */}
        {basePrice != null && basePrice > 0 && (
          <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
            <h3 className="mb-2 text-xs font-semibold text-gray-800">
              Sipariş Özeti
            </h3>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">{productName}</span>
                <span className="font-medium">{basePrice} TL</span>
              </div>
              {hasAudioBook && (
                <div className="flex justify-between">
                  <span className="text-gray-600">
                    Sesli Kitap{" "}
                    {audioType === "cloned" ? "(Klonlanmış)" : "(Profesyonel)"}
                  </span>
                  <span className="font-medium">{audioPrice} TL</span>
                </div>
              )}
              <div className="flex justify-between text-green-600">
                <span>Kargo</span>
                <span className="font-medium">ÜCRETSİZ</span>
              </div>
              {discountAmount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>İndirim {promoCode && `(${promoCode})`}</span>
                  <span className="font-medium">-{discountAmount} TL</span>
                </div>
              )}
              <div className="flex justify-between border-t border-gray-100 pt-2">
                <span className="font-semibold text-gray-800">Toplam</span>
                <div className="text-right">
                  {discountAmount > 0 && (
                    <span className="mr-1.5 text-xs text-gray-400 line-through">
                      {rawTotal} TL
                    </span>
                  )}
                  <span className="font-bold text-purple-600">
                    {totalPrice === 0 ? "ÜCRETSİZ" : `${totalPrice} TL`}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Trust signals */}
        <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-green-50">
                <Truck className="h-3.5 w-3.5 text-green-600" />
              </div>
              <div>
                <p className="text-[10px] text-gray-500">Tahmini Teslimat</p>
                <p className="text-xs font-medium text-green-600">
                  {getEstimatedDelivery()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-pink-50">
                <Heart className="h-3.5 w-3.5 text-pink-500" />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-700">
                  Mutluluk Garantisi
                </p>
                <p className="text-[10px] text-gray-500">Beğenmezseniz iade</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-blue-50">
                <Shield className="h-3.5 w-3.5 text-blue-500" />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-700">
                  Güvenli Ödeme
                </p>
                <p className="text-[10px] text-gray-500">
                  SSL + KVKK uyumlu
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile: collapsible bottom bar */}
      {basePrice != null && basePrice > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-gray-200 bg-white shadow-[0_-4px_20px_rgba(0,0,0,0.08)] lg:hidden">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex w-full items-center justify-between px-4 py-3"
          >
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">
                Sipariş Özeti
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-purple-600">
                {totalPrice === 0 ? "ÜCRETSİZ" : `${totalPrice} TL`}
              </span>
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-gray-400" />
              ) : (
                <ChevronUp className="h-4 w-4 text-gray-400" />
              )}
            </div>
          </button>
          {isExpanded && (
            <div className="border-t border-gray-100 px-4 pb-4 pt-2">
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between text-gray-600">
                  <span>{productName}</span>
                  <span>{basePrice} TL</span>
                </div>
                {hasAudioBook && (
                  <div className="flex justify-between text-gray-600">
                    <span>Sesli Kitap</span>
                    <span>{audioPrice} TL</span>
                  </div>
                )}
                <div className="flex justify-between text-green-600">
                  <span>Kargo</span>
                  <span>ÜCRETSİZ</span>
                </div>
                {discountAmount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>İndirim</span>
                    <span>-{discountAmount} TL</span>
                  </div>
                )}
              </div>
              <div className="mt-2 flex items-center gap-4 border-t border-gray-100 pt-2 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Truck className="h-3 w-3" /> Ücretsiz kargo
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" /> 3-5 iş günü
                </span>
                <span className="flex items-center gap-1">
                  <Shield className="h-3 w-3" /> Güvenli ödeme
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
