"use client";

import ImagePreviewStep from "@/components/ImagePreviewStep";
import GenerationProgressUI from "../ui/GenerationProgress";
import StickyCTA from "../StickyCTA";
import type { GenerationProgress } from "@/lib/api";

interface PreviewStepProps {
  childName: string;
  previewImages: Record<string, string>;
  backCoverImageUrl?: string | null;
  isLoading: boolean;
  generationProgress: GenerationProgress | null;
  errorMessage: string | null;
  onApprove: () => void;
  onBack: () => void;
  onRetry: () => void;
}

export default function PreviewStep({
  childName,
  previewImages,
  backCoverImageUrl,
  isLoading,
  generationProgress,
  errorMessage,
  onApprove,
  onBack,
  onRetry,
}: PreviewStepProps) {
  const hasImages = Object.keys(previewImages).length > 0;

  if (isLoading && !hasImages) {
    return (
      <div className="pb-24">
        <GenerationProgressUI progress={generationProgress} isLoading />
        <StickyCTA
          primaryLabel="Lütfen bekleyin..."
          onPrimary={() => {}}
          primaryDisabled
          secondaryLabel="← Geri"
          onSecondary={onBack}
        />
      </div>
    );
  }

  if (errorMessage && !hasImages) {
    return (
      <div className="pb-24">
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
          <div className="mb-4 h-16 w-16 rounded-2xl bg-red-100 flex items-center justify-center text-3xl">
            😔
          </div>
          <h2 className="text-lg font-bold text-gray-800 mb-2">Bir Sorun Oluştu</h2>
          <p className="text-sm text-gray-500 mb-6 max-w-sm">{errorMessage}</p>
        </div>
        <StickyCTA
          primaryLabel="Tekrar Dene"
          onPrimary={onRetry}
          secondaryLabel="← Geri"
          onSecondary={onBack}
        />
      </div>
    );
  }

  return (
    <div className="pb-24">
      <div className="mb-4">
        <p className="text-[10px] sm:text-xs font-semibold text-purple-500 uppercase tracking-wider mb-0.5">
          Adım 3
        </p>
        <h2 className="text-lg sm:text-xl font-bold text-gray-800">
          Kitabınız Hazır!
        </h2>
        <p className="text-xs sm:text-sm text-gray-500 mt-1">
          Önizlemeyi inceleyin ve onaylayın
        </p>
      </div>

      <ImagePreviewStep
        childName={childName}
        previewImages={previewImages}
        backCoverImageUrl={backCoverImageUrl}
        onApprove={onApprove}
        onBack={onBack}
        isLoading={isLoading}
        generationProgress={generationProgress}
      />

      {hasImages && !isLoading && (
        <StickyCTA
          primaryLabel="Harika! Devam Et"
          onPrimary={onApprove}
          secondaryLabel="← Geri"
          onSecondary={onBack}
        />
      )}
    </div>
  );
}
