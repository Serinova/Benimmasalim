"use client";

import React, { useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import type { OrderListItem } from "../_lib/types";
import { OrderRow } from "./OrderRow";
import { PAGE_SIZE } from "../_lib/constants";

interface OrdersTableProps {
  items: OrderListItem[];
  total: number;
  currentPage: number;
  loading: boolean;
  error: string | null;
  selectedId: string | null;
  onSelectOrder: (id: string) => void;
  onPageChange: (page: number) => void;
  compact?: boolean;
}

export const OrdersTable = React.memo(function OrdersTable({
  items,
  total,
  currentPage,
  loading,
  error,
  selectedId,
  onSelectOrder,
  onPageChange,
  compact = false,
}: OrdersTableProps) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const tbodyRef = useRef<HTMLTableSectionElement>(null);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!items.length) return;
    const currentIdx = items.findIndex((i) => i.id === selectedId);

    if (e.key === "ArrowDown" || e.key === "j") {
      e.preventDefault();
      const nextIdx = currentIdx < items.length - 1 ? currentIdx + 1 : 0;
      onSelectOrder(items[nextIdx].id);
      tbodyRef.current?.children[nextIdx]?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "ArrowUp" || e.key === "k") {
      e.preventDefault();
      const prevIdx = currentIdx > 0 ? currentIdx - 1 : items.length - 1;
      onSelectOrder(items[prevIdx].id);
      tbodyRef.current?.children[prevIdx]?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && selectedId) {
      e.preventDefault();
      onSelectOrder(selectedId);
    }
  }, [items, selectedId, onSelectOrder]);

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-lg border bg-white py-16">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-violet-500" />
          <span className="text-sm text-slate-500">Siparişler yükleniyor...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center">
        <p className="mb-2 text-sm font-medium text-red-700">Siparişler yüklenemedi</p>
        <p className="text-xs text-red-500">{error}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="rounded-lg border bg-white px-6 py-16 text-center">
        <div className="mb-3 text-3xl">📋</div>
        <p className="mb-1 text-sm font-medium text-slate-600">Sipariş bulunamadı</p>
        <p className="text-xs text-slate-400">Filtreleri değiştirmeyi deneyin</p>
      </div>
    );
  }

  return (
    <div
      className="overflow-hidden rounded-lg border bg-white focus:outline-none focus:ring-2 focus:ring-violet-300"
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      <div className="overflow-x-auto">
        <table className={`w-full ${compact ? "text-[11px]" : ""}`}>
          <thead>
            <tr className="border-b bg-slate-50 text-left">
              <th className="whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Sipariş</th>
              <th className="whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Tarih</th>
              <th className="whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Müşteri</th>
              {!compact && <th className="whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Çocuk / Senaryo</th>}
              <th className="whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Durum</th>
              <th className="whitespace-nowrap px-3 py-2.5 text-right text-[11px] font-semibold uppercase tracking-wider text-slate-500">Tutar</th>
              <th className="whitespace-nowrap px-3 py-2.5 text-center text-[11px] font-semibold uppercase tracking-wider text-slate-500">Üretim</th>
              {!compact && <th className="whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Etiketler</th>}
            </tr>
          </thead>
          <tbody ref={tbodyRef}>
            {items.map((item) => (
              <OrderRow
                key={item.id}
                item={item}
                isSelected={selectedId === item.id}
                onSelect={onSelectOrder}
                compact={compact}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t bg-slate-50 px-4 py-2.5">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            disabled={currentPage === 0}
            onClick={() => onPageChange(currentPage - 1)}
          >
            ← Önceki
          </Button>
          <span className="text-xs text-slate-500">
            {currentPage * PAGE_SIZE + 1}–{Math.min((currentPage + 1) * PAGE_SIZE, total)} / {total}
          </span>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            disabled={currentPage + 1 >= totalPages}
            onClick={() => onPageChange(currentPage + 1)}
          >
            Sonraki →
          </Button>
        </div>
      )}
    </div>
  );
});
