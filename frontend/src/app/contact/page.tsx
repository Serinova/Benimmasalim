import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";
import { Mail, Phone, MapPin, Globe, FileText, Building2 } from "lucide-react";

export const metadata: Metadata = {
  title: "İletişim | Benim Masalım",
  description:
    "Benim Masalım iletişim bilgileri. Adres, telefon, KEP adresi ve e-posta ile bize ulaşın.",
};

export default function ContactPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-3xl flex-1 px-4 py-12 text-slate-700">
        <h1 className="mb-8 text-3xl font-bold text-slate-900">İletişim</h1>

        <p className="mb-8 leading-relaxed">
          Sorularınız, önerileriniz veya geri bildirimleriniz için aşağıdaki
          kanallardan bize ulaşabilirsiniz.
        </p>

        {/* --- Yasal Bilgiler (6563 sayılı Kanun gereği) --- */}
        <section className="mb-10 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold text-slate-900">
            Satıcı Bilgileri
          </h2>
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="font-semibold text-slate-500">Ad Soyad</dt>
              <dd className="mt-0.5">Abdullah Alpaslan</dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-500">İşletme Adı</dt>
              <dd className="mt-0.5">Benim Masalım</dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-500">Vergi Dairesi</dt>
              <dd className="mt-0.5">İkitelli</dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-500">Vergi Kimlik No</dt>
              <dd className="mt-0.5">16106557652</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="font-semibold text-slate-500">Merkez Adresi</dt>
              <dd className="mt-0.5">
                İkitelli OSB Mah. Heskoop M2 Blok Sk. Heskoop M2 Blok No: 20
                Başakşehir / İstanbul
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-500">KEP Adresi</dt>
              <dd className="mt-0.5">
                <a
                  href="mailto:abdullah.alpaslan.2@hs01.kep.tr"
                  className="font-medium text-purple-600 underline hover:text-purple-800"
                >
                  abdullah.alpaslan.2@hs01.kep.tr
                </a>
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-500">Meslek Odası</dt>
              <dd className="mt-0.5">
                İstanbul Matbaacılar Odası —{" "}
                <a
                  href="https://www.istanbulmatbaacilar.org.tr"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-purple-600 underline hover:text-purple-800"
                >
                  istanbulmatbaacilar.org.tr
                </a>
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-500">Faaliyet Kodu</dt>
              <dd className="mt-0.5">181201 — Basım Hizmetleri</dd>
            </div>
          </dl>
        </section>

        {/* --- İletişim Kartları --- */}
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <MapPin className="h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 font-semibold text-slate-900">Adres</h2>
              <p className="text-sm leading-relaxed">
                İkitelli OSB Mah. Heskoop M2 Blok Sk.
                <br />
                Heskoop M2 Blok No: 20
                <br />
                Başakşehir / İstanbul
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <Phone className="h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 font-semibold text-slate-900">Telefon</h2>
              <a
                href="tel:+905333239242"
                className="text-sm font-medium text-purple-600 underline hover:text-purple-800"
              >
                0533 323 92 42
              </a>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 font-semibold text-slate-900">E-posta</h2>
              <a
                href="mailto:info@benimmasalim.com.tr"
                className="text-sm font-medium text-purple-600 underline hover:text-purple-800"
              >
                info@benimmasalim.com.tr
              </a>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 font-semibold text-slate-900">KEP Adresi</h2>
              <a
                href="mailto:abdullah.alpaslan.2@hs01.kep.tr"
                className="text-sm font-medium text-purple-600 underline hover:text-purple-800"
              >
                abdullah.alpaslan.2@hs01.kep.tr
              </a>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 font-semibold text-slate-900">Web Sitesi</h2>
              <a
                href="https://www.benimmasalim.com.tr"
                className="text-sm font-medium text-purple-600 underline hover:text-purple-800"
              >
                www.benimmasalim.com.tr
              </a>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 font-semibold text-slate-900">Meslek Odası</h2>
              <p className="text-sm leading-relaxed">
                İstanbul Matbaacılar Odası
              </p>
            </div>
          </div>
        </div>

        <div className="mt-12 border-t pt-6 text-center text-sm text-slate-500">
          <a
            href="/"
            className="text-purple-600 underline hover:text-purple-800"
          >
            Ana Sayfaya Dön
          </a>
        </div>
      </main>
      <Footer />
    </div>
  );
}
