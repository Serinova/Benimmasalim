"use client";

import { Check } from "lucide-react";
import { STEPS } from "../_lib/constants";

interface StepProgressProps {
  currentStep: number;
  maxReached: number;
  onStepClick?: (step: number) => void;
}

const STEP_EMOJIS = ["✨", "📸", "📖", "🎁", "💳"];

export default function StepProgress({
  currentStep,
  maxReached,
  onStepClick,
}: StepProgressProps) {
  return (
    <nav aria-label="Sipariş adımları" className="w-full">
      {/* Desktop */}
      <ol className="hidden items-center sm:flex">
        {STEPS.map((s, idx) => {
          const isActive = currentStep === s.id;
          const isCompleted = currentStep > s.id;
          const isReachable = s.id <= maxReached && s.id !== currentStep;

          return (
            <li key={s.id} className="flex flex-1 items-center last:flex-none">
              <button
                type="button"
                disabled={!isReachable}
                onClick={() => isReachable && onStepClick?.(s.id)}
                className={`
                  group flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-all
                  ${isReachable ? "cursor-pointer hover:bg-violet-50" : "cursor-default"}
                  ${isActive ? "text-violet-700" : isCompleted ? "text-emerald-600" : "text-slate-400"}
                `}
                aria-current={isActive ? "step" : undefined}
              >
                <span
                  className={`
                    flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold transition-all
                    ${isActive ? "bg-violet-600 text-white ring-4 ring-violet-100" : ""}
                    ${isCompleted ? "bg-emerald-500 text-white" : ""}
                    ${!isActive && !isCompleted ? "bg-slate-100 text-slate-400" : ""}
                  `}
                >
                  {isCompleted ? <Check className="h-3.5 w-3.5" /> : s.id}
                </span>
                <span className="hidden lg:inline">{s.label}</span>
                <span className="lg:hidden">{s.shortLabel}</span>
              </button>

              {idx < STEPS.length - 1 && (
                <div className="mx-1 h-0.5 flex-1">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      currentStep > s.id ? "bg-emerald-400" : "bg-slate-200"
                    }`}
                  />
                </div>
              )}
            </li>
          );
        })}
      </ol>

      {/* Mobile — improved mini progress */}
      <div className="flex flex-col gap-1.5 sm:hidden">
        {/* Step dots + progress bar */}
        <div className="flex items-center gap-1" role="list">
          {STEPS.map((s, idx) => {
            const isActive = currentStep === s.id;
            const isCompleted = currentStep > s.id;
            const isReachable = s.id <= maxReached && s.id !== currentStep;

            return (
              <div key={s.id} className="flex flex-1 items-center last:flex-none">
                <button
                  type="button"
                  role="listitem"
                  disabled={!isReachable}
                  onClick={() => isReachable && onStepClick?.(s.id)}
                  aria-label={`${s.label}${isCompleted ? " — Tamamlandı" : isActive ? " — Aktif adım" : ""}`}
                  aria-current={isActive ? "step" : undefined}
                  className={`
                    relative flex items-center justify-center rounded-full transition-all
                    ${isActive ? "h-7 w-7 bg-violet-600 text-[10px] font-bold text-white ring-2 ring-violet-200 ring-offset-1" : ""}
                    ${isCompleted ? "h-5 w-5 bg-emerald-500 text-white" : ""}
                    ${!isActive && !isCompleted ? "h-2.5 w-2.5 bg-slate-200" : ""}
                    ${isReachable ? "cursor-pointer" : "cursor-default"}
                  `}
                  style={
                    !isActive && !isCompleted
                      ? { padding: "calc((44px - 10px) / 2)" }
                      : isCompleted
                      ? { padding: "calc((44px - 20px) / 2)" }
                      : { padding: "calc((44px - 28px) / 2)" }
                  }
                >
                  {isActive && <span>{STEP_EMOJIS[s.id - 1]}</span>}
                  {isCompleted && <Check className="h-3 w-3" />}
                </button>

                {idx < STEPS.length - 1 && (
                  <div className="mx-0.5 h-[2px] flex-1">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        currentStep > s.id ? "bg-emerald-400" : "bg-slate-200"
                      }`}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Label */}
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold text-violet-700">
            {STEPS[currentStep - 1]?.label}
          </p>
          <p className="text-[10px] text-slate-400 tabular-nums">
            Adım {currentStep}/{STEPS.length}
          </p>
        </div>
      </div>
    </nav>
  );
}
