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
    <div className="create-flow relative min-h-[100dvh] w-full max-w-[100vw] overflow-x-hidden bg-[#fdf8ff] text-sm touch-manipulation font-outfit">
      {/* Background decor */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-purple-200/40 blur-[120px] animate-pulse" />
        <div
          className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-pink-200/40 blur-[120px] animate-pulse"
          style={{ animationDelay: "1s" }}
        />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 w-full px-3 sm:px-4 py-2 sm:py-3">
        <div className="mx-auto max-w-lg">
          <div className="rounded-2xl bg-white/70 shadow-sm border border-white/40 backdrop-blur-xl px-3 sm:px-4 py-2 sm:py-3">
            <StepProgress
              currentStep={currentStep}
              maxReached={maxReached}
              onStepClick={onStepClick}
            />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto w-full max-w-5xl px-3 sm:px-4 py-2 pb-28 sm:pb-32">
        <div className={`flex ${showSidebar ? "flex-col lg:flex-row lg:gap-6" : "flex-col items-center"}`}>
          <div className={showSidebar ? "flex-1 min-w-0" : "w-full max-w-2xl"}>
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </div>

          {showSidebar && sidebar && (
            <div className="hidden lg:block w-80 flex-shrink-0 sticky top-24">
              {sidebar}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
