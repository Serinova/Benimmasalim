import { UserPlus, Wand2, Package, type LucideIcon } from "lucide-react";

interface StepData {
  number: string;
  icon: string;
  title: string;
  description: string;
}

interface HowItWorksProps {
  title?: string;
  subtitle?: string;
  data?: { steps?: StepData[] };
}

const ICON_MAP: Record<string, LucideIcon> = { UserPlus, Wand2, Package };

const DEFAULT_STEPS: StepData[] = [
  { number: "1", icon: "UserPlus", title: "Bilgileri Girin", description: "Çocuğunuzun adını, fotoğrafını ve hikaye temasını seçin. Sadece birkaç dakika sürer." },
  { number: "2", icon: "Wand2", title: "Hikayenizi İnceleyin", description: "Yapay zeka çocuğunuza özel benzersiz bir hikaye oluşturur. İnceleyip düzenleyebilirsiniz." },
  { number: "3", icon: "Package", title: "Kapınıza Gelsin!", description: "Profesyonel baskı kalitesiyle hazırlanan kitabınız 2-3 iş günü içinde adresinize ulaşır." },
];

export default function HowItWorks({ title, subtitle, data }: HowItWorksProps) {
  const heading = title ?? "Nasıl Çalışır?";
  const sub = subtitle ?? "Üç kolay adımda çocuğunuza özel kişiselleştirilmiş masal kitabı oluşturun.";
  const steps = (data?.steps ?? DEFAULT_STEPS) as StepData[];

  return (
    <section id="nasil-calisir" className="scroll-mt-20 bg-white py-20 md:py-28">
      <div className="container">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">{heading}</h2>
          <p className="mt-4 text-lg text-slate-500">{sub}</p>
        </div>

        <div className="relative mx-auto max-w-4xl">
          <div className="absolute left-1/2 top-12 hidden h-0.5 w-[60%] -translate-x-1/2 bg-gradient-to-r from-purple-100 via-purple-300 to-purple-100 md:block" aria-hidden="true" />

          <div className="grid gap-10 md:grid-cols-3 md:gap-12">
            {steps.map((step) => {
              const Icon = ICON_MAP[step.icon] ?? UserPlus;
              return (
                <div key={step.number} className="relative flex flex-col items-center text-center">
                  <div className="relative mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-purple-50 ring-4 ring-white shadow-sm">
                    <Icon className="h-8 w-8 text-purple-600" aria-hidden="true" />
                    <span className="absolute -right-1 -top-1 flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-pink-500 text-xs font-bold text-white shadow">
                      {step.number}
                    </span>
                  </div>
                  <h3 className="mb-2 text-xl font-bold text-slate-900">{step.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-500">{step.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
