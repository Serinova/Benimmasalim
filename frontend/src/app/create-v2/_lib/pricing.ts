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
  const base = Number(params.basePrice) || 0;
  const audioPrice = params.hasAudioBook
    ? params.audioType === "cloned"
      ? 300
      : 150
    : 0;
  const coloringBookPrice = params.hasColoringBook ? (Number(params.coloringBookPrice) || 0) : 0;
  const subtotal = base + audioPrice + coloringBookPrice;
  const discount = Number(params.discountAmount) || 0;
  const total = Math.max(0, subtotal - discount);

  return {
    basePrice: base,
    audioPrice,
    coloringBookPrice,
    discount,
    subtotal,
    total,
    promoCode: params.promoCode ?? null,
  };
}

export { formatPrice } from "@/lib/utils";
