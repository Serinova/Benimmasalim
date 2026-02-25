"use client";

import { Check } from "lucide-react";

export interface StepDef {
  label: string;
  shortLabel: string;
  icon: React.ReactNode;
}

interface StepIndicatorProps {
  steps: StepDef[];
  currentStep: number;
  /** Highest step the user has reached (for clickable navigation) */
  maxReached: number;
  onStepClick?: (step: number) => void;
}

export default function StepIndicator({
  steps,
  currentStep,
  maxReached,
  onStepClick,
}: StepIndicatorProps) {
  return (
    <nav aria-label="Sipariş adımları" className="w-full">
      {/* Desktop stepper */}
      <ol className="hidden items-center sm:flex">
        {steps.map((s, idx) => {
          const stepNum = idx + 1;
          const isActive = currentStep === stepNum;
          const isCompleted = currentStep > stepNum;
          const isReachable = stepNum <= maxReached && stepNum !== currentStep;

          return (
            <li
              key={s.label}
              className="flex flex-1 items-center last:flex-none"
            >
              <button
                type="button"
                disabled={!isReachable}
                onClick={() => isReachable && onStepClick?.(stepNum)}
                className={`
                  group flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-all
                  ${isReachable ? "cursor-pointer hover:bg-purple-50" : "cursor-default"}
                  ${isActive ? "text-purple-700" : isCompleted ? "text-green-600" : "text-gray-400"}
                `}
                aria-current={isActive ? "step" : undefined}
              >
                <span
                  className={`
                    flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all
                    ${isActive ? "bg-purple-600 text-white ring-4 ring-purple-100" : ""}
                    ${isCompleted ? "bg-green-500 text-white" : ""}
                    ${!isActive && !isCompleted ? "bg-gray-100 text-gray-400" : ""}
                  `}
                >
                  {isCompleted ? <Check className="h-3.5 w-3.5" /> : stepNum}
                </span>
                <span className="hidden lg:inline">{s.label}</span>
                <span className="lg:hidden">{s.shortLabel}</span>
              </button>

              {/* Connector line */}
              {idx < steps.length - 1 && (
                <div className="mx-1 h-0.5 flex-1">
                  <div
                    className={`h-full rounded-full transition-all ${
                      currentStep > stepNum ? "bg-green-400" : "bg-gray-200"
                    }`}
                  />
                </div>
              )}
            </li>
          );
        })}
      </ol>

      {/* Mobile stepper — compact dots + current label */}
      <div className="flex flex-col items-center gap-2 sm:hidden">
        <div className="flex items-center gap-1.5">
          {steps.map((s, idx) => {
            const stepNum = idx + 1;
            const isActive = currentStep === stepNum;
            const isCompleted = currentStep > stepNum;
            const isReachable = stepNum <= maxReached && stepNum !== currentStep;

            return (
              <button
                key={s.label}
                type="button"
                disabled={!isReachable}
                onClick={() => isReachable && onStepClick?.(stepNum)}
                aria-label={`${s.label} - Adım ${stepNum}`}
                className={`
                  flex items-center justify-center rounded-full transition-all
                  ${isActive ? "h-7 w-7 bg-purple-600 text-xs font-bold text-white ring-2 ring-purple-100" : ""}
                  ${isCompleted ? "h-5 w-5 bg-green-500 text-white" : ""}
                  ${!isActive && !isCompleted ? "h-3 w-3 bg-gray-200" : ""}
                  ${isReachable ? "cursor-pointer" : "cursor-default"}
                `}
              >
                {isActive && stepNum}
                {isCompleted && <Check className="h-3 w-3" />}
              </button>
            );
          })}
        </div>
        <p className="text-xs font-medium text-purple-700">
          {steps[currentStep - 1]?.label}
        </p>
      </div>
    </nav>
  );
}
