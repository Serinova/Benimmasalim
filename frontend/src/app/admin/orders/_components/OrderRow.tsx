"use client";

import React from "react";
import type { OrderListItem } from "../_lib/types";
import { StatusBadge } from "./StatusBadge";
import { getCoverThumb } from "../_lib/constants";

interface OrderRowProps {
  item: OrderListItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
  compact?: boolean;
}

export const OrderRow = React.memo(function OrderRow({ item, isSelected, onSelect, compact = false }: OrderRowProps) {
  const coverUrl = getCoverThumb(item);
  const imageCount = item.image_count ?? (item.page_images ? Object.keys(item.page_images).length : 0);

  return (
    <tr
      className={`cursor-pointer border-b border-slate-100 transition-colors hover:bg-slate-50 ${
        isSelected ? "bg-violet-50 hover:bg-violet-50" : ""
      }`}
      onClick={() => onSelect(item.id)}
    >
      {/* Order ID */}
      <td className="whitespace-nowrap px-3 py-2.5">
        <span className="font-mono text-xs text-slate-600">{item.id.slice(0, 8)}</span>
      </td>

      {/* Date */}
      <td className="whitespace-nowrap px-3 py-2.5">
        <div className="text-xs text-slate-700">
          {new Date(item.created_at).toLocaleDateString("tr-TR")}
        </div>
        <div className="text-[10px] text-slate-400">
          {new Date(item.created_at).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })}
        </div>
      </td>

      {/* Customer */}
      <td className="max-w-[180px] px-3 py-2.5">
        <div className="truncate text-xs font-medium text-slate-800">{item.parent_name}</div>
        <div className="truncate text-[10px] text-slate-400">{item.parent_email}</div>
      </td>

      {/* Child / Scenario */}
      {!compact && (
        <td className="max-w-[160px] px-3 py-2.5">
          <div className="flex items-center gap-2">
            {coverUrl ? (
              <img
                src={coverUrl}
                alt=""
                className="h-8 w-6 flex-shrink-0 rounded object-cover"
                loading="lazy"
                decoding="async"
              />
            ) : (
              <div className="flex h-8 w-6 flex-shrink-0 items-center justify-center rounded bg-slate-100 text-[10px]">
                📖
              </div>
            )}
            <div className="min-w-0">
              <div className="truncate text-xs font-medium text-slate-800">
                {item.child_name} <span className="font-normal text-slate-400">({item.child_age})</span>
              </div>
              <div className="truncate text-[10px] text-slate-400">{item.scenario_name || "—"}</div>
            </div>
          </div>
        </td>
      )}

      {/* Status */}
      <td className="px-3 py-2.5">
        <StatusBadge status={item.status} />
      </td>

      {/* Price */}
      <td className="whitespace-nowrap px-3 py-2.5 text-right">
        {item.product_price ? (
          <span className="text-xs font-semibold text-slate-700">
            {item.product_price.toLocaleString("tr-TR")} ₺
          </span>
        ) : (
          <span className="text-xs text-slate-300">—</span>
        )}
      </td>

      {/* Production */}
      <td className="whitespace-nowrap px-3 py-2.5 text-center">
        <span className="text-xs text-slate-600">
          {imageCount}/{item.page_count}
        </span>
      </td>

      {/* Tags */}
      {!compact && (
        <td className="px-3 py-2.5">
          <div className="flex flex-wrap gap-1">
            {item.has_audio_book && (
              <span className="rounded bg-indigo-50 px-1.5 py-0.5 text-[9px] font-medium text-indigo-600">Sesli</span>
            )}
            {item.has_coloring_book && (
              <span className="rounded bg-pink-50 px-1.5 py-0.5 text-[9px] font-medium text-pink-600">Boyama</span>
            )}
            {item.visual_style_name && (
              <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[9px] text-blue-600">{item.visual_style_name}</span>
            )}
          </div>
        </td>
      )}
    </tr>
  );
});
