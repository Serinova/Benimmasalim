"use client";

import { useState, useMemo, forwardRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Moon,
  Baby,
  Hand,
  Apple,
  ShieldCheck,
  Hourglass,
  TrendingUp,
  HeartHandshake,
  Eraser,
  Gift,
  Users,
  MessageCircleHeart,
  Flag,
  Leaf,
  Search,
  Smartphone,
  GraduationCap,
  PiggyBank,
  Sun,
  Check,
  X,
  ChevronRight,
  Wand2,
  FlaskConical,
  RotateCcw,
  AlertCircle,
  Star,
  Heart,
  Lightbulb,
  Shield,
  Target,
  BookOpen,
  Loader2,
} from "lucide-react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";

// API Types
interface LearningOutcomeItem {
  id: string;
  name: string;
  description: string | null;
  icon_url: string | null;
  color_theme: string | null;
  ai_prompt: string | null;
  ai_prompt_instruction: string | null;
}

interface LearningOutcomeCategoryGroup {
  category: string;
  category_label: string;
  items: LearningOutcomeItem[];
}

interface LearningOutcomeSelectorProps {
  selectedOutcomes: string[];
  onSelect: (outcomes: string[]) => void;
  onContinue: () => void;
  onBack: () => void;
}

// Category icon mapping
const categoryIcons: Record<string, typeof Star> = {
  SelfCare: Heart,
  PersonalGrowth: Lightbulb,
  SocialSkills: Users,
  EducationNature: Leaf,
  Values: Shield,
};

// Category colors (fallback if not from DB)
const categoryColors: Record<string, { bg: string; border: string; text: string; light: string }> =
  {
    SelfCare: {
      bg: "bg-pink-500",
      border: "border-pink-500",
      text: "text-pink-600",
      light: "bg-pink-50",
    },
    PersonalGrowth: {
      bg: "bg-amber-500",
      border: "border-amber-500",
      text: "text-amber-600",
      light: "bg-amber-50",
    },
    SocialSkills: {
      bg: "bg-blue-500",
      border: "border-blue-500",
      text: "text-blue-600",
      light: "bg-blue-50",
    },
    EducationNature: {
      bg: "bg-green-500",
      border: "border-green-500",
      text: "text-green-600",
      light: "bg-green-50",
    },
    Values: {
      bg: "bg-purple-500",
      border: "border-purple-500",
      text: "text-purple-600",
      light: "bg-purple-50",
    },
  };

// Default icon mapping for items (fallback) — reserved for future use
const _defaultIconMap: Record<string, React.ElementType> = {
  Sparkles,
  Moon,
  Baby,
  Hand,
  Apple,
  ShieldCheck,
  Hourglass,
  TrendingUp,
  HeartHandshake,
  Eraser,
  Gift,
  Users,
  MessageCircleHeart,
  Flag,
  Leaf,
  Search,
  Smartphone,
  GraduationCap,
  PiggyBank,
  Sun,
  Heart,
  Lightbulb,
  Shield,
  Target,
  BookOpen,
  Star,
};

// Helper to get color from hex or category
function getColorStyle(colorTheme: string | null, category: string) {
  if (colorTheme) {
    return {
      bg: colorTheme,
      border: colorTheme,
      text: colorTheme,
      light: `${colorTheme}15`,
    };
  }
  return categoryColors[category] || categoryColors.Values;
}

