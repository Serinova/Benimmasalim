"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import type { OrderDetail } from "../../_lib/types";
import { useToast } from "@/hooks/use-toast";

interface NotesTabProps {
  detail: OrderDetail;
}

export function NotesTab({ detail }: NotesTabProps) {
  const { toast } = useToast();

  return (
    <div className="space-y-4">
      {/* Admin notes */}
      <div className="rounded-lg border bg-white p-3">
        <p className="mb-2 text-xs font-semibold text-slate-700">Admin Notları</p>
        {detail.admin_notes ? (
          <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap break-words rounded bg-slate-50 p-2 text-xs text-slate-700">
            {detail.admin_notes}
          </pre>
        ) : (
          <p className="text-xs text-slate-400">Not yok</p>
        )}
      </div>

      {/* Generation manifest */}
      {detail.generation_manifest_json && Object.keys(detail.generation_manifest_json).length > 0 && (
        <details className="overflow-hidden rounded-lg border bg-slate-50">
          <summary className="cursor-pointer select-none bg-slate-100 px-3 py-2 text-xs font-medium hover:bg-slate-200">
            Generation Manifest (debug)
          </summary>
          <div className="space-y-2 p-3">
            {Object.keys(detail.generation_manifest_json)
              .sort((a, b) => Number(a) - Number(b))
              .map((pageKey) => {
                const m = detail.generation_manifest_json![pageKey] as Record<string, unknown>;
                return (
                  <div key={pageKey} className="rounded border bg-white p-2 font-mono text-[10px]">
                    <div className="mb-1 font-semibold text-slate-700">
                      {m?.is_cover ? `Kapak (0)` : `Sayfa ${Number(pageKey)}`}
                    </div>
                    <dl className="grid grid-cols-2 gap-x-3 gap-y-0.5">
                      <dt className="text-slate-500">provider</dt><dd>{String(m?.provider ?? "-")}</dd>
                      <dt className="text-slate-500">model</dt><dd className="truncate">{String(m?.model ?? "-")}</dd>
                      <dt className="text-slate-500">steps</dt><dd>{String(m?.num_inference_steps ?? "-")}</dd>
                      <dt className="text-slate-500">guidance</dt><dd>{String(m?.guidance_scale ?? "-")}</dd>
                      <dt className="text-slate-500">size</dt><dd>{String(m?.width ?? "-")} × {String(m?.height ?? "-")}</dd>
                      <dt className="text-slate-500">ref_used</dt>
                      <dd className={m?.reference_image_used === false ? "font-medium text-amber-600" : ""}>
                        {String(m?.reference_image_used ?? "-")}
                      </dd>
                    </dl>
                  </div>
                );
              })}
          </div>
        </details>
      )}

      {/* Prompts */}
      {detail.prompts_by_page && Object.keys(detail.prompts_by_page).length > 0 && (
        <details className="overflow-hidden rounded-lg border border-emerald-200 bg-emerald-50">
          <summary className="flex cursor-pointer select-none items-center gap-2 bg-emerald-100 px-3 py-2 text-xs font-medium text-emerald-800 hover:bg-emerald-200 [&::-webkit-details-marker]:hidden">
            <span className="transition-transform group-open:rotate-90">▶</span>
            Prompts (final + negative)
            {detail.pipeline_version && (
              <span className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                detail.pipeline_version === "v3" ? "bg-emerald-200 text-emerald-800" : "bg-orange-200 text-orange-800"
              }`}>
                Pipeline {detail.pipeline_version}
              </span>
            )}
          </summary>
          <div className="space-y-3 p-3">
            {Object.keys(detail.prompts_by_page)
              .sort((a, b) => Number(a) - Number(b))
              .map((pageKey) => {
                const pb = detail.prompts_by_page![pageKey];
                const finalP = pb?.final_prompt ?? "";
                const negP = pb?.negative_prompt ?? "";
                const composerVer = pb?.composer_version ?? "";
                const pageType = pb?.page_type ?? "inner";
                const pageIdx = pb?.page_index ?? Number(pageKey);
                const storyNum = pb?.story_page_number;
                const pagePipeline = pb?.pipeline_version ?? "";

                const copyBoth = () => {
                  const text = `=== Pipeline: ${composerVer || pagePipeline || "unknown"} | Type: ${pageType} | Index: ${pageIdx} ===\n=== final_prompt ===\n${finalP}\n\n=== negative_prompt ===\n${negP}`;
                  void navigator.clipboard.writeText(text).then(() => {
                    toast({ title: "Kopyalandı", description: "Promptlar panoya kopyalandı" });
                  });
                };

                return (
                  <div key={pageKey} className="rounded border border-emerald-100 bg-white p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
                        {pageType === "cover" ? "Kapak" :
                         pageType === "front_matter" ? `İthaf (${storyNum ?? pageIdx})` :
                         `Sayfa ${storyNum ?? pageIdx}`}
                        {(composerVer || pagePipeline) && (
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                            (composerVer || pagePipeline) === "v3" ? "bg-emerald-100 text-emerald-700" : "bg-orange-100 text-orange-700"
                          }`}>{composerVer || pagePipeline}</span>
                        )}
                      </div>
                      <Button type="button" variant="outline" size="sm" className="h-6 text-[10px]" onClick={copyBoth}>
                        Kopyala
                      </Button>
                    </div>
                    {finalP && (
                      <div className="mb-2">
                        <p className="mb-1 text-[10px] font-medium text-slate-500">final_prompt</p>
                        <pre className="max-h-32 overflow-y-auto whitespace-pre-wrap break-words rounded border bg-slate-50 p-2 text-[10px]">{finalP}</pre>
                      </div>
                    )}
                    {negP && (
                      <div>
                        <p className="mb-1 text-[10px] font-medium text-slate-500">negative_prompt</p>
                        <pre className="max-h-24 overflow-y-auto whitespace-pre-wrap break-words rounded border bg-slate-50 p-2 text-[10px]">{negP}</pre>
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </details>
      )}
    </div>
  );
}
