"use client";

import { Image as ImageIcon } from "lucide-react";
import type { Scenario } from "../_lib/types";

interface ScenarioPreviewProps {
  scenario: Partial<Scenario>;
}

export function ScenarioPreview({ scenario }: ScenarioPreviewProps) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-600 to-pink-500">
      {/* Thumbnail */}
      <div className="relative aspect-[4/3]">
        {scenario.thumbnail_url ? (
          <img
            src={scenario.thumbnail_url}
            alt={scenario.name || "Preview"}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-purple-200">
            <ImageIcon className="h-12 w-12 text-purple-400" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="bg-white p-3">
        <h3 className="font-bold text-gray-900">{scenario.name || "Senaryo Adı"}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-gray-500">
          {scenario.description || "Açıklama..."}
        </p>

        {/* Gallery preview */}
        {scenario.gallery_images && scenario.gallery_images.length > 0 && (
          <div className="mt-2 flex gap-1">
            {scenario.gallery_images.slice(0, 3).map((img, i) => (
              <div key={i} className="h-8 w-8 overflow-hidden rounded">
                <img src={img} alt={`Gallery ${i}`} className="h-full w-full object-cover" />
              </div>
            ))}
            {scenario.gallery_images.length > 3 && (
              <span className="flex items-center text-xs text-gray-400">
                +{scenario.gallery_images.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
