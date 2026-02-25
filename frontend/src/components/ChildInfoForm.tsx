"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Star,
  Crown,
  Heart,
  ChevronRight,
  User,
  Check,
  Wand2,
  BookOpen,
  Shirt,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChildInfoFormProps {
  childInfo: {
    name: string;
    age: string;
    gender: string;
    clothingDescription: string;
  };
  onUpdate: (info: {
    name: string;
    age: string;
    gender: string;
    clothingDescription: string;
  }) => void;
  onContinue: () => void;
  onBack: () => void;
  scenarioName?: string;
  /** If true, clothing selector is rendered externally (not inside this form). */
  hideClothing?: boolean;
}

// Age range
const ages = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

// Gender options with illustrations
const genderOptions = [
  {
    id: "erkek",
    label: "Erkek",
    emoji: "👦",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-400",
    textColor: "text-blue-600",
    activeBg: "bg-blue-100",
    ringColor: "ring-blue-400",
  },
  {
    id: "kiz",
    label: "Kız",
    emoji: "👧",
    bgColor: "bg-pink-50",
    borderColor: "border-pink-400",
    textColor: "text-pink-600",
    activeBg: "bg-pink-100",
    ringColor: "ring-pink-400",
  },
];

// Floating particles component
function FloatingParticles() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {[...Array(6)].map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 100 }}
          animate={{
            opacity: [0, 1, 0],
            y: [-20, -100],
            x: [0, (i % 2 === 0 ? 1 : -1) * 20],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            delay: i * 0.5,
            ease: "easeOut",
          }}
          className="absolute"
          style={{
            left: `${15 + i * 15}%`,
            bottom: "20%",
          }}
        >
          <Sparkles className="h-4 w-4 text-purple-300" />
        </motion.div>
      ))}
    </div>
  );
}

