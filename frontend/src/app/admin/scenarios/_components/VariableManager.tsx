"use client";

import { useState } from "react";
import {
  Plus,
  Trash2,
  Pencil,
  GripVertical,
  CheckCircle2,
  Variable,
  HelpCircle,
  Type,
  Hash,
  List,
  AlignLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import type { CustomInputField } from "../_lib/types";

interface VariableManagerProps {
  variables: CustomInputField[];
  onVariablesChange: (variables: CustomInputField[]) => void;
}

export function VariableManager({ variables, onVariablesChange }: VariableManagerProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [newField, setNewField] = useState<Partial<CustomInputField>>({
    key: "",
    label: "",
    type: "text",
    required: true,
  });
  const [showAddForm, setShowAddForm] = useState(false);

  const inputTypeOptions = [
    { value: "text", label: "Metin", icon: Type },
    { value: "number", label: "Sayı", icon: Hash },
    { value: "select", label: "Seçenek", icon: List },
    { value: "textarea", label: "Uzun Metin", icon: AlignLeft },
  ];

  const addVariable = () => {
    if (!newField.key || !newField.label) return;

    // Sanitize key (remove spaces, special chars)
    const sanitizedKey = newField.key
      .toLowerCase()
      .replace(/\s+/g, "_")
      .replace(/[^a-z0-9_]/g, "");

    const field: CustomInputField = {
      key: sanitizedKey,
      label: newField.label,
      type: (newField.type as CustomInputField["type"]) || "text",
      default: newField.default || undefined,
      options: newField.type === "select" ? newField.options || [] : undefined,
      required: newField.required ?? true,
      placeholder: newField.placeholder || undefined,
      help_text: newField.help_text || undefined,
    };

    onVariablesChange([...variables, field]);
    setNewField({ key: "", label: "", type: "text", required: true });
    setShowAddForm(false);
  };

  const updateVariable = (index: number, updates: Partial<CustomInputField>) => {
    const updated = [...variables];
    updated[index] = { ...updated[index], ...updates };
    onVariablesChange(updated);
  };

  const removeVariable = (index: number) => {
    onVariablesChange(variables.filter((_, i) => i !== index));
  };

  const moveVariable = (index: number, direction: "up" | "down") => {
    const newIndex = direction === "up" ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= variables.length) return;

    const updated = [...variables];
    [updated[index], updated[newIndex]] = [updated[newIndex], updated[index]];
    onVariablesChange(updated);
  };

  return (
    <div className="space-y-4">
      {/* Existing Variables */}
      {variables.length > 0 && (
        <div className="space-y-2">
          {variables.map((variable, index) => (
            <div
              key={variable.key}
              className="rounded-lg border bg-white p-3 transition-colors hover:border-purple-300"
            >
              {editingIndex === index ? (
                // Edit Mode
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs">Değişken Anahtarı</Label>
                      <Input
                        value={variable.key}
                        onChange={(e) =>
                          updateVariable(index, {
                            key: e.target.value
                              .toLowerCase()
                              .replace(/\s+/g, "_")
                              .replace(/[^a-z0-9_]/g, ""),
                          })
                        }
                        className="mt-1 font-mono text-sm"
                        placeholder="favorite_toy"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Kullanıcı Etiketi</Label>
                      <Input
                        value={variable.label}
                        onChange={(e) => updateVariable(index, { label: e.target.value })}
                        className="mt-1"
                        placeholder="En Sevdiği Oyuncak"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs">Tür</Label>
                      <select
                        value={variable.type}
                        onChange={(e) =>
                          updateVariable(index, {
                            type: e.target.value as CustomInputField["type"],
                          })
                        }
                        className="mt-1 h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                      >
                        {inputTypeOptions.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-xs">Varsayılan</Label>
                      <Input
                        value={variable.default || ""}
                        onChange={(e) => updateVariable(index, { default: e.target.value })}
                        className="mt-1"
                        placeholder="Varsayılan değer"
                      />
                    </div>
                  </div>

                  {variable.type === "select" && (
                    <div>
                      <Label className="text-xs">Seçenekler (virgülle ayırın)</Label>
                      <Input
                        value={(variable.options || []).join(", ")}
                        onChange={(e) =>
                          updateVariable(index, {
                            options: e.target.value
                              .split(",")
                              .map((s) => s.trim())
                              .filter(Boolean),
                          })
                        }
                        className="mt-1"
                        placeholder="Seçenek 1, Seçenek 2, Seçenek 3"
                      />
                    </div>
                  )}

                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={variable.required ?? true}
                        onChange={(e) => updateVariable(index, { required: e.target.checked })}
                        className="rounded"
                      />
                      Zorunlu
                    </label>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => setEditingIndex(null)}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Tamam
                    </Button>
                  </div>
                </div>
              ) : (
                // Display Mode
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex flex-col gap-1">
                      <button
                        type="button"
                        onClick={() => moveVariable(index, "up")}
                        disabled={index === 0}
                        className="text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <GripVertical className="h-3 w-3" />
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      {inputTypeOptions.find((t) => t.value === variable.type)?.icon && (
                        <div className="flex h-8 w-8 items-center justify-center rounded bg-purple-100">
                          {(() => {
                            const IconComp =
                              inputTypeOptions.find((t) => t.value === variable.type)?.icon || Type;
                            return <IconComp className="h-4 w-4 text-purple-600" />;
                          })()}
                        </div>
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <code className="rounded bg-purple-50 px-1.5 py-0.5 font-mono text-sm text-purple-600">
                            {`{${variable.key}}`}
                          </code>
                          {!variable.required && (
                            <Badge variant="outline" className="text-[10px]">
                              Opsiyonel
                            </Badge>
                          )}
                        </div>
                        <p className="mt-0.5 text-xs text-gray-500">{variable.label}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => setEditingIndex(index)}
                      className="h-7 w-7 p-0"
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => removeVariable(index)}
                      className="h-7 w-7 p-0 text-red-500 hover:bg-red-50 hover:text-red-700"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add New Variable Form */}
      {showAddForm ? (
        <div className="space-y-3 rounded-lg border-2 border-dashed border-purple-300 bg-purple-50/50 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-purple-700">
            <Variable className="h-4 w-4" />
            Yeni Değişken Ekle
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs">Değişken Anahtarı *</Label>
              <Input
                value={newField.key || ""}
                onChange={(e) =>
                  setNewField({
                    ...newField,
                    key: e.target.value
                      .toLowerCase()
                      .replace(/\s+/g, "_")
                      .replace(/[^a-z0-9_]/g, ""),
                  })
                }
                className="mt-1 font-mono text-sm"
                placeholder="favorite_toy"
              />
              <p className="mt-0.5 text-[10px] text-gray-400">
                Promptta {`{${newField.key || "key"}}`} olarak kullanılır
              </p>
            </div>
            <div>
              <Label className="text-xs">Kullanıcı Etiketi *</Label>
              <Input
                value={newField.label || ""}
                onChange={(e) => setNewField({ ...newField, label: e.target.value })}
                className="mt-1"
                placeholder="En Sevdiği Oyuncak"
              />
              <p className="mt-0.5 text-[10px] text-gray-400">Kullanıcının göreceği etiket</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div>
              <Label className="text-xs">Tür</Label>
              <select
                value={newField.type || "text"}
                onChange={(e) =>
                  setNewField({ ...newField, type: e.target.value as CustomInputField["type"] })
                }
                className="mt-1 h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
              >
                {inputTypeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs">Varsayılan</Label>
              <Input
                value={newField.default || ""}
                onChange={(e) => setNewField({ ...newField, default: e.target.value })}
                className="mt-1"
                placeholder="Opsiyonel"
              />
            </div>
            <div>
              <Label className="text-xs">Placeholder</Label>
              <Input
                value={newField.placeholder || ""}
                onChange={(e) => setNewField({ ...newField, placeholder: e.target.value })}
                className="mt-1"
                placeholder="İpucu metni"
              />
            </div>
          </div>

          {newField.type === "select" && (
            <div>
              <Label className="text-xs">Seçenekler (virgülle ayırın)</Label>
              <Input
                value={(newField.options || []).join(", ")}
                onChange={(e) =>
                  setNewField({
                    ...newField,
                    options: e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                className="mt-1"
                placeholder="Kedi, Köpek, Kuş"
              />
            </div>
          )}

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={newField.required ?? true}
                onChange={(e) => setNewField({ ...newField, required: e.target.checked })}
                className="rounded"
              />
              Zorunlu Alan
            </label>
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                setShowAddForm(false);
                setNewField({ key: "", label: "", type: "text", required: true });
              }}
            >
              İptal
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={addVariable}
              disabled={!newField.key || !newField.label}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Plus className="mr-1 h-3 w-3" />
              Ekle
            </Button>
          </div>
        </div>
      ) : (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setShowAddForm(true)}
          className="w-full border-dashed hover:border-purple-400 hover:bg-purple-50"
        >
          <Plus className="mr-2 h-4 w-4" />
          Yeni Değişken Ekle
        </Button>
      )}

      {/* Usage hint */}
      {variables.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          <div className="flex items-start gap-2">
            <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
            <div className="text-xs text-amber-800">
              <p className="font-medium">Kullanım:</p>
              <p className="mt-1">
                Bu değişkenleri prompt şablonlarında{" "}
                <code className="rounded bg-amber-100 px-1">{`{değişken_adı}`}</code> formatında
                kullanabilirsiniz.
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {variables.map((v) => (
                  <Badge key={v.key} variant="outline" className="bg-white font-mono text-[10px]">
                    {`{${v.key}}`}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
