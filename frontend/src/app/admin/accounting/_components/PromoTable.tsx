"use client";

import { Ticket, CheckCircle2, XCircle } from "lucide-react";
import type { PromoStat } from "../_lib/accountingApi";

function fmt(n: number) {
  return n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface Props {
  data: PromoStat[];
  loading: boolean;
}

export default function PromoTable({ data, loading }: Props) {
  if (loading) {
    return <div className="h-48 animate-pulse rounded-xl bg-slate-100" />;
  }

  if (!data.length) {
    return (
      <div className="flex h-24 items-center justify-center rounded-xl bg-slate-50">
        <p className="text-sm text-slate-400">Bu dönemde kupon kullanımı yok</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
            <th className="pb-3 pr-4">Kupon Kodu</th>
            <th className="pb-3 pr-4">Tür / Değer</th>
            <th className="pb-3 pr-4 text-right">Kullanım</th>
            <th className="pb-3 pr-4 text-right">İndirim Toplamı</th>
            <th className="pb-3 pr-4 text-right">Brüt Ciro</th>
            <th className="pb-3 text-right">İndirim %</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {data.map((row) => (
            <tr key={row.code} className="hover:bg-slate-50">
              <td className="py-3 pr-4">
                <div className="flex items-center gap-2">
                  <Ticket className="h-4 w-4 text-amber-500 shrink-0" />
                  <span className="font-mono font-semibold text-slate-800">{row.code}</span>
                  {row.is_active === true && (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" title="Aktif" />
                  )}
                  {row.is_active === false && (
                    <XCircle className="h-3.5 w-3.5 text-slate-400" title="Pasif" />
                  )}
                </div>
              </td>
              <td className="py-3 pr-4 text-slate-600">
                {row.discount_type === "PERCENT"
                  ? `%${row.discount_value} indirim`
                  : row.discount_type === "AMOUNT"
                    ? `${row.discount_value} ₺ indirim`
                    : "-"}
              </td>
              <td className="py-3 pr-4 text-right font-medium text-slate-700">{row.uses}</td>
              <td className="py-3 pr-4 text-right font-semibold text-amber-600">
                {fmt(row.total_discount)} ₺
              </td>
              <td className="py-3 pr-4 text-right text-slate-600">{fmt(row.gross_before_discount)} ₺</td>
              <td className="py-3 text-right">
                <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700">
                  %{row.discount_pct.toFixed(1)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t border-slate-200 font-semibold text-slate-900">
            <td colSpan={2} className="pt-3 pr-4 text-xs uppercase text-slate-500">
              Toplam
            </td>
            <td className="pt-3 pr-4 text-right">{data.reduce((s, r) => s + r.uses, 0)}</td>
            <td className="pt-3 pr-4 text-right text-amber-700">
              {fmt(data.reduce((s, r) => s + r.total_discount, 0))} ₺
            </td>
            <td className="pt-3 pr-4 text-right">
              {fmt(data.reduce((s, r) => s + r.gross_before_discount, 0))} ₺
            </td>
            <td className="pt-3" />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
