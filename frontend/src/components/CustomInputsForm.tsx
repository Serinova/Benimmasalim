"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { HelpCircle } from "lucide-react";

// Custom Input Field Schema (from Scenario)
interface CustomInputField {
  key: string;
  label: string;
  type: "text" | "number" | "select" | "textarea";
  default?: string;
  options?: string[];
  required?: boolean;
  placeholder?: string;
  help_text?: string;
}

interface CustomInputsFormProps {
  fields: CustomInputField[];
  values: Record<string, string>;
  onChange: (values: Record<string, string>) => void;
  className?: string;
}

export default function CustomInputsForm({
  fields,
  values,
  onChange,
  className = "",
}: CustomInputsFormProps) {
  if (!fields || fields.length === 0) {
    return null;
  }

  const handleChange = (key: string, value: string) => {
    onChange({ ...values, [key]: value });
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="mb-4 text-center">
        <h3 className="text-lg font-semibold text-gray-800">Hikaye Detayları</h3>
        <p className="text-sm text-gray-500">
          Bu bilgiler hikayenizi özelleştirmek için kullanılacak
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {fields.map((field) => (
          <div key={field.key} className="space-y-1.5">
            <Label htmlFor={field.key} className="flex items-center gap-1.5">
              {field.label}
              {field.required && <span className="text-red-500">*</span>}
              {field.help_text && (
                <span className="cursor-help text-gray-400" title={field.help_text}>
                  <HelpCircle className="h-3.5 w-3.5" />
                </span>
              )}
            </Label>

            {field.type === "text" && (
              <Input
                id={field.key}
                value={values[field.key] || field.default || ""}
                onChange={(e) => handleChange(field.key, e.target.value)}
                placeholder={field.placeholder || `${field.label} girin`}
                className="bg-white"
              />
            )}

            {field.type === "number" && (
              <Input
                id={field.key}
                type="number"
                value={values[field.key] || field.default || ""}
                onChange={(e) => handleChange(field.key, e.target.value)}
                placeholder={field.placeholder || `${field.label} girin`}
                className="bg-white"
              />
            )}

            {field.type === "textarea" && (
              <Textarea
                id={field.key}
                value={values[field.key] || field.default || ""}
                onChange={(e) => handleChange(field.key, e.target.value)}
                placeholder={field.placeholder || `${field.label} girin`}
                rows={3}
                className="resize-none bg-white"
              />
            )}

            {field.type === "select" && field.options && (() => {
              const opts: string[] = Array.isArray(field.options)
                ? field.options.map((o: unknown) =>
                    typeof o === "string"
                      ? o
                      : typeof o === "object" && o !== null
                        ? (o as Record<string, string>).label_tr ?? (o as Record<string, string>).label ?? (o as Record<string, string>).label_en ?? String((o as Record<string, string>).value ?? "")
                        : String(o),
                  )
                : typeof field.options === "string"
                  ? (field.options as string).split(",").map((s: string) => s.trim()).filter(Boolean)
                  : [];
              return (
                <select
                  id={field.key}
                  value={values[field.key] || field.default || ""}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  className="h-10 w-full rounded-md border border-input bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Seçiniz...</option>
                  {opts.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              );
            })()}

            {field.help_text && <p className="text-xs text-gray-400">{field.help_text}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
