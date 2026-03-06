"use client";

import { useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Search, X, Info } from "lucide-react";
import ScenarioDetailModal from "@/components/ScenarioDetailModal";
import CustomInputsForm from "@/components/CustomInputsForm";
import type { Scenario } from "@/lib/api";
import { AGES } from "../../_lib/constants";
import {
  validateChildName,
  validateAge,
  validateScenario,
} from "../../_lib/validations";
import StickyCTA from "../StickyCTA";

interface HeroAndAdventureStepProps {
  childName: string;
  childAge: string;
  childGender: string;
  scenarioId: string;
  customVariables: Record<string, string>;
  scenarios: Scenario[];
  onChildNameChange: (name: string) => void;
  onChildAgeChange: (age: string) => void;
  onChildGenderChange: (gender: string) => void;
  onScenarioSelect: (id: string) => void;
  onCustomVariablesChange: (vars: Record<string, string>) => void;
  onContinue: () => void;
  onBack: () => void;
  preselectedScenarioId?: string;
}

function getTheme(s: Scenario): string {
  const name = (s.name || "").toLowerCase().trim();
  if (name.includes("uzay") || name.includes("gezegen") || name.includes("güneş")) return "Uzay";
  if (name.includes("orman") || name.includes("doğa") || name.includes("amazon")) return "Doğa";
  if (name.includes("tarih") || name.includes("kapadok") || name.includes("yerebatan") || name.includes("sarnıç")) return "Tarih";
  if (name.includes("deniz") || name.includes("okyanus") || name.includes("su")) return "Deniz";
  if (name.includes("spor") || name.includes("futbol") || name.includes("koş")) return "Spor";
  if (name.includes("bilim") || name.includes("robot") || name.includes("teknoloj")) return "Bilim";
  return "Macera";
}