// Hero Avatar Component
function HeroAvatar({ name, gender, age }: { name: string; gender: string; age: string }) {
  const genderOption = genderOptions.find((g) => g.id === gender);

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="relative"
    >
      {/* Glow Effect */}
      <div
        className={`absolute inset-0 rounded-full blur-xl ${
          gender === "kiz" ? "bg-pink-200" : gender === "erkek" ? "bg-blue-200" : "bg-purple-200"
        } opacity-50`}
      />

      {/* Avatar Circle */}
      <motion.div
        animate={{
          scale: name ? [1, 1.05, 1] : 1,
        }}
        transition={{ duration: 0.3 }}
        className={`relative flex h-32 w-32 items-center justify-center rounded-full md:h-40 md:w-40 ${
          gender === "kiz"
            ? "bg-gradient-to-br from-pink-100 to-pink-200"
            : gender === "erkek"
              ? "bg-gradient-to-br from-blue-100 to-blue-200"
              : "bg-gradient-to-br from-purple-100 to-purple-200"
        } border-4 border-white shadow-xl`}
      >
        {/* Avatar Content */}
        {gender ? (
          <span className="text-6xl md:text-7xl">{genderOption?.emoji}</span>
        ) : (
          <User className="h-16 w-16 text-gray-300" />
        )}

        {/* Crown for named hero */}
        {name && (
          <motion.div
            initial={{ scale: 0, y: 10 }}
            animate={{ scale: 1, y: 0 }}
            className="absolute -top-4 left-1/2 -translate-x-1/2"
          >
            <Crown className="h-10 w-10 fill-yellow-400 text-yellow-500" />
          </motion.div>
        )}

        {/* Age Badge */}
        {age && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -bottom-2 -right-2 flex h-12 w-12 items-center justify-center rounded-full border-4 border-white bg-gradient-to-r from-purple-500 to-pink-500 text-lg font-bold text-white shadow-lg"
          >
            {age}
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
}

export default function ChildInfoForm({
  childInfo,
  onUpdate,
  onContinue,
  onBack,
  scenarioName,
  hideClothing = false,
}: ChildInfoFormProps) {
  const [isFocused, setIsFocused] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const ageScrollRef = useRef<HTMLDivElement>(null);

  // V2: clothing is now optional (handled by external ClothingSelector or skipped)
  const clothingTrimmed = (childInfo.clothingDescription || "").trim();
  const isClothingValid =
    hideClothing || clothingTrimmed.length === 0 || clothingTrimmed.length >= 8;

  // Check if form is valid (clothing is optional)
  const isValid =
    childInfo.name.trim() !== "" &&
    childInfo.age !== "" &&
    childInfo.gender !== "" &&
    isClothingValid;

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && childInfo.name.trim()) {
      // Focus age selection area
      ageScrollRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  // Scroll selected age into view
  useEffect(() => {
    if (childInfo.age && ageScrollRef.current) {
      const selectedButton = ageScrollRef.current.querySelector(`[data-age="${childInfo.age}"]`);
      selectedButton?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    }
  }, [childInfo.age]);

  // Dynamic title based on name
  const getTitle = () => {
    if (childInfo.name.trim()) {
      return (
        <span>
          <span className="text-purple-600">{childInfo.name}</span> Bizim Kahramanımız!
        </span>
      );
    }
    return "Kahramanımızı Tanıyalım";
  };

  return (
    <div className="relative space-y-4">
      {/* Floating Particles */}
      <FloatingParticles />

      {/* Header */}
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-purple-100 via-pink-100 to-orange-100 px-4 py-2"
        >
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-500" />
          <span className="text-sm font-medium text-purple-700">Kahraman Profili</span>
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-500" />
        </motion.div>

        <motion.h1
          key={childInfo.name}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-xl font-bold text-gray-800 md:text-2xl"
        >
          {getTitle()}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="mt-3 text-gray-600"
        >
          Bu hikaye tamamen onun hakkında olacak ✨
        </motion.p>
      </div>

      {/* Hero Avatar */}
      <div className="flex justify-center py-4">
        <HeroAvatar name={childInfo.name} gender={childInfo.gender} age={childInfo.age} />
      </div>

      {/* Main Form Card - mobil: taşma yok, tam sayfa sığar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="min-w-0 max-w-full space-y-4 rounded-xl border border-gray-200 bg-white p-3 shadow-lg md:p-4 touch-manipulation"
      >
        {/* Name Input - The Centerpiece */}
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Wand2 className="h-4 w-4 text-purple-500" />
            Kahramanın Adı
          </label>

          <div className="relative min-w-0">
            <motion.div
              animate={{
                boxShadow: isFocused
                  ? "0 0 0 4px rgba(168, 85, 247, 0.2), 0 0 30px rgba(168, 85, 247, 0.1)"
                  : "0 0 0 0px rgba(168, 85, 247, 0)",
              }}
              className="min-w-0 rounded-2xl"
            >
              <input
                ref={nameInputRef}
                type="text"
                inputMode="text"
                autoComplete="off"
                value={childInfo.name}
                onChange={(e) => onUpdate({ ...childInfo, name: e.target.value })}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onKeyDown={handleKeyDown}
                placeholder="Çocuğun Adı"
                className="w-full rounded-xl border-2 border-gray-200 bg-gradient-to-r from-purple-50/50 via-pink-50/50 to-orange-50/50 px-3 py-3 text-center font-bold text-gray-800 transition-all placeholder:text-gray-300 focus:border-purple-400 focus:outline-none md:text-xl lg:text-2xl"
                style={{ fontSize: "max(16px, 1rem)" }}
              />
            </motion.div>

            {/* Sparkle decorations when name entered */}
            <AnimatePresence>
              {childInfo.name && (
                <>
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    className="absolute -left-2 -top-2"
                  >
                    <Sparkles className="h-6 w-6 text-yellow-400" />
                  </motion.div>
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    transition={{ delay: 0.1 }}
                    className="absolute -right-2 -top-2"
                  >
                    <Sparkles className="h-6 w-6 text-pink-400" />
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Gender Selection */}
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Heart className="h-4 w-4 text-pink-500" />
            Cinsiyet
          </label>

          <div className="grid min-w-0 grid-cols-2 gap-3 sm:gap-4">
            {genderOptions.map((option) => {
              const isSelected = childInfo.gender === option.id;

              return (
                <motion.button
                  key={option.id}
                  onClick={() => onUpdate({ ...childInfo, gender: option.id })}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  animate={isSelected ? { scale: [1, 1.05, 1] } : {}}
                  className={`relative min-w-0 rounded-lg border-2 p-2.5 transition-all sm:p-3 ${
                    isSelected
                      ? `${option.activeBg} ${option.borderColor} border-4 shadow-lg`
                      : `${option.bgColor} border-2 border-transparent hover:border-gray-200`
                  }`}
                >
                  {/* Selected Checkmark */}
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className={`absolute -right-2 -top-2 h-7 w-7 ${
                          option.id === "erkek" ? "bg-blue-500" : "bg-pink-500"
                        } flex items-center justify-center rounded-full shadow-lg`}
                      >
                        <Check className="h-4 w-4 text-white" strokeWidth={3} />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Avatar */}
                  <div className="mb-3 text-5xl md:text-6xl">{option.emoji}</div>

                  {/* Label */}
                  <p
                    className={`text-base font-bold ${isSelected ? option.textColor : "text-gray-700"}`}
                  >
                    {option.label}
                  </p>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Age Selection */}
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Star className="h-4 w-4 text-yellow-500" />
            Yaş
          </label>

          <div
            ref={ageScrollRef}
            className="scrollbar-hide -mx-2 flex gap-3 overflow-x-auto px-2 pb-2"
            style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
          >
            {ages.map((age) => {
              const isSelected = childInfo.age === age.toString();

              return (
                <motion.button
                  key={age}
                  data-age={age}
                  onClick={() => onUpdate({ ...childInfo, age: age.toString() })}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  animate={
                    isSelected
                      ? {
                          scale: 1.15,
                          y: -4,
                        }
                      : {
                          scale: 1,
                          y: 0,
                        }
                  }
                  className={`relative h-12 w-12 flex-shrink-0 rounded-full text-base font-bold transition-all md:h-14 md:w-14 md:text-lg ${
                    isSelected
                      ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-300"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {age}

                  {/* Selection Ring */}
                  {isSelected && (
                    <motion.div
                      layoutId="age-ring"
                      className="absolute inset-0 rounded-full border-4 border-purple-300"
                      initial={false}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                </motion.button>
              );
            })}
          </div>
        </div>
      </motion.div>

      {/* V2: Clothing Description — only shown if NOT handled by external ClothingSelector */}
      {!hideClothing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="space-y-3 rounded-xl border border-gray-200 bg-white p-3 shadow-lg md:p-4"
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Shirt className="h-4 w-4 text-indigo-500" />
            Çocuğun Kıyafeti
            <span className="ml-1 text-xs text-gray-400">(tüm sayfalarda aynı olacak)</span>
          </label>

          <input
            type="text"
            inputMode="text"
            value={childInfo.clothingDescription}
            onChange={(e) => onUpdate({ ...childInfo, clothingDescription: e.target.value })}
            placeholder="Örn: kırmızı mont, mavi pantolon, beyaz spor ayakkabı"
            className="w-full rounded-xl border-2 border-gray-200 bg-gradient-to-r from-indigo-50/30 via-purple-50/30 to-pink-50/30 px-3 py-3 text-sm text-gray-800 transition-all placeholder:text-gray-300 focus:border-indigo-400 focus:outline-none md:text-base"
          />

          {clothingTrimmed.length > 0 && !isClothingValid && (
            <p className="text-xs text-amber-600">
              En az 8 karakter gerekli ({clothingTrimmed.length}/8)
            </p>
          )}
        </motion.div>
      )}

      {/* Live Preview Summary */}
      <AnimatePresence>
        {(childInfo.name || childInfo.age || childInfo.gender) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="rounded-xl border border-purple-100 bg-gradient-to-r from-purple-50 via-pink-50 to-orange-50 p-3"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500">
                <BookOpen className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-500">Hazırlanan Hikaye</p>
                <p className="font-medium text-gray-800">
                  {childInfo.age && (
                    <span className="text-purple-600">{childInfo.age} yaşındaki </span>
                  )}
                  {childInfo.name ? (
                    <span className="text-pink-600">{childInfo.name}</span>
                  ) : (
                    <span className="text-gray-400">???</span>
                  )}
                  {scenarioName && (
                    <span>
                      {" "}
                      için <span className="text-orange-500">{scenarioName}</span>
                    </span>
                  )}
                  <span> hazırlanıyor...</span>
                </p>
              </div>
              <Sparkles className="h-6 w-6 animate-pulse text-yellow-400" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="flex flex-col gap-4 md:flex-row"
      >
        <Button variant="outline" onClick={onBack} className="md:w-auto">
          Geri
        </Button>

        <motion.div className="flex-1">
          <Button
            onClick={onContinue}
            disabled={!isValid}
            className={`w-full py-4 text-base font-bold transition-all ${
              isValid
                ? "bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 shadow-lg shadow-purple-200 hover:from-purple-700 hover:via-pink-600 hover:to-orange-500"
                : "cursor-not-allowed bg-gray-200 text-gray-500"
            }`}
          >
            {isValid ? (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-2"
              >
                <Sparkles className="h-5 w-5" />
                Devam Et
                <ChevronRight className="h-5 w-5" />
              </motion.span>
            ) : (
              <span className="flex items-center gap-2">Tüm Bilgileri Doldurun</span>
            )}
          </Button>
        </motion.div>
      </motion.div>

      {/* Validation Hint */}
      {!isValid && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center text-sm text-gray-400"
        >
          <span className="inline-flex flex-wrap items-center justify-center gap-1">
            {!childInfo.name && (
              <>
                <span className="h-2 w-2 rounded-full bg-gray-300" />
                Ad
              </>
            )}
            {!childInfo.name && !childInfo.gender && ", "}
            {!childInfo.gender && (
              <>
                <span className="ml-1 h-2 w-2 rounded-full bg-gray-300" />
                Cinsiyet
              </>
            )}
            {(!childInfo.name || !childInfo.gender) && !childInfo.age && ", "}
            {!childInfo.age && (
              <>
                <span className="ml-1 h-2 w-2 rounded-full bg-gray-300" />
                Yaş
              </>
            )}
            {!hideClothing &&
              (!childInfo.name || !childInfo.gender || !childInfo.age) &&
              !isClothingValid &&
              ", "}
            {!hideClothing && !isClothingValid && (
              <>
                <span className="ml-1 h-2 w-2 rounded-full bg-gray-300" />
                Kıyafet
              </>
            )}
            <span className="ml-1">gerekli</span>
          </span>
        </motion.div>
      )}
    </div>
  );
}
