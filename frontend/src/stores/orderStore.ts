/**
 * Order wizard state management — Prompt System V2.
 *
 * Centralized V2 fields: IDs + child meta + clothing.
 * Frontend never composes prompts — backend is source of truth.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { StoryPage } from "@/lib/api";

export interface OrderState {
  // Step tracking
  currentStep: number;

  // Selections (V2: IDs only)
  productId: string | null;
  scenarioId: string | null;
  visualStyleId: string | null;
  selectedOutcomes: string[];

  // Child info
  childName: string;
  childAge: number;
  childGender: string | null;

  // V2: Clothing description (outfit lock for all pages)
  clothingDescription: string;
  selectedOutfitIndex: number | null;
  outfitSuggestions: string[];

  // Photo
  photoUrl: string | null;
  faceScore: number | null;

  // Generated content (V2)
  previewId: string | null;
  trialToken: string | null;
  storyTitle: string | null;
  storyPages: StoryPage[];

  // Audio
  hasAudioBook: boolean;
  audioType: "system" | "cloned" | null;

  // Actions
  setStep: (step: number) => void;
  setProduct: (id: string) => void;
  setScenario: (id: string) => void;
  setVisualStyle: (id: string) => void;
  toggleOutcome: (id: string) => void;
  setChildInfo: (name: string, age: number, gender: string | null) => void;
  setClothingDescription: (desc: string) => void;
  setOutfitSuggestions: (suggestions: string[]) => void;
  selectOutfit: (index: number) => void;
  setPhoto: (url: string | null, score: number | null) => void;
  setPreviewId: (id: string | null, token?: string | null) => void;
  setStory: (title: string, pages: StoryPage[]) => void;
  setAudioBook: (has: boolean, type: "system" | "cloned" | null) => void;
  reset: () => void;
}

const initialState = {
  currentStep: 0,
  productId: null,
  scenarioId: null,
  visualStyleId: null,
  selectedOutcomes: [] as string[],
  childName: "",
  childAge: 7,
  childGender: null,
  clothingDescription: "",
  selectedOutfitIndex: null,
  outfitSuggestions: [] as string[],
  photoUrl: null,
  faceScore: null,
  previewId: null,
  trialToken: null,
  storyTitle: null,
  storyPages: [] as StoryPage[],
  hasAudioBook: false,
  audioType: null,
};

export const useOrderStore = create<OrderState>()(
  persist(
    (set) => ({
      ...initialState,

      setStep: (step) => set({ currentStep: step }),
      setProduct: (id) => set({ productId: id }),
      setScenario: (id) => set({ scenarioId: id }),
      setVisualStyle: (id) => set({ visualStyleId: id }),

      toggleOutcome: (id) =>
        set((state) => {
          const outcomes = state.selectedOutcomes.includes(id)
            ? state.selectedOutcomes.filter((o) => o !== id)
            : state.selectedOutcomes.length < 3
              ? [...state.selectedOutcomes, id]
              : state.selectedOutcomes;
          return { selectedOutcomes: outcomes };
        }),

      setChildInfo: (name, age, gender) =>
        set({ childName: name, childAge: age, childGender: gender }),

      setClothingDescription: (desc) => set({ clothingDescription: desc }),

      setOutfitSuggestions: (suggestions) => set({ outfitSuggestions: suggestions }),

      selectOutfit: (index) =>
        set((state) => ({
          selectedOutfitIndex: index,
          clothingDescription: state.outfitSuggestions[index] || state.clothingDescription,
        })),

      setPhoto: (url, score) => set({ photoUrl: url, faceScore: score }),

      setPreviewId: (id, token) => set({ previewId: id, trialToken: token ?? null }),

      setStory: (title, pages) => set({ storyTitle: title, storyPages: pages }),

      setAudioBook: (has, type) => set({ hasAudioBook: has, audioType: type }),

      reset: () => set(initialState),
    }),
    {
      name: "order-storage",
      partialize: (state) => ({
        productId: state.productId,
        scenarioId: state.scenarioId,
        visualStyleId: state.visualStyleId,
        selectedOutcomes: state.selectedOutcomes,
        childName: state.childName,
        childAge: state.childAge,
        childGender: state.childGender,
        clothingDescription: state.clothingDescription,
        selectedOutfitIndex: state.selectedOutfitIndex,
        outfitSuggestions: state.outfitSuggestions,
        previewId: state.previewId,
        trialToken: state.trialToken,
      }),
    }
  )
);
