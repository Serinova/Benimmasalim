/**
 * Server-side data fetcher for homepage sections.
 * Called from page.tsx (Server Component) at request time.
 */

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

export interface HomepageSectionData {
  section_type: string;
  title: string | null;
  subtitle: string | null;
  sort_order: number;
  data: Record<string, unknown>;
}

/**
 * Fetch visible homepage sections from the public API.
 * Returns empty array on failure — components use their built-in defaults.
 */
export async function getHomepageSections(): Promise<HomepageSectionData[]> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/homepage`, {
      next: { revalidate: 60 }, // ISR: revalidate every 60 seconds
    });
    if (!res.ok) return [];
    return (await res.json()) as HomepageSectionData[];
  } catch {
    // Backend unreachable — fallback to component defaults
    return [];
  }
}

/**
 * Helper: find a section by type from the fetched array.
 */
export function findSection(
  sections: HomepageSectionData[],
  type: string
): HomepageSectionData | undefined {
  return sections.find((s) => s.section_type === type);
}

/* ─── Product data for Pricing section ─────────────────────── */

export interface ProductForPricing {
  id: string;
  name: string;
  base_price: number;
  discounted_price: number | null;
  default_page_count: number;
  extra_page_price: number;
  cover_type: string;
  paper_type: string;
  promo_badge: string | null;
  feature_list: string[];
  rating: number | null;
  review_count: number;
  social_proof_text: string | null;
  thumbnail_url: string | null;
}

/**
 * Fetch active products from API for the pricing section.
 * Returns empty array on failure.
 */
export async function getProducts(): Promise<ProductForPricing[]> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/products`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    return (await res.json()) as ProductForPricing[];
  } catch {
    return [];
  }
}

/* ─── Scenario data for Adventures/Products section ────────── */

export interface ScenarioForHomepage {
  id: string;
  name: string;
  description: string | null;
  thumbnail_url: string;
  tagline: string | null;
  marketing_badge: string | null;
  marketing_price_label: string | null;
  marketing_features: string[] | null;
  age_range: string | null;
  estimated_duration: string | null;
  rating: number | null;
  review_count: number | null;
  marketing_gallery: string[] | null;
  default_page_count: number | null;
  linked_product_page_count: number | null;
  story_page_count: number | null;
  cover_count: number | null;
  greeting_page_count: number | null;
  back_info_page_count: number | null;
  total_page_count: number | null;
}

/**
 * Fetch active scenarios for the homepage adventures section.
 * Returns empty array on failure.
 */
export async function getScenarios(): Promise<ScenarioForHomepage[]> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/scenarios`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    return (await res.json()) as ScenarioForHomepage[];
  } catch {
    return [];
  }
}
