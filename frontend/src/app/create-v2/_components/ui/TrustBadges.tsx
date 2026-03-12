"use client";

import { ShieldCheck, Truck, Heart, Star, Lock } from "lucide-react";

interface TrustBadgesProps {
  variant?: "inline" | "grid";
  className?: string;
}

const BADGES = [
  { icon: Lock, label: "SSL Şifreli", color: "text-emerald-500" },
  { icon: ShieldCheck, label: "KVKK Uyumlu", color: "text-blue-500" },
  { icon: Truck, label: "Ücretsiz Kargo", color: "text-violet-500" },
  { icon: Heart, label: "Mutluluk Garantisi", color: "text-pink-500" },
  { icon: Star, label: "4.9/5 Puan", color: "text-amber-500" },
];

export default function TrustBadges({ variant = "inline", className = "" }: TrustBadgesProps) {
  if (variant === "grid") {
    return (
      <div className={`grid grid-cols-2 sm:grid-cols-3 gap-2 ${className}`}>
        {BADGES.map((b) => (
          <div
            key={b.label}
            className="flex items-center gap-1.5 rounded-lg bg-slate-50/60 px-2.5 py-1.5"
          >
            <b.icon className={`h-3.5 w-3.5 flex-shrink-0 ${b.color}`} />
            <span className="text-[11px] font-medium text-slate-500">{b.label}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`flex flex-wrap items-center justify-center gap-x-4 gap-y-1 ${className}`}>
      {BADGES.map((b) => (
        <span
          key={b.label}
          className="flex items-center gap-1 text-[10px] sm:text-[11px] text-slate-400"
        >
          <b.icon className={`h-3 w-3 ${b.color}`} />
          {b.label}
        </span>
      ))}
    </div>
  );
}
