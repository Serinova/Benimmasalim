"use client";

import React from "react";
import { getStatusColor, getStatusLabel } from "../_lib/constants";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

export const StatusBadge = React.memo(function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const colorClass = getStatusColor(status);
  const label = getStatusLabel(status);
  const sizeClass = size === "sm"
    ? "px-2 py-0.5 text-[11px]"
    : "px-2.5 py-1 text-xs";

  return (
    <span className={`inline-flex items-center rounded-md border font-medium ${colorClass} ${sizeClass}`}>
      {label}
    </span>
  );
});
