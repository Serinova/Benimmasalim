export interface PriceBreakdown {
  basePrice: number;
  audioPrice: number;
  coloringBookPrice: number;
  discount: number;
  subtotal: number;
  total: number;
  promoCode: string | null;
}

export function calculatePricing(params: {
  basePrice: number;
  hasAudioBook: boolean;
  audioType: "system" | "cloned";
  hasColoringBook: boolean;
  coloringBookPrice: number;
  discountAmount?: number;
  promoCode?: string | null;
}): PriceBreakdown {
  const audioPrice = params.hasAudioBook
    ? params.audioType === "cloned"
      ? 300
      : 150
    : 0;
  const coloringBookPrice = params.hasColoringBook ? params.coloringBookPrice : 0;
  const subtotal = params.basePrice + audioPrice + coloringBookPrice;
  const discount = params.discountAmount ?? 0;
  const total = Math.max(0, subtotal - discount);

  return {
    basePrice: params.basePrice,
    audioPrice,
    coloringBookPrice,
    discount,
    subtotal,
    total,
    promoCode: params.promoCode ?? null,
  };
}

export { formatPrice } from "@/lib/utils";
