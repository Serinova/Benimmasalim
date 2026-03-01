"use client";

import { useState } from "react";
import { Loader2, Tag, X, Check } from "lucide-react";

interface PromoCodeInputProps {
  onApply: (code: string) => Promise<void>;
  onClear: () => void;
  loading: boolean;
  appliedCode: string | null;
  discountAmount: number;
  error: string | null;
}

export default function PromoCodeInput({
  onApply,
  onClear,
  loading,
  appliedCode,
  discountAmount,
  error,
}: PromoCodeInputProps) {
  const [input, setInput] = useState(appliedCode || "");

  if (appliedCode) {
    return (
      <div className="flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 px-3 py-2.5">
        <Check className="h-4 w-4 text-green-600 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-green-700">{appliedCode}</p>
          <p className="text-xs text-green-600">-{discountAmount} ₺ indirim uygulandı</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setInput("");
            onClear();
          }}
          className="p-1 rounded-full hover:bg-green-100 text-green-600"
          aria-label="Kuponu kaldır"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Tag className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase())}
            placeholder="Kupon kodu"
            maxLength={50}
            className={`
              w-full rounded-xl border-2 bg-white pl-9 pr-3 py-2.5 text-sm font-medium uppercase
              placeholder:text-gray-300 placeholder:normal-case outline-none transition-all
              ${error ? "border-red-300" : "border-gray-200 focus:border-purple-400"}
            `}
          />
        </div>
        <button
          type="button"
          onClick={() => input.trim() && onApply(input.trim())}
          disabled={!input.trim() || loading}
          className="h-[42px] px-4 rounded-xl bg-purple-600 text-white text-sm font-semibold disabled:bg-gray-200 disabled:text-gray-400 transition-colors flex items-center gap-1.5"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Uygula"}
        </button>
      </div>
      {error && (
        <p className="text-xs text-red-500 font-medium">{error}</p>
      )}
    </div>
  );
}
