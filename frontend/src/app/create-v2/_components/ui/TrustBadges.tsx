"use client";

import { Shield, Truck, Headphones } from "lucide-react";

export default function TrustBadges() {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4 py-3">
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        <Shield className="h-3.5 w-3.5 text-green-500" />
        <span>256-bit SSL Güvenli Ödeme</span>
      </div>
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        <Truck className="h-3.5 w-3.5 text-blue-500" />
        <span>14 Gün İade Garantisi</span>
      </div>
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        <Headphones className="h-3.5 w-3.5 text-purple-500" />
        <span>7/24 Destek</span>
      </div>
    </div>
  );
}
