"use client";

import {
  TrendingUp,
  TrendingDown,
  Percent,
  ShoppingCart,
  Ticket,
} from "lucide-react";
import type { AccountingSummary } from "../_lib/accountingApi";

function fmt(n: number) {
  return n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface CardProps {
  title: string;
  value: string;
  sub?: string;
  icon: React.ReactNode;
  color: string;
  bg: string;
}

function StatCard({ title, value, sub, icon, color, bg }: CardProps) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-500 truncate">{title}</p>
          <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
          {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
        </div>
        <div className={`${bg} flex-shrink-0 rounded-xl p-3 ml-3`}>
          <span className={color}>{icon}</span>
        </div>
      </div>
    </div>
  );
}

interface Props {
  data: AccountingSummary | null;
  loading: boolean;
}

export default function SummaryCards({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-xl bg-slate-100" />
        ))}
      </div>
    );
  }

  const cards: CardProps[] = [
    {
      title: "Brüt Gelir",
      value: `${fmt(data.gross_revenue)} ₺`,
      sub: `${data.order_count} sipariş`,
      icon: <TrendingUp className="h-5 w-5" />,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
    },
    {
      title: "Net Gelir",
      value: `${fmt(data.net_revenue)} ₺`,
      sub: "indirim sonrası",
      icon: <TrendingUp className="h-5 w-5" />,
      color: "text-indigo-600",
      bg: "bg-indigo-50",
    },
    {
      title: "Toplam İndirim",
      value: `${fmt(data.total_discount)} ₺`,
      sub: `${data.promo_used_count} kupon kullanıldı`,
      icon: <Ticket className="h-5 w-5" />,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
    {
      title: "KDV Tutarı",
      value: `${fmt(data.vat_amount)} ₺`,
      sub: `KDV hariç: ${fmt(data.revenue_ex_vat)} ₺`,
      icon: <Percent className="h-5 w-5" />,
      color: "text-violet-600",
      bg: "bg-violet-50",
    },
    {
      title: "İade Toplamı",
      value: `${fmt(data.refund_total)} ₺`,
      sub: "iade edilen tutarlar",
      icon: <TrendingDown className="h-5 w-5" />,
      color: "text-red-600",
      bg: "bg-red-50",
    },
    {
      title: "Ek Ürünler",
      value: `${data.audio_book_count + data.coloring_book_count}`,
      sub: `${data.audio_book_count} sesli · ${data.coloring_book_count} boyama`,
      icon: <ShoppingCart className="h-5 w-5" />,
      color: "text-cyan-600",
      bg: "bg-cyan-50",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {cards.map((c) => (
        <StatCard key={c.title} {...c} />
      ))}
    </div>
  );
}
