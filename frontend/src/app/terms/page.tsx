import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";

export const metadata: Metadata = {
  title: "Kullanım Şartları",
  description: "Benim Masalım Kullanım Şartları — Hizmetlerimizi kullanma koşulları.",
};

export default function TermsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-3xl flex-1 px-4 py-12 text-slate-700">
      <h1 className="mb-8 text-3xl font-bold text-slate-900">
        Kullanım Şartları
      </h1>
      <p className="mb-4 text-sm text-slate-500">
        Son güncelleme: 14 Şubat 2026
      </p>

      <section className="space-y-6 leading-relaxed">
        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">1. Genel</h2>
          <p>
            Bu kullanım şartları, www.benimmasalim.com.tr web sitesi ve Benim Masalım hizmetlerinin
            kullanımına ilişkin koşulları düzenlemektedir. Hizmetlerimizi kullanarak bu
            şartları kabul etmiş sayılırsınız.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">2. Hizmet Tanımı</h2>
          <p>
            Benim Masalım, yapay zeka teknolojisi kullanarak çocuklara özel kişiselleştirilmiş
            masal kitapları oluşturan bir platformdur. Hizmetimiz:
          </p>
          <ul className="ml-6 list-disc space-y-1">
            <li>Çocuğun adı, yaşı ve fotoğrafıyla kişiselleştirilmiş hikaye metni üretimi</li>
            <li>Yapay zeka ile çocuğa benzeyen görseller oluşturma</li>
            <li>Basılı kitap üretimi ve teslimatı</li>
            <li>İsteğe bağlı sesli kitap özelliği</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">3. Sipariş ve Ödeme</h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>Siparişler, ödeme onayı alındıktan sonra işleme alınır</li>
            <li>Ödeme işlemleri güvenli ödeme altyapısı üzerinden gerçekleştirilir</li>
            <li>Fiyatlar web sitesinde belirtildiği şekildedir ve KDV dahildir</li>
            <li>Sipariş verildikten sonra kişiselleştirilmiş içerik üretildiğinden, iade koşulları aşağıda belirtilmiştir</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">4. İade ve İptal</h2>
          <p>
            Kişiye özel üretilen kitaplar 6502 sayılı Tüketicinin Korunması Hakkında Kanun&apos;un
            15/ğ maddesi gereğince cayma hakkı kapsamı dışındadır. Ancak:
          </p>
          <ul className="ml-6 list-disc space-y-1">
            <li>Üretim hatası durumunda ücretsiz yeniden basım yapılır</li>
            <li>Kargo hasarı durumunda yeniden gönderim sağlanır</li>
            <li>Üretim öncesi iptal talepleri değerlendirilir</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">5. Fikri Mülkiyet</h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>Oluşturulan hikaye metinleri ve görseller yapay zeka tarafından üretilmiştir</li>
            <li>Sipariş veren kişi, üretilen kitabı kişisel kullanım amacıyla kullanabilir</li>
            <li>Kitap içeriğinin ticari amaçlarla çoğaltılması ve dağıtılması yasaktır</li>
            <li>Web sitesinin tasarımı, logosu ve altyapısı Benim Masalım&apos;a aittir</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">6. Kullanıcı Sorumlulukları</h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>Doğru ve güncel bilgi sağlamak</li>
            <li>Yalnızca yasal haklarına sahip olduğu fotoğrafları yüklemek</li>
            <li>Çocuk fotoğrafı yüklenmesi halinde yasal veli/vasi onayına sahip olmak</li>
            <li>Hizmeti kötüye kullanmamak</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">7. Yapay Zeka Kullanımı</h2>
          <p>
            Hizmetimizde yapay zeka teknolojisi kullanılmaktadır. Yapay zeka ile üretilen
            içeriklerin kalitesi değişkenlik gösterebilir. Oluşturulan hikaye ve görseller
            üretim öncesinde onayınıza sunulur.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">8. Kişisel Verilerin Korunması</h2>
          <p>
            Kişisel verilerinizin korunması hakkında detaylı bilgi için{" "}
            <a href="/kvkk" className="font-medium text-purple-600 underline hover:text-purple-800">KVKK Aydınlatma Metni</a>{" "}
            ve{" "}
            <a href="/privacy" className="font-medium text-purple-600 underline hover:text-purple-800">Gizlilik Politikası</a>{" "}
            sayfalarımızı incelemenizi rica ederiz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">9. Sorumluluk Sınırı</h2>
          <p>
            Benim Masalım, mücbir sebepler (doğal afet, teknik altyapı sorunları, üçüncü
            taraf hizmet kesintileri vb.) nedeniyle hizmetin gecikmesinden veya
            aksamasından dolayı sorumlu tutulamaz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">10. Uyuşmazlık Çözümü</h2>
          <p>
            Bu şartlardan doğan uyuşmazlıklarda Türkiye Cumhuriyeti kanunları uygulanır.
            Uyuşmazlıkların çözümünde İstanbul Mahkemeleri ve İcra Daireleri yetkilidir.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">11. İletişim</h2>
          <p>
            Kullanım şartları hakkında sorularınız için{" "}
            <a href="mailto:info@benimmasalim.com.tr" className="font-medium text-purple-600 underline hover:text-purple-800">
              info@benimmasalim.com.tr
            </a>{" "}
            adresinden bize ulaşabilirsiniz.
          </p>
        </div>
      </section>

      <div className="mt-12 border-t pt-6 text-center text-sm text-slate-500">
        <a href="/" className="text-purple-600 hover:text-purple-800 underline">
          Ana Sayfaya Dön
        </a>
      </div>
      </main>
      <Footer />
    </div>
  );
}