// Outcome Card Component
function OutcomeCard({
  outcome,
  category,
  isSelected,
  isDisabled,
  onToggle,
}: {
  outcome: LearningOutcomeItem;
  category: string;
  isSelected: boolean;
  isDisabled: boolean;
  onToggle: () => void;
}) {
  const [isShaking, setIsShaking] = useState(false);
  const _colorStyle = getColorStyle(outcome.color_theme, category);
  const CategoryIcon = categoryIcons[category] || Sparkles;

  const handleClick = () => {
    if (isDisabled && !isSelected) {
      setIsShaking(true);
      setTimeout(() => setIsShaking(false), 500);
      return;
    }
    onToggle();
  };

  // Determine background and border colors
  const bgColor = outcome.color_theme
    ? `${outcome.color_theme}15`
    : categoryColors[category]?.light || "bg-purple-50";
  const borderColor =
    outcome.color_theme || categoryColors[category]?.border?.replace("border-", "") || "#8B5CF6";
  const textColor =
    outcome.color_theme || categoryColors[category]?.text?.replace("text-", "") || "#8B5CF6";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{
        opacity: 1,
        scale: 1,
        x: isShaking ? [0, -10, 10, -10, 10, 0] : 0,
      }}
      transition={{
        duration: isShaking ? 0.4 : 0.3,
        type: isShaking ? "tween" : "spring",
      }}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.95 }}
      onClick={handleClick}
      className={`relative cursor-pointer rounded-2xl border-2 p-4 transition-all duration-300 ${
        isSelected
          ? "shadow-lg"
          : isDisabled
            ? "border-gray-200 bg-gray-50 opacity-60"
            : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-md"
      }`}
      style={
        isSelected
          ? {
              borderColor: borderColor,
              backgroundColor: bgColor,
            }
          : undefined
      }
    >
      {/* Selected Badge */}
      <AnimatePresence>
        {isSelected && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full shadow-lg"
            style={{ backgroundColor: borderColor }}
          >
            <Check className="h-4 w-4 text-white" strokeWidth={3} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Icon */}
      <div
        className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl"
        style={{
          backgroundColor: isSelected ? borderColor : "#f3f4f6",
        }}
      >
        {outcome.icon_url ? (
          <Image src={outcome.icon_url} alt="" width={28} height={28} className="h-7 w-7" unoptimized />
        ) : (
          <CategoryIcon className={`h-6 w-6 ${isSelected ? "text-white" : "text-gray-600"}`} />
        )}
      </div>

      {/* Content */}
      <h3
        className="mb-1 text-base font-bold"
        style={{ color: isSelected ? textColor : "#1f2937" }}
      >
        {outcome.name}
      </h3>
      <p className="text-sm leading-relaxed text-gray-500">{outcome.description || ""}</p>

      {/* Category Tag */}
      <div
        className="mt-3 inline-flex items-center rounded-full px-2 py-1 text-xs font-medium"
        style={
          isSelected
            ? {
                backgroundColor: borderColor,
                color: "white",
              }
            : {
                backgroundColor: "#f3f4f6",
                color: "#4b5563",
              }
        }
      >
        {categoryColors[category] ? category.replace(/([A-Z])/g, " $1").trim() : category}
      </div>
    </motion.div>
  );
}

// Selected Pills Component
const SelectedPills = forwardRef<
  HTMLDivElement,
  {
    selectedOutcomes: string[];
    outcomes: LearningOutcomeItem[];
    categories: LearningOutcomeCategoryGroup[];
    onRemove: (id: string) => void;
  }
>(function SelectedPills({ selectedOutcomes, outcomes, categories, onRemove }, ref) {
  return (
    <div ref={ref} className="flex flex-wrap gap-2">
      {selectedOutcomes.map((id) => {
        const outcome = outcomes.find((o) => o.id === id);
        if (!outcome) return null;

        // Find category for this outcome
        const categoryGroup = categories.find((cat) => cat.items.some((item) => item.id === id));
        const category = categoryGroup?.category || "Values";
        const _colorStyle = getColorStyle(outcome.color_theme, category);
        const CategoryIcon = categoryIcons[category] || Sparkles;
        const borderColor =
          outcome.color_theme ||
          categoryColors[category]?.border?.replace("border-", "") ||
          "#8B5CF6";

        return (
          <motion.div
            key={id}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            className="flex items-center gap-2 rounded-full border px-3 py-1.5"
            style={{
              backgroundColor: `${borderColor}15`,
              borderColor: borderColor,
            }}
          >
            {outcome.icon_url ? (
              <Image src={outcome.icon_url} alt="" width={16} height={16} className="h-4 w-4" unoptimized />
            ) : (
              <CategoryIcon className="h-4 w-4" style={{ color: borderColor }} />
            )}
            <span className="text-sm font-medium" style={{ color: borderColor }}>
              {outcome.name}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(id);
              }}
              className="flex h-5 w-5 items-center justify-center rounded-full transition hover:opacity-80"
              style={{ backgroundColor: borderColor }}
            >
              <X className="h-3 w-3 text-white" />
            </button>
          </motion.div>
        );
      })}
    </div>
  );
});

