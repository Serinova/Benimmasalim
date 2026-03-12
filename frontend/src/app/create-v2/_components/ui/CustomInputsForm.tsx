"use client";

import FormField from "./FormField";

interface SelectOption {
  label: string;
  value: string;
}

interface FieldSchema {
  key: string;
  label: string;
  type: "text" | "number" | "select" | "textarea";
  required?: boolean;
  options?: (string | SelectOption)[];
}

/** Get display label and value from an option that can be string or {label, value}. */
function getOptionParts(opt: string | SelectOption): { label: string; value: string } {
  if (typeof opt === "string") {
    if (opt === "[object Object]") return { label: "", value: "" };
    return { label: opt, value: opt };
  }
  return { label: opt.label, value: opt.value };
}

interface CustomInputsFormProps {
  fields: FieldSchema[];
  values: Record<string, string>;
  onChange: (vars: Record<string, string>) => void;
}

export default function CustomInputsForm({
  fields,
  values,
  onChange,
}: CustomInputsFormProps) {
  if (!fields || fields.length === 0) return null;

  const handleFieldChange = (key: string, value: string) => {
    onChange({ ...values, [key]: value });
  };

  return (
    <div className="space-y-3">
      <p className="text-xs font-semibold text-violet-600 uppercase tracking-wider">
        Senaryo Detayları
      </p>
      {fields.map((field) => {
        if (field.type === "select" && field.options?.length) {
          return (
            <div key={field.key}>
              <label className="mb-1 block text-xs font-semibold text-slate-600">
                {field.label}
                {field.required && <span className="ml-0.5 text-red-400">*</span>}
              </label>
              <select
                value={values[field.key] || ""}
                onChange={(e) => handleFieldChange(field.key, e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
              >
                <option value="">Seçiniz</option>
                {field.options.map((opt) => {
                  const { label, value } = getOptionParts(opt);
                  if (!label && !value) return null; // Skip corrupted entries
                  return (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  );
                })}
              </select>
            </div>
          );
        }

        if (field.type === "textarea") {
          return (
            <div key={field.key}>
              <label className="mb-1 block text-xs font-semibold text-slate-600">
                {field.label}
                {field.required && <span className="ml-0.5 text-red-400">*</span>}
              </label>
              <textarea
                value={values[field.key] || ""}
                onChange={(e) => handleFieldChange(field.key, e.target.value)}
                rows={3}
                className="w-full resize-none rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                placeholder={field.label}
              />
            </div>
          );
        }

        return (
          <FormField
            key={field.key}
            label={field.label}
            type={field.type === "number" ? "number" : "text"}
            value={values[field.key] || ""}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            placeholder={field.label}
          />
        );
      })}
    </div>
  );
}
