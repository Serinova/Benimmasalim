import {
  Sparkles,
  BookOpen,
  Palette,
  Headphones,
  Camera,
  Fingerprint,
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
};

const DEFAULT_ITEMS: FeatureItem[] = [
  { icon: "Sparkles", title: "AI Kişiselleştirme", description: "Her kitap %100 özgün. Yapay zeka çocuğunuzun adı ve özellikleriyle benzersiz hikayeler oluşturur." },
  { icon: "BookOpen", title: "Eğitici Değerler", description: "Özgüven, paylaşma, cesaret gibi değerleri eğlenceli hikayelerle çocuğunuza öğretin." },
  { icon: "Palette", title: "Profesyonel Baskı", description: "Yüksek kalite kağıt ve canlı renklerle baskı. Gerçek bir kitap deneyimi sunar." },
  { icon: "Headphones", title: "Sesli Kitap Seçeneği", description: "Hikayenizi sesli kitap olarak da dinleyin. Kendi sesinizle veya profesyonel seslendirme ile." },
  { icon: "Camera", title: "Çocuğunuzun Fotoğrafıyla", description: "Fotoğraf yükleyin, yapay zeka çocuğunuzu hikayenin kahramanı yapsın. Tam kişiselleştirilmiş masal." },
  { icon: "Fingerprint", title: "%100 Özgün Hikaye", description: "Hazır şablonlar değil, tamamen sıfırdan yazılan çocuğun adıyla masal. Her kitap tek ve benzersiz." },
];

export default function Features({ title, subtitle, data }: FeaturesProps) {
  const heading = title ?? "Neden Benim Masalım?";
  const sub = subtitle ?? "Kişiye özel çocuk kitabı oluşturmanın en kolay ve kaliteli yolu.";
  const items = (data?.items ?? DEFAULT_ITEMS) as FeatureItem[];

  return (
    <section className="bg-muted/30 py-20">
      <div className="container">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((feature) => {
            const Icon = ICON_MAP[feature.icon] ?? Sparkles;
            return (
              <div key={feature.title} className="group rounded-xl border bg-card p-6 shadow-sm transition-all hover:shadow-md">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 transition-colors group-hover:bg-primary/20">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
