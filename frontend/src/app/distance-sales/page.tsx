import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";

export const metadata: Metadata = {
  title: "Mesafeli Satış Sözleşmesi | Benim Masalım",
  description:
    "Benim Masalım Mesafeli Satış Sözleşmesi — 6502 sayılı Tüketicinin Korunması Hakkında Kanun kapsamında.",
};

export default function DistanceSalesPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-3xl flex-1 px-4 py-12 text-slate-700">
        <h1 className="mb-8 text-3xl font-bold text-slate-900">
          Mesafeli Satış Sözleşmesi
        </h1>
      <p className="mb-4 text-sm text-slate-500">
        Son güncelleme: 17 Şubat 2026
      </p>

      <section className="space-y-6 leading-relaxed">
        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 1 — Taraflar
          </h2>
          <h3 className="mb-1 mt-3 font-semibold text-slate-700">
            1.1. Satıcı Bilgileri
          </h3>
          <ul className="ml-6 list-disc space-y-1">
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
              <strong>Meslek Odası:</strong> İstanbul Matbaacılar Odası
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

          <h3 className="mb-1 mt-3 font-semibold text-slate-700">
            1.2. Alıcı Bilgileri
          </h3>
          <p>
            Sipariş sırasında alıcı tarafından beyan edilen ad, soyad, adres,
            telefon ve e-posta bilgileri esas alınır.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 2 — Sözleşme Konusu
          </h2>
          <p>
            İşbu sözleşmenin konusu, alıcının{" "}
            <a
              href="https://www.benimmasalim.com.tr"
              className="font-medium text-purple-600 underline hover:text-purple-800"
            >
              www.benimmasalim.com.tr
            </a>{" "}
            web sitesinden elektronik ortamda siparişini verdiği, aşağıda
            nitelikleri ve satış fiyatı belirtilen ürün/ürünlerin satışı ve
            teslimi ile ilgili olarak 6502 sayılı Tüketicinin Korunması Hakkında
            Kanun ve Mesafeli Sözleşmeler Yönetmeliği hükümleri gereğince
            tarafların hak ve yükümlülüklerinin belirlenmesidir.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 3 — Sözleşme Konusu Ürün Bilgileri
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              <strong>Ürün:</strong> Yapay zeka destekli kişiselleştirilmiş
              çocuk masal kitabı
            </li>
            <li>
              <strong>Özellikler:</strong> Çocuğun adı, yaşı ve fotoğrafıyla
              kişiselleştirilmiş hikaye metni ve illüstrasyonlar; profesyonel
              baskı kalitesinde ciltli kitap
            </li>
            <li>
              <strong>Ek hizmetler:</strong> İsteğe bağlı sesli kitap özelliği
            </li>
            <li>
              Ürünün temel özellikleri, fiyatı (KDV dahil) ve ödeme bilgileri
              sipariş onay sayfasında gösterilmektedir
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 4 — Genel Hükümler
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              Alıcı, sözleşme konusu ürünün temel nitelikleri, satış fiyatı,
              ödeme şekli ve teslimata ilişkin ön bilgileri okuyup bilgi sahibi
              olduğunu ve elektronik ortamda gerekli onayı verdiğini kabul ve
              beyan eder.
            </li>
            <li>
              Alıcı, bu sözleşmeyi elektronik ortamda onaylayarak, mesafeli
              sözleşmelerin akdinden önce satıcı tarafından verilmesi gereken
              bilgilerin tamamını doğru ve eksiksiz olarak edindiğini teyit eder.
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 5 — Ödeme Şekli
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              Ödeme, iyzico güvenli ödeme altyapısı üzerinden kredi kartı /
              banka kartı ile yapılır
            </li>
            <li>
              Visa, Mastercard ve Troy kartları kabul edilmektedir
            </li>
            <li>
              Kredi kartı bilgileri satıcının sunucularında saklanmaz; tüm ödeme
              işlemleri PCI DSS uyumlu iyzico altyapısı tarafından
              gerçekleştirilir
            </li>
            <li>
              Tüm fiyatlar KDV dahil Türk Lirası (TL) cinsindendir
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 6 — Teslimat Koşulları
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              Ürün, alıcının sipariş formunda belirttiği teslimat adresine
              teslim edilir
            </li>
            <li>
              Tahmini teslimat süresi, ödeme onayından itibaren 4-8 iş günüdür
              (üretim + kargo)
            </li>
            <li>
              Teslimat, anlaşmalı kargo firması aracılığıyla yapılır
            </li>
            <li>
              Mücbir sebep hallerinde (doğal afet, pandemi, olağanüstü hal vb.)
              teslimat süreleri uzayabilir; satıcı bu durumdan sorumlu
              tutulamaz
            </li>
            <li>
              Kargo takip bilgisi, gönderim sonrası alıcının e-posta adresine
              iletilir
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 7 — Cayma Hakkı
          </h2>
          <p>
            Alıcı, 6502 sayılı Tüketicinin Korunması Hakkında Kanun&apos;un 15.
            maddesi ve Mesafeli Sözleşmeler Yönetmeliği&apos;nin 15/ğ maddesi
            gereğince,{" "}
            <strong>
              tüketicinin istekleri veya açıkça kişisel ihtiyaçları
              doğrultusunda hazırlanan mallarda cayma hakkının kullanılamayacağını
            </strong>{" "}
            kabul ve beyan eder.
          </p>
          <p className="mt-2">
            Benim Masalım ürünleri, her müşteri için çocuğun adı, yaşı ve
            fotoğrafıyla özel olarak üretilen kişiselleştirilmiş ürünlerdir.
            Bu nedenle cayma hakkı kapsamı dışındadır.
          </p>
          <p className="mt-2">
            Ancak üretim hatası, kargo hasarı veya sipariş bilgileriyle
            uyuşmayan ürün teslimi durumlarında satıcı, ürünün ücretsiz olarak
            yeniden üretilmesini veya para iadesi sürecini başlatır.
          </p>
          <p className="mt-2">
            <strong>Para İadesi:</strong> Üretim öncesi iptal durumunda ödeme
            tutarının tamamı en geç 3 iş günü içinde; üretim hatası, kargo hasarı
            veya yanlış içerik durumunda ise müşterinin tercihine göre ödeme tutarı
            en geç 7 iş günü içinde, ödemenin yapıldığı kredi kartına veya banka
            hesabına iade edilir. Tüm iade işlemleri iyzico güvenli ödeme altyapısı
            üzerinden gerçekleştirilir. Detaylı bilgi için{" "}
            <a
              href="/delivery"
              className="font-medium text-purple-600 underline hover:text-purple-800"
            >
              Teslimat ve İade Şartları
            </a>{" "}
            sayfasını inceleyiniz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 8 — Kişisel Verilerin Korunması
          </h2>
          <p>
            Alıcının kişisel verileri, 6698 sayılı Kişisel Verilerin Korunması
            Kanunu (KVKK) kapsamında işlenir ve korunur. Detaylı bilgi için{" "}
            <a
              href="/kvkk"
              className="font-medium text-purple-600 underline hover:text-purple-800"
            >
              KVKK Aydınlatma Metni
            </a>{" "}
            ve{" "}
            <a
              href="/privacy"
              className="font-medium text-purple-600 underline hover:text-purple-800"
            >
              Gizlilik Politikası
            </a>{" "}
            sayfalarını inceleyiniz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 9 — Uyuşmazlık Çözümü
          </h2>
          <p>
            İşbu sözleşmeden doğan uyuşmazlıklarda Türkiye Cumhuriyeti kanunları
            uygulanır. Uyuşmazlıkların çözümünde Gümrük ve Ticaret Bakanlığı
            tarafından ilan edilen değere kadar Tüketici Hakem Heyetleri, bu
            değerin üzerindeki uyuşmazlıklarda ise Tüketici Mahkemeleri
            yetkilidir. İstanbul Mahkemeleri ve İcra Daireleri yetkilidir.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            Madde 10 — Yürürlük
          </h2>
          <p>
            Alıcı, sipariş onayı ile birlikte işbu sözleşmenin tüm koşullarını
            kabul etmiş sayılır. Satıcı, siparişin gerçekleşmesi öncesinde işbu
            sözleşmenin sitede alıcı tarafından okunup kabul edildiğine dair
            onay alır.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            İletişim
          </h2>
          <p>
            Sözleşme hakkında sorularınız için{" "}
            <a
              href="mailto:info@benimmasalim.com.tr"
              className="font-medium text-purple-600 underline hover:text-purple-800"
            >
              info@benimmasalim.com.tr
            </a>{" "}
            adresinden veya{" "}
            <a
              href="tel:+905333239242"
              className="font-medium text-purple-600 underline hover:text-purple-800"
            >
              0533 323 92 42
            </a>{" "}
            numarasından bize ulaşabilirsiniz.
          </p>
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
