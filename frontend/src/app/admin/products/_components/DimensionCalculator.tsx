"use client";

import { Monitor } from "lucide-react";

interface DimensionCalculatorProps {
  width: number;
  height: number;
}

export function DimensionCalculator({ width, height }: DimensionCalculatorProps) {
  const DPI = 300;
  const pixelWidth = Math.round((width / 25.4) * DPI);
  const pixelHeight = Math.round((height / 25.4) * DPI);
  const orientation = width > height ? "Yatay" : width < height ? "Dikey" : "Kare";
  const aspectRatio = (width / height).toFixed(2);

  return (
    <div className="mt-3 rounded-lg border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Monitor className="h-4 w-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-800">Çıktı Hesaplaması</span>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-gray-500">Hedef Çözünürlük</p>
          <p className="font-mono font-semibold text-blue-700">
            {pixelWidth} × {pixelHeight} px
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">DPI / Oryantasyon</p>
          <p className="font-mono font-semibold text-blue-700">
            {DPI} DPI • {orientation}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">En-Boy Oranı</p>
          <p className="font-mono font-semibold text-blue-700">{aspectRatio}:1</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Tahmini Dosya Boyutu</p>
          <p className="font-mono font-semibold text-blue-700">
            ~{((pixelWidth * pixelHeight * 3) / 1024 / 1024).toFixed(1)} MB
          </p>
        </div>
      </div>
    </div>
  );
}
