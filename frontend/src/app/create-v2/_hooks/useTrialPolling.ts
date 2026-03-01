"use client";

import { useRef, useCallback } from "react";
import { getTrialStatus, getTrialPreview } from "@/lib/api";
import type { GenerationProgress } from "@/lib/api";
import { POLLING_INTERVAL_MS, POLLING_MAX_ATTEMPTS } from "../_lib/constants";

interface UseTrialPollingOptions {
  onProgress: (progress: GenerationProgress) => void;
  onPreviewReady: (images: Record<string, string>) => void;
  onError: (message: string) => void;
  onComplete: () => void;
}

export function useTrialPolling(options: UseTrialPollingOptions) {
  const abortRef = useRef<AbortController | null>(null);
  const attemptRef = useRef(0);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    attemptRef.current = 0;
  }, []);

  const start = useCallback(
    (trialId: string, trialToken?: string) => {
      stop();
      const controller = new AbortController();
      abortRef.current = controller;
      attemptRef.current = 0;

      const poll = async () => {
        if (controller.signal.aborted) return;
        attemptRef.current += 1;

        if (attemptRef.current > POLLING_MAX_ATTEMPTS) {
          options.onError("Önizleme zaman aşımına uğradı. Lütfen tekrar deneyin.");
          options.onComplete();
          return;
        }

        try {
          const status = await getTrialStatus(trialId, trialToken);

          if (controller.signal.aborted) return;

          if (status.generation_progress) {
            options.onProgress(status.generation_progress);
          }

          if (status.is_failed) {
            options.onError("Önizleme oluşturulamadı. Lütfen tekrar deneyin.");
            options.onComplete();
            return;
          }

          if (status.is_preview_ready) {
            const preview = await getTrialPreview(trialId, trialToken);
            if (preview.success && preview.preview_images) {
              options.onPreviewReady(preview.preview_images);
            }
            options.onComplete();
            return;
          }

          setTimeout(poll, POLLING_INTERVAL_MS);
        } catch {
          if (!controller.signal.aborted) {
            options.onError("Bağlantı hatası. Lütfen tekrar deneyin.");
            options.onComplete();
          }
        }
      };

      poll();
    },
    [options, stop],
  );

  return { start, stop };
}
