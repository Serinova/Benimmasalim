"use client";

import { useId, forwardRef } from "react";
import type { ValidationResult } from "../../_lib/validations";

interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: ValidationResult | null;
  touched?: boolean;
  hint?: string;
}

const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  ({ label, error, touched, hint, className, id: externalId, ...props }, ref) => {
    const generatedId = useId();
    const fieldId = externalId || generatedId;
    const errorId = `${fieldId}-error`;
    const hintId = `${fieldId}-hint`;

    const showError = touched && error && !error.valid;

    return (
      <div className="space-y-1.5">
        <label
          htmlFor={fieldId}
          className="block text-[13px] font-semibold text-gray-600"
        >
          {label}
        </label>
        <input
          ref={ref}
          id={fieldId}
          aria-invalid={showError ? "true" : undefined}
          aria-describedby={
            showError ? errorId : hint ? hintId : undefined
          }
          className={`
            w-full rounded-xl border-2 bg-white px-4 py-3 text-sm text-gray-800
            placeholder:text-gray-300 outline-none transition-all
            ${
              showError
                ? "border-red-400 ring-4 ring-red-100 focus:border-red-500"
                : "border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-100"
            }
            ${className ?? ""}
          `}
          {...props}
        />
        {showError && (
          <p id={errorId} className="text-xs text-red-500 font-medium" role="alert">
            {error.message}
          </p>
        )}
        {!showError && hint && (
          <p id={hintId} className="text-xs text-gray-400">
            {hint}
          </p>
        )}
      </div>
    );
  },
);

FormField.displayName = "FormField";

export default FormField;

/* ── Textarea variant ── */

interface FormTextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: ValidationResult | null;
  touched?: boolean;
  hint?: string;
}

export function FormTextarea({
  label,
  error,
  touched,
  hint,
  className,
  id: externalId,
  ...props
}: FormTextareaProps) {
  const generatedId = useId();
  const fieldId = externalId || generatedId;
  const errorId = `${fieldId}-error`;
  const showError = touched && error && !error.valid;

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={fieldId}
        className="block text-[13px] font-semibold text-gray-600"
      >
        {label}
      </label>
      <textarea
        id={fieldId}
        aria-invalid={showError ? "true" : undefined}
        aria-describedby={showError ? errorId : undefined}
        className={`
          w-full rounded-xl border-2 bg-white px-4 py-3 text-sm text-gray-800
          placeholder:text-gray-300 outline-none transition-all resize-none
          ${
            showError
              ? "border-red-400 ring-4 ring-red-100"
              : "border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-100"
          }
          ${className ?? ""}
        `}
        {...props}
      />
      {showError && (
        <p id={errorId} className="text-xs text-red-500 font-medium" role="alert">
          {error.message}
        </p>
      )}
      {hint && !showError && (
        <p className="text-xs text-gray-400">{hint}</p>
      )}
    </div>
  );
}
