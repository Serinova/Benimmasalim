export const STEP_COUNT = 5;

export interface StepDef {
  id: number;
  label: string;
  shortLabel: string;
}

export const STEPS: StepDef[] = [
  { id: 1, label: "Kahraman & Macera", shortLabel: "Kahraman" },
  { id: 2, label: "Fotoğraf & Stil", shortLabel: "Fotoğraf" },
  { id: 3, label: "Kitap Önizleme", shortLabel: "Önizleme" },
  { id: 4, label: "Ekstralar & Teslimat", shortLabel: "Teslimat" },
  { id: 5, label: "Ödeme", shortLabel: "Ödeme" },
];

export const AGES = ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12"] as const;

export const MAX_PHOTO_SIZE_MB = 10;
export const MAX_PHOTO_SIZE_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024;
export const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

export const MAX_NAME_LENGTH = 30;
export const MIN_NAME_LENGTH = 2;
export const MAX_DEDICATION_LENGTH = 300;
export const MAX_ADDRESS_LENGTH = 500;

export const POLLING_INTERVAL_MS = 6000; // 6s — reduced from 3s to cut server load by 50%
export const POLLING_MAX_ATTEMPTS = 60;  // 60 × 6s = 6 min total timeout (same as before)

export const SESSION_KEY = "orderDraft_v2";
