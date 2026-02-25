"use client";

import { useState } from "react";
import { ShieldCheck, Send, CheckCircle } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";

type RequestType = "ACCESS" | "EXPORT" | "DELETION" | "CORRECTION";

const REQUEST_TYPES: { value: RequestType; label: string; desc: string }[] = [
  { value: "ACCESS", label: "Veri Erişim", desc: "Hangi verilerimin işlendiğini öğrenmek istiyorum" },
  { value: "EXPORT", label: "Veri Aktarımı", desc: "Verilerimin bir kopyasını almak istiyorum" },
  { value: "DELETION", label: "Veri Silme", desc: "Verilerimin silinmesini / yok edilmesini istiyorum" },
  { value: "CORRECTION", label: "Veri Düzeltme", desc: "Verilerimin düzeltilmesini istiyorum" },
];

export default function DataRequestPage() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [requestType, setRequestType] = useState<RequestType>("ACCESS");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch(`${API_BASE_URL}/data-request/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          full_name: fullName,
          request_type: requestType,
          description: description || null,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Bir hata oluştu");
      }

      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Beklenmeyen bir hata oluştu");
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="mx-auto flex min-h-[60vh] max-w-lg flex-1 items-center justify-center px-4 py-12">
        <div className="rounded-2xl border border-green-200 bg-green-50 p-8 text-center">
          <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-600" />
          <h2 className="mb-2 text-xl font-bold text-green-800">Talebiniz Alındı</h2>
          <p className="text-sm text-green-700">
            KVKK kapsamındaki talebiniz kayıt altına alınmıştır. En geç <strong>30 gün</strong> içinde{" "}
            <strong>{email}</strong> adresine yanıt verilecektir.
          </p>
          <a
            href="/"
            className="mt-6 inline-block rounded-lg bg-purple-600 px-6 py-2 text-sm font-medium text-white hover:bg-purple-700"
          >
            Ana Sayfaya Dön
          </a>
        </div>
      </main>
      <Footer />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-lg flex-1 px-4 py-12">
        <div className="mb-8 text-center">
        <ShieldCheck className="mx-auto mb-3 h-10 w-10 text-purple-600" />
        <h1 className="text-2xl font-bold text-slate-900">KVKK Veri Talebi</h1>
        <p className="mt-2 text-sm text-slate-500">
          6698 sayılı KVKK kapsamındaki haklarınızı kullanmak için aşağıdaki formu doldurun.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Full Name */}
        <div>
          <label htmlFor="fullName" className="mb-1 block text-sm font-medium text-slate-700">
            Ad Soyad <span className="text-red-500">*</span>
          </label>
          <input
            id="fullName"
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            placeholder="Adınız ve soyadınız"
          />
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
            E-posta Adresi <span className="text-red-500">*</span>
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            placeholder="ornek@email.com"
          />
        </div>

        {/* Request Type */}
        <fieldset>
          <legend className="mb-2 block text-sm font-medium text-slate-700">
            Talep Türü <span className="text-red-500">*</span>
          </legend>
          <div className="space-y-2">
            {REQUEST_TYPES.map((rt) => (
              <label
                key={rt.value}
                className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                  requestType === rt.value
                    ? "border-purple-400 bg-purple-50"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="requestType"
                  value={rt.value}
                  checked={requestType === rt.value}
                  onChange={(e) => setRequestType(e.target.value as RequestType)}
                  className="mt-0.5 accent-purple-600"
                />
                <span>
                  <span className="text-sm font-medium text-slate-800">{rt.label}</span>
                  <span className="block text-xs text-slate-500">{rt.desc}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        {/* Description */}
        <div>
          <label htmlFor="description" className="mb-1 block text-sm font-medium text-slate-700">
            Açıklama <span className="text-slate-400">(opsiyonel)</span>
          </label>
          <textarea
            id="description"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            placeholder="Talebinizle ilgili ek bilgi..."
          />
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !email || !fullName}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-purple-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {submitting ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Gönderiliyor...
            </>
          ) : (
            <>
              <Send className="h-4 w-4" />
              Talep Gönder
            </>
          )}
        </button>

        <p className="text-center text-xs text-slate-400">
          Talebiniz KVKK kapsamında en geç 30 gün içerisinde yanıtlanacaktır.{" "}
          <a href="/kvkk" className="text-purple-600 underline hover:text-purple-800">
            KVKK Aydınlatma Metni
          </a>
        </p>
      </form>
      </main>
      <Footer />
    </div>
  );
}
