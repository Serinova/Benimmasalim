"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-slate-50 px-4 text-center">
      <div className="text-4xl" aria-hidden="true">📖</div>
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Bir şeyler ters gitti</h1>
        <p className="mt-2 text-slate-500">
          Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.
        </p>
      </div>
      <div className="flex gap-3">
        <Button onClick={reset} variant="outline">
          Tekrar Dene
        </Button>
        <Link href="/">
          <Button>Ana Sayfaya Dön</Button>
        </Link>
      </div>
      {error.digest && (
        <p className="text-xs text-slate-400">Hata kodu: {error.digest}</p>
      )}
    </div>
  );
}
