import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";

export const metadata: Metadata = {
  title: "Hakkımızda | Benim Masalım",
  description:
    "Benim Masalım — Yapay zeka destekli kişiye özel çocuk kitabı platformu. Misyonumuz, değerlerimiz ve hikayemiz.",
};

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-3xl flex-1 px-4 py-12 text-slate-700">
        <h1 className="mb-8 text-3xl font-bold text-slate-900">Hakkımızda</h1>

      <section className="space-y-6 leading-relaxed">
        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Benim Masalım Nedir?
          </h2>
          <p>
            Benim Masalım, yapay zeka teknolojisini kullanarak çocuklara özel
            kişiselleştirilmiş masal kitapları oluşturan yenilikçi bir
            platformdur. Çocuğunuzun adı, yaşı ve fotoğrafıyla benzersiz
            hikayeler üretiyoruz. Her kitap, profesyonel baskı kalitesinde
            hazırlanarak kapınıza kadar ulaştırılır.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Misyonumuz
          </h2>
          <p>
            Her çocuğun kendi hikayesinin kahramanı olduğuna inanıyoruz.
            Misyonumuz, teknoloji ve yaratıcılığı bir araya getirerek çocuklara
            okuma sevgisi aşılamak, hayal güçlerini beslemek ve onlara özel,
            unutulmaz anılar yaratmaktır.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Ne Yapıyoruz?
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              Çocuğunuzun adı ve fotoğrafıyla kişiselleştirilmiş masal
              kitapları oluşturuyoruz
            </li>
            <li>
              Yapay zeka destekli illüstrasyonlarla çocuğunuza benzeyen
              karakterler yaratıyoruz
            </li>
            <li>
              Eğitici değerler içeren, yaşa uygun hikayeler üretiyoruz
            </li>
            <li>
              Profesyonel baskı kalitesinde, dayanıklı kitaplar hazırlıyoruz
            </li>
            <li>
              İsteğe bağlı sesli kitap seçeneği sunuyoruz
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Değerlerimiz
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              <strong>Çocuk Güvenliği:</strong> Çocuk verilerinin korunması en
              öncelikli konumuzdur. KVKK ve kişisel veri güvenliği
              standartlarına tam uyum sağlarız.
            </li>
            <li>
              <strong>Kalite:</strong> Her kitap, yüksek baskı kalitesi ve
              özenli içerikle hazırlanır.
            </li>
            <li>
              <strong>Yenilikçilik:</strong> En güncel yapay zeka
              teknolojilerini kullanarak sürekli gelişen bir platform sunarız.
            </li>
            <li>
              <strong>Güvenilirlik:</strong> Güvenli ödeme altyapısı (iyzico) ve
              SSL sertifikası ile korunan bir platform işletiriz.
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Güvenli Ödeme
          </h2>
          <p>
            Tüm ödeme işlemlerimiz iyzico güvenli ödeme altyapısı üzerinden
            gerçekleştirilmektedir. Kredi kartı bilgileriniz sunucularımızda
            saklanmaz. Visa, Mastercard ve Troy kartlarıyla güvenle ödeme
            yapabilirsiniz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Satıcı Bilgileri
          </h2>
          <ul className="ml-6 mt-2 list-disc space-y-1">
            <li>
              <strong>Ad Soyad:</strong> Abdullah Alpaslan
            </li>
            <li>
              <strong>İşletme Adı:</strong> Benim Masalım
            </li>
            <li>
              <strong>Vergi Dairesi / VKN:</strong> İkitelli / 16106557652
            </li>
            <li>
              <strong>Meslek Odası:</strong> İstanbul Matbaacılar Odası{" "}
              (<a
                href="https://www.istanbulmatbaacilar.org.tr"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >istanbulmatbaacilar.org.tr</a>)
            </li>
            <li>
              <strong>Adres:</strong> İkitelli OSB Mah. Heskoop M2 Blok Sk.
              Heskoop M2 Blok No: 20 Başakşehir / İstanbul
            </li>
            <li>
              <strong>Telefon:</strong>{" "}
              <a
                href="tel:+905333239242"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                0533 323 92 42
              </a>
            </li>
            <li>
              <strong>E-posta:</strong>{" "}
              <a
                href="mailto:info@benimmasalim.com.tr"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                info@benimmasalim.com.tr
              </a>
            </li>
            <li>
              <strong>KEP Adresi:</strong>{" "}
              <a
                href="mailto:abdullah.alpaslan.2@hs01.kep.tr"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                abdullah.alpaslan.2@hs01.kep.tr
              </a>
            </li>
            <li>
              <strong>Web sitesi:</strong>{" "}
              <a
                href="https://www.benimmasalim.com.tr"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                www.benimmasalim.com.tr
              </a>
            </li>
          </ul>
        </div>
      </section>

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
