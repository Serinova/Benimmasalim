"use client";

import { AnimatePresence, motion } from "framer-motion";
import { HelpCircle } from "lucide-react";
import StepProgress from "./StepProgress";

interface WizardShellProps {
  currentStep: number;
  maxReached: number;
  onStepClick: (step: number) => void;
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  showSidebar?: boolean;
}

export default function WizardShell({
  currentStep,
  maxReached,
  onStepClick,
  children,
  sidebar,
  showSidebar = false,
}: WizardShellProps) {
  return (
    <div className="create-flow relative min-h-[100dvh] w-full max-w-[100vw] overflow-x-hidden bg-gradient-to-b from-violet-50/40 via-white to-rose-50/20 text-sm touch-manipulation">
      {/* Background decor */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden" aria-hidden="true">
        <div className="wizard-blob absolute top-[-12%] left-[-12%] w-[45%] h-[45%] rounded-full bg-violet-100/25 blur-[100px]" />
        <div className="wizard-blob animation-delay-1s absolute bottom-[-12%] right-[-12%] w-[45%] h-[45%] rounded-full bg-pink-100/20 blur-[100px]" />
        <div className="wizard-blob animation-delay-2s absolute top-[40%] right-[-8%] w-[30%] h-[30%] rounded-full bg-amber-50/20 blur-[80px]" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 w-full px-3 py-2 sm:px-4 sm:py-2.5">
        <div className="mx-auto max-w-lg">
          <div className="rounded-2xl border border-white/50 bg-white/85 px-3 py-2 shadow-sm backdrop-blur-xl sm:px-4 sm:py-2.5">
            {/* Brand + Help row */}
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-bold tracking-wide text-violet-600 uppercase">
                Benim Masalım
              </span>
              <a
                href="https://wa.me/905551234567"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 rounded-full bg-slate-50 px-2 py-0.5 text-[10px] font-medium text-slate-500 transition-colors hover:bg-slate-100"
              >
                <HelpCircle className="h-3 w-3" />
                Yardım
              </a>
            </div>
            {/* Stepper */}
            <StepProgress
              currentStep={currentStep}
              maxReached={maxReached}
              onStepClick={onStepClick}
            />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main
        className="mx-auto w-full max-w-5xl px-3 py-2 sm:px-4"
        style={{ paddingBottom: "calc(8rem + env(safe-area-inset-bottom, 0px))" }}
      >
        <div className={`flex ${showSidebar ? "flex-col lg:flex-row lg:gap-6" : "flex-col items-center"}`}>
          <div className={showSidebar ? "flex-1 min-w-0" : "w-full max-w-2xl"}>
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.18 }}
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </div>

          {showSidebar && sidebar && (
            <div className="hidden w-80 flex-shrink-0 lg:block lg:sticky lg:top-24">
              {sidebar}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
