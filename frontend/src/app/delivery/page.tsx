import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";

export const metadata: Metadata = {
  title: "Teslimat ve İade Şartları | Benim Masalım",
  description:
    "Benim Masalım teslimat süreleri, kargo bilgileri ve iade koşulları hakkında detaylı bilgi.",
};

export default function DeliveryPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-3xl flex-1 px-4 py-12 text-slate-700">
        <h1 className="mb-8 text-3xl font-bold text-slate-900">
          Teslimat ve İade Şartları
        </h1>
      <p className="mb-4 text-sm text-slate-500">
        Son güncelleme: 17 Şubat 2026
      </p>

      <section className="space-y-6 leading-relaxed">
        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            1. Teslimat Süresi
          </h2>
          <p>
            Siparişiniz ödeme onayının ardından üretim sürecine alınır. Kişiye
            özel kitap üretimi ve teslimat süreci aşağıdaki şekildedir:
          </p>
          <ul className="ml-6 mt-2 list-disc space-y-1">
            <li>
              <strong>Üretim süresi:</strong> Ödeme onayından itibaren 3-5 iş
              günü
            </li>
            <li>
              <strong>Kargo süresi:</strong> Üretim tamamlandıktan sonra 1-3 iş
              günü
            </li>
            <li>
              <strong>Toplam tahmini süre:</strong> 4-8 iş günü
            </li>
          </ul>
          <p className="mt-2 text-sm text-slate-500">
            Yoğun dönemlerde (bayram, özel günler vb.) teslimat süreleri
            uzayabilir. Bu durumda e-posta ile bilgilendirilirsiniz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            2. Teslimat Yöntemi ve Bölgesi
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>Teslimat, anlaşmalı kargo firmaları aracılığıyla yapılır</li>
            <li>Türkiye genelinde tüm il ve ilçelere teslimat yapılmaktadır</li>
            <li>
              Kargo takip numarası, sipariş gönderildikten sonra e-posta ile
              iletilir
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            3. Kargo Ücreti
          </h2>
          <p>
            Kargo ücreti sipariş sırasında toplam tutara dahil olarak
            gösterilir. Kampanya dönemlerinde ücretsiz kargo fırsatları
            sunulabilir.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            4. Teslimat Sırasında Dikkat Edilecekler
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              Paketinizi teslim alırken dış ambalajı kontrol ediniz
            </li>
            <li>
              Hasar görmüş paketler için kargo görevlisi huzurunda tutanak
              tutturunuz
            </li>
            <li>
              Hasarlı teslimat durumunda{" "}
              <a
                href="mailto:info@benimmasalim.com.tr"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                info@benimmasalim.com.tr
              </a>{" "}
              adresine fotoğraflı olarak bildirimde bulununuz
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            5. İade ve Cayma Hakkı
          </h2>
          <p>
            Benim Masalım ürünleri, her müşteri için özel olarak üretilen
            kişiselleştirilmiş ürünlerdir. 6502 sayılı Tüketicinin Korunması
            Hakkında Kanun&apos;un 15/ğ maddesi gereğince,{" "}
            <strong>
              tüketicinin istekleri veya açıkça kişisel ihtiyaçları
              doğrultusunda hazırlanan ürünlerde cayma hakkı kullanılamaz.
            </strong>
          </p>
          <p className="mt-2">Ancak aşağıdaki durumlarda destek sağlarız:</p>
          <ul className="ml-6 mt-2 list-disc space-y-1">
            <li>
              <strong>Üretim hatası:</strong> Baskı kalitesi, sayfa eksikliği
              veya cilt hatası durumunda kitabınız ücretsiz olarak yeniden
              basılır
            </li>
            <li>
              <strong>Kargo hasarı:</strong> Taşıma sırasında hasar gören
              kitaplar için ücretsiz yeniden gönderim sağlanır
            </li>
            <li>
              <strong>Yanlış içerik:</strong> Sipariş bilgilerinizle uyuşmayan
              bir kitap teslim edilmesi durumunda yeniden üretim yapılır
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            6. Sipariş İptali ve Para İadesi
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              Üretim sürecine alınmamış siparişler için iptal talebi
              yapılabilir. İptal durumunda ödemenizin <strong>tamamı</strong> iade edilir.
            </li>
            <li>
              Üretim sürecine alınmış siparişlerde iptal mümkün değildir.
            </li>
            <li>
              İptal talepleri için{" "}
              <a
                href="mailto:info@benimmasalim.com.tr"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                info@benimmasalim.com.tr
              </a>{" "}
              adresinden en kısa sürede iletişime geçiniz.
            </li>
          </ul>

          <h3 className="mb-1 mt-4 font-semibold text-slate-700">
            Para İadesi Koşulları
          </h3>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              <strong>Üretim öncesi iptal:</strong> Ödeme tutarının tamamı,
              talebin tarafımıza ulaşmasından itibaren en geç{" "}
              <strong>3 iş günü</strong> içinde iade edilir.
            </li>
            <li>
              <strong>Üretim hatası / kargo hasarı / yanlış içerik:</strong>{" "}
              Müşterinin tercihine göre ürün ücretsiz yeniden üretilir veya
              ödeme tutarının tamamı iade edilir. Para iadesi talebinin
              onaylanmasından itibaren en geç <strong>7 iş günü</strong>{" "}
              içinde gerçekleştirilir.
            </li>
            <li>
              <strong>İade yöntemi:</strong> Kredi kartı ile yapılan ödemelerde
              iade, ödemenin yapıldığı kredi kartına; banka kartı ile yapılan
              ödemelerde ise ilgili banka hesabına aktarılır. İade süresi
              bankanıza bağlı olarak değişebilir.
            </li>
            <li>
              Tüm iade işlemleri iyzico güvenli ödeme altyapısı üzerinden
              gerçekleştirilir.
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            7. İade Süreci
          </h2>
          <p>
            Üretim hatası veya kargo hasarı nedeniyle iade/değişim talebi
            oluşturmak için:
          </p>
          <ol className="ml-6 mt-2 list-decimal space-y-1">
            <li>
              <a
                href="mailto:info@benimmasalim.com.tr"
                className="font-medium text-purple-600 underline hover:text-purple-800"
              >
                info@benimmasalim.com.tr
              </a>{" "}
              adresine sipariş numaranız ve sorunu gösteren fotoğraflarla
              birlikte başvurun
            </li>
            <li>Talebiniz en geç 48 saat içinde değerlendirilir</li>
            <li>
              Onaylanan talepler için yeniden üretim veya para iadesi süreci başlatılır
            </li>
            <li>
              Para iadesi tercih edilmesi halinde, iade tutarı yukarıda belirtilen
              sürelerde ödeme yönteminize göre hesabınıza aktarılır
            </li>
          </ol>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            8. Genel Bilgiler
          </h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>
              Tüm fiyatlar <strong>KDV dahil Türk Lirası (TL)</strong>{" "}
              cinsindendir.
            </li>
            <li>
              Hizmetlerimiz yalnızca <strong>Türkiye</strong> sınırları
              içindeki adreslere teslimat kapsamındadır.
            </li>
            <li>
              Sipariş verebilmek için <strong>18 yaşından büyük</strong> olmanız
              veya yasal vasinin onayı gerekmektedir.
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">
            9. İletişim
          </h2>
          <p>
            Teslimat ve iade süreçleri hakkında sorularınız için{" "}
            <a
              href="mailto:info@benimmasalim.com.tr"
              className="font-medium text-purple-600 underline hover:text-purple-800"
            >
              info@benimmasalim.com.tr
            </a>{" "}
            adresinden bize ulaşabilirsiniz.
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
