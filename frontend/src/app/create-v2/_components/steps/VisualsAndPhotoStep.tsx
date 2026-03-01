"use client";

import VisualsStep from "@/components/VisualsStep";
import type { VisualStyle } from "@/lib/api";

interface VisualsAndPhotoStepProps {
  childName: string;
  photoPreview: string;
  faceDetected: boolean;
  isAnalyzing: boolean;
  onPhotoSelect: (file: File) => void;
  onClear: () => void;
  onAnalyze: () => Promise<void>;
  visualStyles: VisualStyle[];
  selectedStyle: string;
  customIdWeight: number | null;
  onStyleSelect: (id: string) => void;
  onIdWeightChange: (v: number | null) => void;
  onBack: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export default function VisualsAndPhotoStep(props: VisualsAndPhotoStepProps) {
  return (
    <div className="pb-24 sm:pb-28 max-w-2xl mx-auto">
      {/* Step header */}
      <div className="mb-4 sm:mb-5">
        <p className="text-[10px] sm:text-xs font-semibold text-purple-500 uppercase tracking-wider mb-0.5">
          Adım 2
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-gray-800 leading-tight">
          Fotoğrafını Yükle, Stilini Seç
        </h2>
        <p className="text-xs sm:text-sm text-gray-500 mt-1">
          Çocuğunuzun net bir yüz fotoğrafı yükleyin ve kitabınızın görsel stilini seçin
        </p>
      </div>

      <VisualsStep
        childName={props.childName}
        photoPreview={props.photoPreview}
        faceDetected={props.faceDetected}
        isAnalyzing={props.isAnalyzing}
        onPhotoSelect={props.onPhotoSelect}
        onClear={props.onClear}
        onAnalyze={props.onAnalyze}
        visualStyles={props.visualStyles}
        selectedStyle={props.selectedStyle}
        customIdWeight={props.customIdWeight}
        onStyleSelect={props.onStyleSelect}
        onIdWeightChange={props.onIdWeightChange}
        onBack={props.onBack}
        onSubmit={props.onSubmit}
        isSubmitting={props.isSubmitting}
      />
    </div>
  );
}
