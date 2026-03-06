"use client";

import { AnimatePresence, motion } from "framer-motion";
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
    <div className="create-flow relative min-h-[100dvh] w-full max-w-[100vw] overflow-x-hidden bg-[#fdf8ff] text-sm touch-manipulation">
      {/* Background decor — motion.prefers-reduced-motion handled via CSS */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden" aria-hidden="true">
        <div className="wizard-blob absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-purple-200/30 blur-3xl" />
        <div className="wizard-blob animation-delay-1s absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-pink-200/25 blur-3xl" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 w-full px-3 py-2 sm:px-4 sm:py-3">
        <div className="mx-auto max-w-lg">
          <div className="rounded-2xl border border-white/40 bg-white/80 px-3 py-2 shadow-sm backdrop-blur-xl sm:px-4 sm:py-3">
            <StepProgress
              currentStep={currentStep}
              maxReached={maxReached}
              onStepClick={onStepClick}
            />
          </div>
        </div>
      </header>

      {/* Main content — bottom padding respects safe-area + CTA bar height */}
      <main
        className="mx-auto w-full max-w-5xl px-3 py-2 sm:px-4"
        style={{ paddingBottom: "calc(7rem + env(safe-area-inset-bottom, 0px))" }}
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
