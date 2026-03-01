"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { BookOpen, Headphones, ChevronRight } from "lucide-react";
import type { UserTrial } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  COMPLETING: "Kitap Hazırlanıyor",
  COMPLETED: "Tamamlandı",
  PAYMENT_PENDING: "Ödeme Bekliyor",
};

interface AccountTrialDetailSheetProps {
  trial: UserTrial | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AccountTrialDetailSheet({
  trial,
  open,
  onOpenChange,
}: AccountTrialDetailSheetProps) {
  const router = useRouter();
  if (!trial) return null;

  const statusLabel = STATUS_LABELS[trial.status] || trial.status;
  const createUrl = `/create-v2?trialId=${trial.id}&token=${trial.confirmation_token}`;

  const handleDevamEt = () => {
    onOpenChange(false);
    router.push(createUrl);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg p-0">
        <div className="flex h-full flex-col">
          <SheetHeader className="border-b px-6 py-4 bg-purple-50/50">
            <p className="text-xs font-medium uppercase tracking-wider text-purple-600">
              Devam Eden Sipariş
            </p>
            <div className="mt-3 flex items-start gap-3">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-purple-100">
                <BookOpen className="h-6 w-6 text-purple-600" />
              </div>
              <div className="min-w-0 flex-1">
                <SheetTitle className="truncate text-lg text-slate-800">
                  {trial.child_name}
                </SheetTitle>
                <SheetDescription className="mt-0.5 text-slate-500">
                  {trial.story_title}
                </SheetDescription>
                <span className="mt-2 inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700">
                  {statusLabel}
                </span>
              </div>
            </div>
          </SheetHeader>

          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {/* Sipariş bilgileri */}
            <div className="rounded-xl border border-purple-100 bg-purple-50/30 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-700">
                Sipariş Bilgileri
              </h3>
              <div className="space-y-2 text-sm">
                <p className="text-slate-600">
                  <span className="font-medium text-slate-700">Çocuk:</span> {trial.child_name}
                </p>
                <p className="text-slate-600">
                  <span className="font-medium text-slate-700">Hikaye:</span> {trial.story_title}
                </p>
                <p className="text-xs text-slate-500">
                  {new Date(trial.created_at).toLocaleDateString("tr-TR", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </p>
                {trial.product_name && (
                  <p className="text-slate-600">
                    <span className="font-medium text-slate-700">Ürün:</span> {trial.product_name}
                  </p>
                )}
                {trial.product_price != null && (
                  <p className="font-semibold text-purple-600">
                    {trial.product_price.toFixed(2)} TL
                  </p>
                )}
                {trial.has_audio_book && (
                  <div className="flex items-center gap-1.5 text-xs text-blue-600">
                    <Headphones className="h-3.5 w-3.5" />
                    Sesli kitap dahil
                  </div>
                )}
              </div>
            </div>

            {/* Önizleme görselleri */}
            {trial.preview_images && Object.keys(trial.preview_images).length > 0 && (
              <div className="rounded-xl border bg-white p-4">
                <h3 className="mb-3 text-sm font-semibold text-slate-700">
                  Kitap Önizleme
                </h3>
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {Object.entries(trial.preview_images).slice(0, 6).map(([key, url]) => (
                    <img
                      key={key}
                      src={url}
                      alt={`Sayfa ${key}`}
                      className="h-24 w-auto rounded-lg object-cover border"
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Devam Et */}
            <div className="space-y-2 pt-2">
              <p className="text-center text-xs text-slate-500">
                Siparişi tamamlamak için Devam Et butonuna tıklayın
              </p>
              <Button
                onClick={handleDevamEt}
                className="w-full rounded-xl bg-purple-600 hover:bg-purple-700"
              >
                Devam Et
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
