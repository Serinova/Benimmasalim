import {
  Sparkles,
  BookOpen,
  Palette,
  Headphones,
  Camera,
  Fingerprint,
  PaintBucket,
  type LucideIcon,
} from "lucide-react";

interface FeatureItem {
  icon: string;
  title: string;
  description: string;
}

interface FeaturesProps {
  title?: string;
  subtitle?: string;
  data?: { items?: FeatureItem[] };
}

const ICON_MAP: Record<string, LucideIcon> = {
  Sparkles,
  BookOpen,
  Palette,
  Headphones,
  Camera,
  Fingerprint,
  PaintBucket,
};

const DEFAULT_ITEMS: FeatureItem[] = [
  { icon: "Sparkles", title: "AI Kişiselleştirme", description: "Her kitap %100 özgün. Yapay zeka çocuğunuzun adı ve özellikleriyle benzersiz hikayeler oluşturur." },
  { icon: "BookOpen", title: "Eğitici Değerler", description: "Özgüven, paylaşma, cesaret gibi değerleri eğlenceli hikayelerle çocuğunuza öğretin." },
  { icon: "Palette", title: "Profesyonel Baskı", description: "Yüksek kalite kağıt ve canlı renklerle baskı. Gerçek bir kitap deneyimi sunar." },
  { icon: "Headphones", title: "Sesli Kitap Seçeneği", description: "Hikayenizi sesli kitap olarak da dinleyin. Kendi sesinizle veya profesyonel seslendirme ile." },
  { icon: "Camera", title: "Çocuğunuzun Fotoğrafıyla", description: "Fotoğraf yükleyin, yapay zeka çocuğunuzu hikayenin kahramanı yapsın. Tam kişiselleştirilmiş masal." },
  { icon: "PaintBucket", title: "Boyama Kitabı Seçeneği", description: "Hikayenizdeki aynı karakterler ve sahneler boyama kitabına dönüşsün! Profesyonel line-art çizimler, yaratıcılığı geliştiren aktivite." },
];

export default function Features({ title, subtitle, data }: FeaturesProps) {
  const heading = title ?? "Neden Benim Masalım?";
  const sub = subtitle ?? "Kişiye özel çocuk kitabı oluşturmanın en kolay ve kaliteli yolu.";
  const items = (data?.items ?? DEFAULT_ITEMS) as FeatureItem[];

  return (
    <section className="bg-slate-50 py-20 md:py-28">
      <div className="container">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-slate-500">{sub}</p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((feature) => {
            const Icon = ICON_MAP[feature.icon] ?? Sparkles;
            return (
              <div key={feature.title} className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 transition-colors group-hover:bg-purple-100">
                  <Icon className="h-6 w-6 text-purple-600" aria-hidden="true" />
                </div>
                <h3 className="mb-2 text-lg font-bold text-slate-900">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-slate-500">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
