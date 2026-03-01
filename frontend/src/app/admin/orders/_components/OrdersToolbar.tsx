"use client";

import React, { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { STATUS_OPTIONS, getStatusLabel } from "../_lib/constants";
import type { OrderListItem } from "../_lib/types";

interface OrdersToolbarProps {
  statusFilter: string;
  onStatusChange: (status: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  dateFrom: string;
  onDateFromChange: (date: string) => void;
  dateTo: string;
  onDateToChange: (date: string) => void;
  items: OrderListItem[];
  compact: boolean;
  onCompactToggle: () => void;
}

export const OrdersToolbar = React.memo(function OrdersToolbar({
  statusFilter,
  onStatusChange,
  searchQuery,
  onSearchChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  items,
  compact,
  onCompactToggle,
}: OrdersToolbarProps) {
  const [localSearch, setLocalSearch] = useState(searchQuery);

  const handleSearchSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    onSearchChange(localSearch);
  }, [localSearch, onSearchChange]);

  const handleSearchKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      onSearchChange(localSearch);
    }
  }, [localSearch, onSearchChange]);

  const exportCsv = useCallback((data: OrderListItem[]) => {
    if (data.length === 0) return;
    const headers = ["Sipariş No", "Tarih", "Müşteri", "Email", "Telefon", "Çocuk", "Yaş", "Senaryo", "Durum", "Tutar", "Sayfa", "Görsel"];
    const rows = data.map((item) => [
      item.id.slice(0, 8),
      new Date(item.created_at).toLocaleString("tr-TR"),
      item.parent_name,
      item.parent_email,
      item.parent_phone || "",
      item.child_name,
      String(item.child_age),
      item.scenario_name || "",
      item.status,
      item.product_price ? String(item.product_price) : "",
      String(item.page_count),
      String(item.image_count ?? (item.page_images ? Object.keys(item.page_images).length : 0)),
    ]);
    const csvContent = [headers, ...rows].map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `siparisler_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);

  return (
    <div className="space-y-3">
      {/* Search + Date filters */}
      <div className="flex items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md">
          <div className="relative">
            <Input
              type="text"
              placeholder="Sipariş no, müşteri adı, email veya çocuk adı..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="h-9 pl-9 text-sm"
            />
            <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {localSearch && (
              <button
                type="button"
                onClick={() => { setLocalSearch(""); onSearchChange(""); }}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center gap-2">
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => onDateFromChange(e.target.value)}
            className="h-9 w-36 text-xs"
            placeholder="Başlangıç"
          />
          <span className="text-xs text-slate-400">—</span>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => onDateToChange(e.target.value)}
            className="h-9 w-36 text-xs"
            placeholder="Bitiş"
          />
          {(dateFrom || dateTo) && (
            <button
              onClick={() => { onDateFromChange(""); onDateToChange(""); }}
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Temizle
            </button>
          )}
        </div>
      </div>

      {/* Status filters + actions */}
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-1.5">
          {STATUS_OPTIONS.map((status) => (
            <Button
              key={status || "all"}
              variant={statusFilter === status ? "default" : "outline"}
              size="sm"
              className="h-7 text-xs"
              onClick={() => onStatusChange(status)}
            >
              {status === "" ? "Tümü" : getStatusLabel(status)}
            </Button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={onCompactToggle}
          >
            {compact ? "Geniş" : "Kompakt"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={() => exportCsv(items)}
          >
            CSV İndir
          </Button>
        </div>
      </div>
    </div>
  );
});