export default function HeroAndAdventureStep({
  childName,
  childAge,
  childGender,
  scenarioId,
  customVariables,
  scenarios,
  onChildNameChange,
  onChildAgeChange,
  onChildGenderChange,
  onScenarioSelect,
  onCustomVariablesChange,
  onContinue,
  onBack: _onBack,
  preselectedScenarioId,
}: HeroAndAdventureStepProps) {
  const router = useRouter();
  const [nameTouched, setNameTouched] = useState(false);
  const [nameFocused, setNameFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTheme, setActiveTheme] = useState<string | null>(null);
  const [detailScenario, setDetailScenario] = useState<Scenario | null>(null);

  const nameValidation = validateChildName(childName);
  const ageValidation = validateAge(childAge);
  const scenarioValidation = validateScenario(scenarioId);

  const canContinue =
    nameValidation.valid && ageValidation.valid && scenarioValidation.valid;

  const themes = useMemo(
    () => Array.from(new Set(scenarios.map(getTheme))),
    [scenarios],
  );

  const filtered = useMemo(
    () =>
      scenarios.filter((s) => {
        const matchesSearch =
          !searchQuery || s.name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesTheme = !activeTheme || getTheme(s) === activeTheme;
        return matchesSearch && matchesTheme;
      }),
    [scenarios, searchQuery, activeTheme],
  );

  const selectedScenarioObj = scenarios.find((s) => s.id === scenarioId);

  const avatarEmoji =
    childGender === "kız"
      ? ["👧", "👩‍🦰", "🧒‍♀️"][childName.length % 3]
      : ["👦", "🧒", "👨‍🦱"][childName.length % 3];

  const handleNameBlur = useCallback(() => {
    setNameTouched(true);
    setNameFocused(false);
  }, []);

  // Ana sayfadan seçili macera ile gelinmişse grid'i başta gizle
  // Kullanıcı "Değiştir" butonuna basarsa açılır
  const [showScenarioPicker, setShowScenarioPicker] = useState(!preselectedScenarioId);


  return (
    <div className="pb-24 space-y-6">
      {/* ── Section 1: Child Info ── */}
      <section aria-label="Kahraman bilgileri">
        {/* Avatar + Title */}
        <div className="flex items-center gap-3 mb-5">
          <motion.div
            key={childGender + childName.slice(0, 1)}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex-shrink-0 w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center text-2xl sm:text-3xl shadow-sm"
          >
            {avatarEmoji}
          </motion.div>
          <div className="min-w-0">
            <p className="text-[10px] sm:text-xs font-semibold text-purple-500 uppercase tracking-wider mb-0.5">
              Adım 1
            </p>
            <h2 className="text-lg sm:text-xl font-bold text-gray-800 leading-tight">
              Kahramanını Tanı, Konusunu Seç
            </h2>
          </div>
        </div>

        {/* Name */}
        <div className="space-y-4">
          <div>
            <label htmlFor="child-name" className="block text-[13px] font-semibold text-gray-600 mb-1.5">
              Kahramanın Adı
            </label>
            <div
              className={`
                relative flex items-center rounded-xl border-2 transition-all bg-white
                ${nameFocused ? "border-purple-400 ring-4 ring-purple-100" : nameValidation.valid && nameTouched ? "border-green-300" : nameTouched && !nameValidation.valid ? "border-red-400 ring-4 ring-red-100" : "border-gray-200"}
              `}
            >
              <input
                id="child-name"
                type="text"
                value={childName}
                onChange={(e) => onChildNameChange(e.target.value)}
                onFocus={() => setNameFocused(true)}
                onBlur={handleNameBlur}
                placeholder="Çocuğunuzun adı"
                maxLength={30}
                autoComplete="given-name"
                enterKeyHint="next"
                aria-invalid={nameTouched && !nameValidation.valid ? "true" : undefined}
                className="flex-1 bg-transparent px-4 py-3 text-base font-medium text-gray-800 placeholder:text-gray-300 outline-none"
              />
              <AnimatePresence>
                {nameValidation.valid && nameTouched && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                    className="pr-3"
                  >
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            {nameTouched && !nameValidation.valid && (
              <p className="mt-1 text-xs text-red-500 font-medium" role="alert">
                {nameValidation.message}
              </p>
            )}
          </div>

          {/* Gender */}
          <div>
            <label className="block text-[13px] font-semibold text-gray-600 mb-1.5">
              Cinsiyet
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              {[
                { value: "erkek", emoji: "👦", label: "Erkek", activeClasses: "bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-400 text-blue-700" },
                { value: "kız", emoji: "👧", label: "Kız", activeClasses: "bg-gradient-to-br from-pink-50 to-rose-50 border-pink-400 text-pink-700" },
              ].map(({ value, emoji, label, activeClasses }) => (
                <motion.button
                  key={value}
                  type="button"
                  whileTap={{ scale: 0.97 }}
                  onClick={() => onChildGenderChange(value)}
                  className={`
                    relative flex items-center justify-center gap-2 rounded-xl border-2 p-3 font-semibold transition-all text-sm
                    ${childGender === value ? `${activeClasses} shadow-md` : "bg-white border-gray-200 text-gray-500 active:bg-gray-50"}
                  `}
                >
                  <span className="text-xl">{emoji}</span>
                  <span>{label}</span>
                  {childGender === value && (
                    <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute top-1.5 right-1.5 text-xs">✓</motion.span>
                  )}
                </motion.button>
              ))}
            </div>
          </div>

          {/* Age */}
          <div>
            <label className="block text-[13px] font-semibold text-gray-600 mb-1.5">
              Yaş
            </label>
            <div className="grid grid-cols-5 gap-1.5">
              {AGES.map((age) => (
                <motion.button
                  key={age}
                  type="button"
                  whileTap={{ scale: 0.93 }}
                  onClick={() => onChildAgeChange(age)}
                  className={`
                    h-11 rounded-xl border-2 text-sm font-bold transition-all
                    ${childAge === age
                      ? "bg-gradient-to-br from-purple-500 to-pink-500 border-transparent text-white shadow-lg shadow-purple-200"
                      : "bg-white border-gray-200 text-gray-600 hover:border-purple-300 active:bg-purple-50"}
                  `}
                >
                  {age}
                </motion.button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 2: Scenario Selection ── */}
      <section aria-label="Macera seçimi" className="pt-2">
        <div className="flex items-center gap-2 mb-4">
          <div className="h-px flex-1 bg-gray-200" />
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Hikaye Konusu
          </span>
          <div className="h-px flex-1 bg-gray-200" />
        </div>

        {/* Eğer ana sayfadan seçili macera ile gelindiyse ve picker kapalıysa → Banner göster */}
        {!showScenarioPicker && selectedScenarioObj ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 rounded-2xl border-2 border-purple-400 bg-gradient-to-r from-purple-50 to-pink-50 p-3 shadow-sm"
          >
            {selectedScenarioObj.thumbnail_url && (
              <div className="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-xl shadow-sm">
                <Image
                  src={selectedScenarioObj.thumbnail_url}
                  alt={selectedScenarioObj.name}
                  fill
                  className="object-cover"
                  sizes="64px"
                />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-[10px] font-bold uppercase tracking-wider text-purple-400 mb-0.5">
                Seçilen Macera ✓
              </p>
              <p className="text-sm font-bold text-gray-800 line-clamp-1">
                {selectedScenarioObj.name}
              </p>
              {selectedScenarioObj.tagline && (
                <p className="text-xs text-gray-500 line-clamp-1 mt-0.5">
                  {selectedScenarioObj.tagline}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => setShowScenarioPicker(true)}
              className="flex-shrink-0 rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-500 hover:border-purple-300 hover:text-purple-600 transition-all"
            >
              Değiştir
            </button>
          </motion.div>
        ) : (
          <>
            {/* Eğer preselected ile picker açıldıysa geri dön butonu */}
            {preselectedScenarioId && selectedScenarioObj && (
              <div className="flex items-center gap-2 mb-3">
                <button
                  type="button"
                  onClick={() => setShowScenarioPicker(false)}
                  className="text-xs text-purple-500 font-semibold hover:underline"
                >
                  ← Seçili maceraya dön
                </button>
              </div>
            )}

            {/* Search + Theme filter */}
            <div className="space-y-3 mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Konu ara..."
                  className="w-full rounded-xl border-2 border-gray-200 bg-white pl-9 pr-9 py-2.5 text-sm placeholder:text-gray-300 outline-none focus:border-purple-400 transition-colors"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => setSearchQuery("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              {themes.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
                  <button
                    type="button"
                    onClick={() => setActiveTheme(null)}
                    className={`flex-shrink-0 rounded-full px-3 py-1 text-xs font-semibold transition-all ${!activeTheme ? "bg-purple-600 text-white" : "bg-gray-100 text-gray-600"
                      }`}
                  >
                    Tümü
                  </button>
                  {themes.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setActiveTheme(activeTheme === t ? null : t)}
                      className={`flex-shrink-0 rounded-full px-3 py-1 text-xs font-semibold transition-all ${activeTheme === t ? "bg-purple-600 text-white" : "bg-gray-100 text-gray-600"
                        }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Scenario Grid */}
            {filtered.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-gray-400">Aramanızla eşleşen konu bulunamadı</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2.5 sm:gap-3">
                {filtered.map((s) => {
                  const isSelected = scenarioId === s.id;
                  return (
                    <motion.button
                      key={s.id}
                      type="button"
                      whileTap={{ scale: 0.97 }}
                      onClick={() => {
                        onScenarioSelect(s.id);
                        // Picker'dan seçim yapıldıysa kapat
                        if (preselectedScenarioId) setShowScenarioPicker(false);
                      }}
                      className={`
                        relative rounded-2xl overflow-hidden border-2 transition-all text-left
                        ${isSelected ? "border-purple-500 ring-4 ring-purple-100 shadow-lg" : "border-gray-100 hover:border-gray-200 shadow-sm"}
                      `}
                    >
                      {s.thumbnail_url && (
                        <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
                          <Image
                            src={s.thumbnail_url}
                            alt={s.name}
                            fill
                            loading="lazy"
                            className="object-cover"
                            sizes="(max-width: 640px) 50vw, 33vw"
                            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
                          />
                        </div>
                      )}
                      <div className="p-2.5 sm:p-3">
                        <p className="text-xs sm:text-sm font-bold text-gray-800 line-clamp-1">{s.name}</p>
                        {s.tagline && (
                          <p className="text-[10px] sm:text-xs text-gray-500 line-clamp-1 mt-0.5">{s.tagline}</p>
                        )}
                      </div>

                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute top-2 right-2 h-6 w-6 rounded-full bg-purple-600 text-white flex items-center justify-center"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                        </motion.div>
                      )}

                      {/* Info button */}
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); setDetailScenario(s); }}
                        className="absolute bottom-2 right-2 p-1 rounded-full bg-white/80 text-gray-500 hover:bg-white"
                      >
                        <Info className="h-3.5 w-3.5" />
                      </button>
                    </motion.button>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* Custom inputs for selected scenario */}
        {selectedScenarioObj?.custom_inputs_schema?.length ? (
          <div className="mt-4 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <CustomInputsForm
              fields={selectedScenarioObj.custom_inputs_schema as unknown as Array<{
                key: string;
                label: string;
                type: "text" | "number" | "select" | "textarea";
                required?: boolean;
                options?: string[];
              }>}
              values={customVariables}
              onChange={onCustomVariablesChange}
            />
          </div>
        ) : null}
      </section>


      {/* Scenario detail modal */}
      <ScenarioDetailModal
        scenario={detailScenario}
        isOpen={!!detailScenario}
        onClose={() => setDetailScenario(null)}
        onSelect={() => {
          if (detailScenario) onScenarioSelect(detailScenario.id);
          setDetailScenario(null);
        }}
      />

      {/* Sticky CTA */}
      <StickyCTA
        primaryLabel={canContinue ? "Fotoğraf & Stil Adımına Geç" : "Bilgileri Tamamlayın"}
        onPrimary={onContinue}
        primaryDisabled={!canContinue}
        secondaryLabel="← Geri"
        onSecondary={() => router.push("/")}
      />
    </div>
  );
}
