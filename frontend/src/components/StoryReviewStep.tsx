"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Pencil, Check, X, RefreshCw, Sparkles, BookOpen, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StoryPage {
  page_number: number;
  text: string;
  visual_prompt: string; // Now shown to user for debugging
  scene_description?: string; // Original scene from Gemini
}

interface StoryStructure {
  title: string;
  pages: StoryPage[];
}

interface StoryReviewStepProps {
  storyStructure: StoryStructure;
  childName: string;
  onUpdateStory: (updatedStory: StoryStructure) => void;
  onRegenerateStory: () => void;
  onApproveAndContinue: () => void;
  onBack: () => void;
  isRegenerating?: boolean;
}

export default function StoryReviewStep({
  storyStructure,
  childName,
  onUpdateStory,
  onRegenerateStory,
  onApproveAndContinue,
  onBack,
  isRegenerating = false,
}: StoryReviewStepProps) {
  const [editingPageIndex, setEditingPageIndex] = useState<number | null>(null);
  const [editedText, setEditedText] = useState<string>("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus and select text when editing
  useEffect(() => {
    if (editingPageIndex !== null && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, [editingPageIndex]);

  const handleStartEdit = (pageIndex: number) => {
    setEditingPageIndex(pageIndex);
    setEditedText(storyStructure.pages[pageIndex].text);
  };

  const handleSaveEdit = () => {
    if (editingPageIndex === null) return;

    const updatedPages = [...storyStructure.pages];
    updatedPages[editingPageIndex] = {
      ...updatedPages[editingPageIndex],
      text: editedText,
    };

    onUpdateStory({
      ...storyStructure,
      pages: updatedPages,
    });

    setEditingPageIndex(null);
    setEditedText("");
  };

  const handleCancelEdit = () => {
    setEditingPageIndex(null);
    setEditedText("");
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      handleCancelEdit();
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      handleSaveEdit();
    }
  };

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditedText(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = e.target.scrollHeight + "px";
  };

  return (
    <div className="relative pb-24">
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 text-center"
      >
        {/* Decorative top element */}
        <div className="mb-2 flex items-center justify-center gap-3">
          <div className="h-px w-16 bg-gradient-to-r from-transparent via-amber-400 to-amber-600" />
          <BookOpen className="h-5 w-5 text-amber-600" />
          <div className="h-px w-16 bg-gradient-to-l from-transparent via-amber-400 to-amber-600" />
        </div>

        <h1 className="mb-2 font-serif text-2xl text-amber-900 md:text-3xl">
          İşte {childName}&apos;{childName.slice(-1).match(/[aıouAIOU]/) ? "nın" : "ın"} Hikayesi!
        </h1>

        <p className="mx-auto mb-3 max-w-xl text-sm text-amber-700/80">
          Hikayeyi okuyun, gerekirse düzenleyin ve resimleri çizmeye başlayalım.
        </p>

        {/* Regenerate button */}
        <Button
          variant="outline"
          size="sm"
          onClick={onRegenerateStory}
          disabled={isRegenerating}
          className="border-amber-300 text-amber-700 hover:border-amber-400 hover:bg-amber-50"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isRegenerating ? "animate-spin" : ""}`} />
          {isRegenerating ? "Yeniden Yazılıyor..." : "Hikayeyi Yeniden Yaz"}
        </Button>
      </motion.div>

      {/* Story Title Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mx-auto mb-4 max-w-3xl"
      >
        <div className="manuscript-paper rounded-xl border border-amber-200/50 p-4 text-center">
          <h2 className="font-serif text-xl italic text-amber-900 md:text-2xl">
            &ldquo;{storyStructure.title}&rdquo;
          </h2>
          <p className="mt-2 text-sm text-amber-600/70">
            {storyStructure.pages.filter((p) => p.page_number !== 0).length} sayfalık macera
          </p>
        </div>
      </motion.div>

      {/* Page Cards Container — kapak sayfası (page_number=0) hariç */}
      <div className="mx-auto max-w-3xl space-y-4">
        <AnimatePresence mode="popLayout">
          {storyStructure.pages
            .filter((page) => page.page_number !== 0)
            .map((page, index) => (
              <motion.div
                key={page.page_number}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: index * 0.05 }}
                layout
              >
                <PageCard
                  page={page}
                  pageIndex={index}
                  totalPages={storyStructure.pages.filter((p) => p.page_number !== 0).length}
                  isEditing={editingPageIndex === index}
                  editedText={editedText}
                  onStartEdit={() => handleStartEdit(storyStructure.pages.indexOf(page))}
                  onSaveEdit={handleSaveEdit}
                  onCancelEdit={handleCancelEdit}
                  onTextChange={handleTextareaChange}
                  onKeyDown={handleKeyDown}
                  textareaRef={editingPageIndex === storyStructure.pages.indexOf(page) ? textareaRef : undefined}
                />
              </motion.div>
            ))}
        </AnimatePresence>
      </div>

      {/* Sticky Footer */}
      <div className="fixed bottom-0 left-0 right-0 z-50">
        <div className="bg-gradient-to-t from-purple-50 via-purple-50/95 to-transparent pb-4 pt-6">
          <div className="mx-auto max-w-3xl px-4">
            <div className="flex items-center gap-3">
              {/* Back Button */}
              <Button
                variant="outline"
                onClick={onBack}
                className="border-gray-300 text-gray-600 hover:bg-gray-50"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Geri
              </Button>

              {/* Main CTA Button */}
              <button
                onClick={onApproveAndContinue}
                disabled={editingPageIndex !== null || isRegenerating}
                className="magic-button relative flex-1 rounded-xl px-6 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {/* Sparkle effects */}
                <SparkleEffect />

                <span className="relative z-10 flex items-center justify-center gap-3">
                  <Sparkles className="h-5 w-5 animate-sparkle" />
                  <span className="text-lg">Harika! Resimleri Çizmeye Başla</span>
                  <span className="text-xl">🎨</span>
                </span>
              </button>
            </div>

            {/* Helper text */}
            {editingPageIndex !== null && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-3 text-center text-sm text-amber-600"
              >
                Düzenlemeyi tamamlamak için ✓ butonuna tıklayın veya Ctrl+Enter tuşlayın
              </motion.p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Page Card Component
interface PageCardProps {
  page: StoryPage;
  pageIndex: number;
  totalPages: number;
  isEditing: boolean;
  editedText: string;
  onStartEdit: () => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onTextChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  textareaRef?: React.RefObject<HTMLTextAreaElement>;
}

function PageCard({
  page,
  pageIndex,
  totalPages,
  isEditing,
  editedText,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onTextChange,
  onKeyDown,
  textareaRef,
}: PageCardProps) {
  const isCover = page.page_number === 0;

  return (
    <div
      className={`
        manuscript-paper overflow-hidden rounded-2xl transition-all duration-300
        ${
          isEditing
            ? "shadow-lg ring-2 ring-amber-400 ring-offset-2 ring-offset-purple-50"
            : "border border-amber-200/50 hover:border-amber-300/70 hover:shadow-md"
        }
      `}
    >
      {/* Page Header with Bookmark */}
      <div className="relative">
        <div className="page-bookmark">{isCover ? "Kapak" : `Sayfa ${page.page_number}`}</div>

        {/* Edit/Save buttons */}
        <div className="absolute right-3 top-3 flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={onSaveEdit}
                className="rounded-full bg-green-100 p-2 text-green-600 transition-colors hover:bg-green-200"
                title="Kaydet (Ctrl+Enter)"
              >
                <Check className="h-4 w-4" />
              </button>
              <button
                onClick={onCancelEdit}
                className="rounded-full bg-red-100 p-2 text-red-500 transition-colors hover:bg-red-200"
                title="İptal (Esc)"
              >
                <X className="h-4 w-4" />
              </button>
            </>
          ) : (
            <button
              onClick={onStartEdit}
              className="rounded-full bg-amber-100/80 p-2 text-amber-600 opacity-0 transition-all hover:bg-amber-200 group-hover:opacity-100"
              title="Düzenle"
              style={{ opacity: 1 }} // Always visible for better UX
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Page Content */}
      <div className="p-6 pt-4">
        {isEditing ? (
          <textarea
            ref={textareaRef as React.RefObject<HTMLTextAreaElement>}
            value={editedText}
            onChange={onTextChange}
            onKeyDown={onKeyDown}
            className="manuscript-text editable-story-text min-h-[120px] w-full resize-none bg-transparent text-lg outline-none md:text-xl"
            style={{ height: "auto" }}
          />
        ) : (
          <p
            className="manuscript-text -m-2 cursor-pointer rounded-lg p-2 text-lg transition-colors hover:bg-amber-50/50 md:text-xl"
            onClick={onStartEdit}
          >
            {page.text}
          </p>
        )}
      </div>

      {/* Visual Prompt — sadece geliştirme ortamında göster */}

      {/* Page Footer - subtle page indicator */}
      <div className="flex justify-end px-6 pb-4">
        <span className="text-xs font-medium text-amber-400/60">
          {pageIndex + 1} / {totalPages}
        </span>
      </div>
    </div>
  );
}

// Sparkle Effect Component for CTA Button
function SparkleEffect() {
  const sparklePositions = [
    { top: "10%", left: "5%", delay: "0s" },
    { top: "20%", right: "10%", delay: "0.3s" },
    { bottom: "15%", left: "15%", delay: "0.6s" },
    { top: "50%", right: "5%", delay: "0.9s" },
    { bottom: "20%", right: "20%", delay: "1.2s" },
    { top: "30%", left: "25%", delay: "1.5s" },
  ];

  return (
    <div className="sparkle-container rounded-xl">
      {sparklePositions.map((pos, i) => (
        <span
          key={i}
          className="sparkle"
          style={{
            ...pos,
            animationDelay: pos.delay,
          }}
        />
      ))}
    </div>
  );
}