export default function LearningOutcomeSelector({
  selectedOutcomes,
  onSelect,
  onContinue,
  onBack,
}: LearningOutcomeSelectorProps) {
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<LearningOutcomeCategoryGroup[]>([]);
  const { toast } = useToast();

  const MAX_SELECTIONS = 1;

  // Fetch learning outcomes from API
  useEffect(() => {
    const fetchOutcomes = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/scenarios/learning-outcomes`);
        if (response.ok) {
          const data: LearningOutcomeCategoryGroup[] = await response.json();
          setCategories(data);
        } else {
          toast({
            title: "Hata",
            description: "Kazanımlar yüklenemedi",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Failed to fetch learning outcomes:", error);
        toast({
          title: "Hata",
          description: "Sunucuya bağlanılamadı",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchOutcomes();
  }, [toast]);

  // Flatten all outcomes for easy lookup
  const allOutcomes = useMemo(() => {
    return categories.flatMap((cat) => cat.items);
  }, [categories]);

  // Build category tabs
  const categoryTabs = useMemo(() => {
    const tabs = [{ id: "all", label: "Tümü", icon: Star }];
    categories.forEach((cat) => {
      tabs.push({
        id: cat.category,
        label: cat.category_label,
        icon: categoryIcons[cat.category] || Sparkles,
      });
    });
    return tabs;
  }, [categories]);

  // Filter outcomes
  const filteredOutcomes = useMemo(() => {
    const filtered: Array<{ item: LearningOutcomeItem; category: string }> = [];

    categories.forEach((cat) => {
      if (activeCategory === "all" || cat.category === activeCategory) {
        cat.items.forEach((item) => {
          const matchesSearch =
            searchQuery === "" ||
            item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (item.description &&
              item.description.toLowerCase().includes(searchQuery.toLowerCase()));

          if (matchesSearch) {
            filtered.push({ item, category: cat.category });
          }
        });
      }
    });

    return filtered;
  }, [categories, activeCategory, searchQuery]);

  // Toggle selection — single select: clicking a new one replaces the old
  const handleToggle = (id: string) => {
    if (selectedOutcomes.includes(id)) {
      onSelect(selectedOutcomes.filter((o) => o !== id));
    } else {
      // Replace current selection (single select mode)
      onSelect([id]);
    }
  };

  // Reset selections
  const handleReset = () => {
    onSelect([]);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="mb-4 h-12 w-12 animate-spin text-purple-600" />
        <p className="text-gray-500">Sihirli malzemeler yükleniyor...</p>
      </div>
    );
  }

  if (categories.length === 0) {
    return (
      <div className="py-20 text-center">
        <AlertCircle className="mx-auto mb-4 h-16 w-16 text-gray-300" />
        <h3 className="mb-2 text-xl font-semibold text-gray-700">Henüz kazanım tanımlanmamış</h3>
        <p className="mb-6 text-gray-500">Admin panelinden kazanım ekleyebilirsiniz.</p>
        <Button variant="outline" onClick={onBack}>
          Geri Dön
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Hero Section */}
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-2 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-purple-100 via-pink-100 to-orange-100 px-3 py-1.5"
        >
          <FlaskConical className="h-4 w-4 text-purple-600" />
          <span className="text-sm font-medium text-purple-700">Karakter Tarifi</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 bg-clip-text text-2xl font-bold text-transparent md:text-3xl"
        >
          Sihirli Malzemeleri Seçin
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mx-auto mt-3 max-w-lg text-gray-600"
        >
          Hikayenize hangi değeri eklemek istersiniz?
          <span className="font-medium text-purple-600"> 1 tane</span> seçin.
        </motion.p>
      </div>

      {/* Sticky Selection Status */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-20 rounded-2xl border border-gray-200 bg-white/90 p-4 shadow-lg backdrop-blur-md"
      >
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          {/* Selection Counter */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full ${
                  selectedOutcomes.length === MAX_SELECTIONS
                    ? "bg-gradient-to-r from-green-500 to-emerald-500"
                    : "bg-gradient-to-r from-purple-500 to-pink-500"
                }`}
              >
                <Wand2 className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Seçilen Malzeme</p>
                <p className="text-lg font-bold">
                  <span
                    className={
                      selectedOutcomes.length === MAX_SELECTIONS
                        ? "text-green-600"
                        : "text-purple-600"
                    }
                  >
                    {selectedOutcomes.length}
                  </span>
                  <span className="text-gray-400"> / {MAX_SELECTIONS}</span>
                </p>
              </div>
            </div>

            {/* Progress Dots */}
            <div className="ml-4 hidden items-center gap-1.5 md:flex">
              {[...Array(MAX_SELECTIONS)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ scale: 0 }}
                  animate={{
                    scale: 1,
                    backgroundColor: i < selectedOutcomes.length ? "#8B5CF6" : "#E5E7EB",
                  }}
                  className="h-3 w-3 rounded-full"
                />
              ))}
            </div>
          </div>

          {/* Selected Pills */}
          <div className="min-w-0 flex-1 overflow-x-auto">
            <AnimatePresence mode="popLayout">
              {selectedOutcomes.length > 0 ? (
                <SelectedPills
                  selectedOutcomes={selectedOutcomes}
                  outcomes={allOutcomes}
                  categories={categories}
                  onRemove={(id) => onSelect(selectedOutcomes.filter((o) => o !== id))}
                />
              ) : (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-sm italic text-gray-400"
                >
                  Henüz seçim yapılmadı...
                </motion.p>
              )}
            </AnimatePresence>
          </div>

          {/* Reset Button */}
          {selectedOutcomes.length > 0 && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleReset}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-gray-500 transition hover:bg-red-50 hover:text-red-500"
            >
              <RotateCcw className="h-4 w-4" />
              Sıfırla
            </motion.button>
          )}
        </div>
      </motion.div>

      {/* Category Tabs & Search */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="flex flex-col gap-4 md:flex-row"
      >
        {/* Category Pills */}
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
          {categoryTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeCategory === tab.id;

            return (
              <motion.button
                key={tab.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveCategory(tab.id)}
                className={`flex items-center gap-2 whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </motion.button>
            );
          })}
        </div>

        {/* Search Bar */}
        <div className="relative max-w-xs flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Ara... (örn: Cesaret)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-full border border-gray-200 py-2 pl-10 pr-4 text-sm outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full bg-gray-200 transition hover:bg-gray-300"
            >
              <X className="h-3 w-3 text-gray-600" />
            </button>
          )}
        </div>
      </motion.div>

      {/* Warning if max reached */}
      <AnimatePresence>
        {selectedOutcomes.length === MAX_SELECTIONS && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-amber-700"
          >
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm">
              Seçiminiz tamamlandı. Farklı bir özellik seçmek için önce mevcut seçimi kaldırın.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Outcomes Grid - Bento Style */}
      <motion.div layout className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        <AnimatePresence mode="popLayout">
          {filteredOutcomes.map(({ item, category }, index) => (
            <motion.div
              key={item.id}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ delay: index * 0.03 }}
            >
              <OutcomeCard
                outcome={item}
                category={category}
                isSelected={selectedOutcomes.includes(item.id)}
                isDisabled={selectedOutcomes.length >= MAX_SELECTIONS}
                onToggle={() => handleToggle(item.id)}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {/* Empty State */}
      {filteredOutcomes.length === 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="py-12 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
            <Search className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="mb-2 text-lg font-medium text-gray-700">Sonuç Bulunamadı</h3>
          <p className="text-gray-500">
            &quot;{searchQuery}&quot; ile eşleşen özellik yok. Farklı bir terim deneyin.
          </p>
          <Button
            variant="outline"
            onClick={() => {
              setSearchQuery("");
              setActiveCategory("all");
            }}
            className="mt-4"
          >
            Filtreleri Temizle
          </Button>
        </motion.div>
      )}

      {/* Bottom Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex flex-col gap-4 border-t border-gray-200 pt-6 md:flex-row"
      >
        <Button variant="outline" onClick={onBack} className="md:w-auto">
          Geri
        </Button>

        <Button
          onClick={onContinue}
          disabled={selectedOutcomes.length === 0}
          className="flex-1 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 py-6 text-lg font-bold shadow-lg shadow-purple-200 hover:from-purple-700 hover:via-pink-600 hover:to-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {selectedOutcomes.length === 0 ? (
            "En Az 1 Özellik Seçin"
          ) : (
            <>
              Devam Et
              <ChevronRight className="ml-2 h-5 w-5" />
            </>
          )}
        </Button>
      </motion.div>

      {/* Skip Option */}
      <div className="text-center">
        <button
          onClick={onContinue}
          className="text-sm text-gray-400 underline underline-offset-4 transition hover:text-gray-600"
        >
          Bu adımı atla
        </button>
      </div>
    </div>
  );
}
