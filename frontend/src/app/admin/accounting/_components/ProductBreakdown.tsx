"use client";

import type { ProductRevenue } from "../_lib/accountingApi";

function fmt(n: number) {
  return n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface Props {
  data: ProductRevenue[];
  loading: boolean;
}

export default function ProductBreakdown({ data, loading }: Props) {
  if (loading) {
    return <div className="h-48 animate-pulse rounded-xl bg-slate-100" />;
  }

  if (!data.length) {
    return (
      <div className="flex h-32 items-center justify-center rounded-xl bg-slate-50">
        <p className="text-sm text-slate-400">Bu dönemde veri yok</p>
      </div>
    );
  }

  const maxNet = Math.max(...data.map((d) => d.net), 1);

  return (
    <div className="space-y-4">
      {data.map((row) => {
        const pct = (row.net / maxNet) * 100;
        return (
          <div key={row.product_name}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700 truncate max-w-[200px]">{row.product_name}</span>
              <div className="flex items-center gap-4 text-slate-500 ml-2 shrink-0">
                <span className="text-xs">{row.count} adet</span>
                {row.discount > 0 && (
                  <span className="text-xs text-amber-600">-{fmt(row.discount)} ₺ indirim</span>
                )}
                <span className="font-semibold text-slate-900">{fmt(row.net)} ₺</span>
              </div>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
