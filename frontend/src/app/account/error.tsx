"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

export default function AccountError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Account error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-4">
      <AlertTriangle className="h-12 w-12 text-amber-500" />
      <h2 className="mt-4 text-lg font-semibold text-gray-900">Bir şeyler ters gitti</h2>
      <p className="mt-1 text-sm text-gray-500">
        Sayfa yüklenirken bir hata oluştu. Lütfen tekrar deneyin.
      </p>
      <Button
        onClick={reset}
        className="mt-6 rounded-xl bg-purple-600 hover:bg-purple-700"
      >
        Tekrar Dene
      </Button>
    </div>
  );
}
