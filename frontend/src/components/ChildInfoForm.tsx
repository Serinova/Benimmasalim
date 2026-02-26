"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

interface ChildInfo {
  name: string;
  age: string;
  gender: string;
  clothingDescription: string;
}

interface ChildInfoFormProps {
  childInfo: ChildInfo;
  onUpdate: (info: ChildInfo) => void;
  onContinue?: () => void;
  onBack?: () => void;
  hideNavButtons?: boolean;
  hideClothing?: boolean;
  scenarioName?: string; // backward compat with old create page
}

const AGES = ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12"];

export default function ChildInfoForm({
  childInfo,
  onUpdate,
  hideClothing = false,
}: ChildInfoFormProps) {
  const [nameFocused, setNameFocused] = useState(false);
  const [nameValid, setNameValid] = useState(false);

  useEffect(() => {
    setNameValid(childInfo.name.trim().length >= 2);
  }, [childInfo.name]);

  const update = (patch: Partial<ChildInfo>) =>
    onUpdate({ ...childInfo, ...patch });

  const avatarEmoji =
    childInfo.gender === "kız"
      ? ["👧", "👩‍🦰", "🧒‍♀️"][childInfo.name.length % 3]
      : ["👦", "🧒", "👨‍🦱"][childInfo.name.length % 3];

  return (
    <div className="space-y-6 px-1 pt-2 pb-4">

      {/* ── Avatar + intro ── */}
      <div className="flex items-center gap-4">
        <motion.div
          key={childInfo.gender + childInfo.name.slice(0, 1)}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="flex-shrink-0 w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center text-3xl shadow-sm"
        >
          {avatarEmoji}
        </motion.div>
        <div>
          <p className="text-xs font-semibold text-purple-500 uppercase tracking-wider mb-0.5">
            ⭐ Kahraman Profili
          </p>
          <h2 className="text-xl font-bold text-gray-800 leading-tight">
            {childInfo.name
              ? <><span className="text-purple-600">{childInfo.name}</span>&apos;\u0131 tan\u0131yal\u0131m</>
              : "Kahramanımızı Tanıyalım"}
          </h2>
        </div>
      </div>

      {/* ── Name ── */}
      <div>
        <label className="block text-sm font-semibold text-gray-600 mb-2">
          ✏️ Kahramanın Adı
        </label>
        <div className={`
          relative flex items-center rounded-2xl border-2 transition-all duration-200 bg-white
          ${nameFocused ? "border-purple-400 shadow-lg shadow-purple-100" : nameValid ? "border-green-300" : "border-gray-200"}
        `}>
          <input
            type="text"
            value={childInfo.name}
            onChange={(e) => update({ name: e.target.value })}
            onFocus={() => setNameFocused(true)}
            onBlur={() => setNameFocused(false)}
            placeholder="Çocuğun adını yaz..."
            maxLength={30}
            className="flex-1 bg-transparent px-4 py-4 text-lg font-medium text-gray-800 placeholder:text-gray-300 outline-none"
          />
          <AnimatePresence>
            {nameValid && (
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                className="pr-4"
              >
                <CheckCircle2 className="h-6 w-6 text-green-500" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ── Gender ── */}
      <div>
        <label className="block text-sm font-semibold text-gray-600 mb-2">
          👤 Cinsiyet
        </label>
        <div className="grid grid-cols-2 gap-3">
          {[
            { value: "erkek", emoji: "👦", label: "Erkek", color: "from-blue-50 to-indigo-50", border: "border-blue-400", text: "text-blue-700" },
            { value: "kız", emoji: "👧", label: "Kız", color: "from-pink-50 to-rose-50", border: "border-pink-400", text: "text-pink-700" },
          ].map(({ value, emoji, label, color, border, text }) => (
            <motion.button
              key={value}
              type="button"
              whileTap={{ scale: 0.97 }}
              onClick={() => update({ gender: value })}
              className={`
                relative flex items-center justify-center gap-2.5 rounded-2xl border-2 p-4 transition-all duration-200 font-semibold
                ${childInfo.gender === value
                  ? `bg-gradient-to-br ${color} ${border} ${text} shadow-md`
                  : "bg-white border-gray-200 text-gray-500"
                }
              `}
            >
              <span className="text-2xl">{emoji}</span>
              <span className="text-base">{label}</span>
              {childInfo.gender === value && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute top-2 right-2 w-5 h-5 rounded-full bg-current/20 flex items-center justify-center"
                >
                  <span className="text-xs">✓</span>
                </motion.div>
              )}
            </motion.button>
          ))}
        </div>
      </div>

      {/* ── Age ── */}
      <div>
        <label className="block text-sm font-semibold text-gray-600 mb-2">
          🎂 Yaş
        </label>
        <div className="grid grid-cols-5 gap-2">
          {AGES.map((age) => (
            <motion.button
              key={age}
              type="button"
              whileTap={{ scale: 0.93 }}
              onClick={() => update({ age })}
              className={`
                h-12 rounded-xl border-2 text-base font-bold transition-all duration-150
                ${childInfo.age === age
                  ? "bg-gradient-to-br from-purple-500 to-pink-500 border-transparent text-white shadow-lg shadow-purple-200"
                  : "bg-white border-gray-200 text-gray-600 hover:border-purple-300 hover:text-purple-600"
                }
              `}
            >
              {age}
            </motion.button>
          ))}
        </div>
        {childInfo.age && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-center text-sm text-purple-600 font-medium"
          >
            {childInfo.age} yaşında — Harika bir seçim! ✨
          </motion.p>
        )}
      </div>

      {/* ── Clothing (optional) ── */}
      {!hideClothing && (
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-2">
            👕 Kıyafet Tarifi <span className="font-normal text-gray-400">(isteğe bağlı)</span>
          </label>
          <textarea
            value={childInfo.clothingDescription}
            onChange={(e) => update({ clothingDescription: e.target.value })}
            placeholder="Örn: Mavi kapüşonlu, sarı ayakkabılı..."
            maxLength={200}
            rows={3}
            className="w-full rounded-2xl border-2 border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 placeholder:text-gray-300 outline-none focus:border-purple-400 resize-none transition-colors"
          />
        </div>
      )}
    </div>
  );
}
