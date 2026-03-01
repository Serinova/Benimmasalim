"use client";

import { useMemo, useState } from "react";
import type { RevenuePoint } from "../_lib/accountingApi";

function fmtDate(iso: string, period: "daily" | "weekly" | "monthly") {
  const d = new Date(iso);
  if (period === "monthly") return d.toLocaleDateString("tr-TR", { month: "short", year: "2-digit" });
  if (period === "weekly") return `${d.toLocaleDateString("tr-TR", { day: "numeric", month: "short" })} hf.`;
  return d.toLocaleDateString("tr-TR", { day: "numeric", month: "short" });
}

function fmtMoney(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k ₺`;
  return `${n.toFixed(0)} ₺`;
}

interface Props {
  data: RevenuePoint[];
  period: "daily" | "weekly" | "monthly";
  loading: boolean;
}

const CHART_H = 200;
const CHART_W = 800;
const PAD_L = 56;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 40;
const INNER_W = CHART_W - PAD_L - PAD_R;
const INNER_H = CHART_H - PAD_T - PAD_B;

export default function RevenueChart({ data, period, loading }: Props) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const { points, maxVal, yTicks } = useMemo(() => {
    if (!data.length) return { points: [], maxVal: 0, yTicks: [] };
    const maxVal = Math.max(...data.map((d) => d.net), 1);
    const nice = Math.ceil(maxVal / 5) * 5;
    const step = nice / 4;
    const yTicks = [0, step, step * 2, step * 3, step * 4];
    const n = data.length;
    const points = data.map((d, i) => {
      const x = PAD_L + (i / Math.max(n - 1, 1)) * INNER_W;
      const y = PAD_T + INNER_H - (d.net / nice) * INNER_H;
      return { x, y, d };
    });
    return { points, maxVal: nice, yTicks };
  }, [data]);

  if (loading) {
    return <div className="h-56 animate-pulse rounded-xl bg-slate-100" />;
  }

  if (!data.length) {
    return (
      <div className="flex h-56 items-center justify-center rounded-xl bg-slate-50">
        <p className="text-sm text-slate-400">Bu dönemde veri yok</p>
      </div>
    );
  }

  // Build polyline path
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const areaPath =
    linePath +
    ` L ${points[points.length - 1].x.toFixed(1)} ${(PAD_T + INNER_H).toFixed(1)}` +
    ` L ${points[0].x.toFixed(1)} ${(PAD_T + INNER_H).toFixed(1)} Z`;

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        className="w-full"
        style={{ minWidth: 320 }}
        aria-label="Gelir grafiği"
      >
        {/* Y-axis grid lines + labels */}
        {yTicks.map((tick) => {
          const y = PAD_T + INNER_H - (tick / maxVal) * INNER_H;
          return (
            <g key={tick}>
              <line
                x1={PAD_L}
                y1={y}
                x2={CHART_W - PAD_R}
                y2={y}
                stroke="#e2e8f0"
                strokeWidth={1}
                strokeDasharray="4 3"
              />
              <text x={PAD_L - 4} y={y + 4} textAnchor="end" fontSize={10} fill="#94a3b8">
                {fmtMoney(tick)}
              </text>
            </g>
          );
        })}

        {/* Area fill */}
        <path d={areaPath} fill="url(#gradNet)" opacity={0.25} />

        {/* Line */}
        <path d={linePath} fill="none" stroke="#6366f1" strokeWidth={2.5} strokeLinejoin="round" />

        {/* Data points + hover tooltip */}
        {points.map(({ x, y, d }, i) => {
          const isHovered = hoveredIdx === i;
          const tipW = 130;
          const tipX = Math.min(Math.max(x - tipW / 2, PAD_L), CHART_W - PAD_R - tipW);
          const tipY = y - 52;
          return (
            <g
              key={i}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
              style={{ cursor: "pointer" }}
            >
              {/* Hit area */}
              <rect x={x - 10} y={PAD_T} width={20} height={INNER_H} fill="transparent" />
              <circle cx={x} cy={y} r={isHovered ? 6 : 4} fill="white" stroke="#6366f1" strokeWidth={2} />
              {/* Hover tooltip */}
              {isHovered && (
                <g>
                  <rect x={tipX} y={tipY} width={tipW} height={44} rx={6} fill="#1e293b" opacity={0.92} />
                  <text x={tipX + 8} y={tipY + 14} fontSize={9} fill="#94a3b8">{fmtDate(d.period, period)}</text>
                  <text x={tipX + 8} y={tipY + 28} fontSize={11} fontWeight="bold" fill="white">
                    {d.net.toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺
                  </text>
                  <text x={tipX + 8} y={tipY + 40} fontSize={9} fill="#94a3b8">{d.count} sipariş</text>
                </g>
              )}
            </g>
          );
        })}

        {/* X-axis labels — only show first, middle, last to avoid crowding */}
        {points
          .filter((_, i) => i === 0 || i === points.length - 1 || (points.length > 6 && i === Math.floor(points.length / 2)))
          .map(({ x, d }) => (
            <text
              key={d.period}
              x={x}
              y={CHART_H - 8}
              textAnchor="middle"
              fontSize={10}
              fill="#94a3b8"
            >
              {fmtDate(d.period, period)}
            </text>
          ))}

        {/* Bar chart bars (subtle, behind line) */}
        {points.map(({ x, y, d }, i) => {
          const bw = Math.max(4, (INNER_W / points.length) * 0.5);
          const bh = PAD_T + INNER_H - y;
          return (
            <rect
              key={i}
              x={x - bw / 2}
              y={y}
              width={bw}
              height={bh > 0 ? bh : 0}
              fill="#6366f1"
              opacity={0.12}
              rx={2}
            />
          );
        })}

        {/* Gradient definition */}
        <defs>
          <linearGradient id="gradNet" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.8} />
            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}
