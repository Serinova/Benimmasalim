import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";

export const metadata: Metadata = {
  title: "Gizlilik Politikası",
  description: "Benim Masalım Gizlilik Politikası — Kişisel verilerinizin nasıl toplandığı, kullanıldığı ve korunduğu hakkında bilgi.",
};

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-3xl flex-1 px-4 py-12 text-slate-700">
      <h1 className="mb-8 text-3xl font-bold text-slate-900">
        Gizlilik Politikası
      </h1>
      <p className="mb-4 text-sm text-slate-500">
        Son güncelleme: 14 Şubat 2026
      </p>

      <section className="space-y-6 leading-relaxed">
        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">1. Genel Bakış</h2>
          <p>
            Benim Masalım olarak gizliliğinize saygı duyuyoruz. Bu politika, web sitemizi ve
            hizmetlerimizi kullanırken kişisel verilerinizin nasıl toplandığını, kullanıldığını,
            saklandığını ve korunduğunu açıklamaktadır.
          </p>
          <ul className="ml-6 mt-2 list-disc space-y-1 text-sm">
            <li><strong>Veri Sorumlusu:</strong> Abdullah Alpaslan — Benim Masalım</li>
            <li><strong>Adres:</strong> İkitelli OSB Mah. Heskoop M2 Blok Sk. Heskoop M2 Blok No: 20 Başakşehir / İstanbul</li>
            <li><strong>E-posta:</strong>{" "}
              <a href="mailto:info@benimmasalim.com.tr" className="font-medium text-purple-600 underline hover:text-purple-800">
                info@benimmasalim.com.tr
              </a>
            </li>
            <li><strong>KEP:</strong>{" "}
              <a href="mailto:abdullah.alpaslan.2@hs01.kep.tr" className="font-medium text-purple-600 underline hover:text-purple-800">
                abdullah.alpaslan.2@hs01.kep.tr
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">2. Toplanan Bilgiler</h2>
          <h3 className="mb-1 mt-3 font-semibold text-slate-700">2.1. Doğrudan sağladığınız bilgiler</h3>
          <ul className="ml-6 list-disc space-y-1">
            <li>Sipariş oluşturma sırasında: ad, soyad, e-posta, telefon, teslimat adresi</li>
            <li>Çocuk bilgileri: ad, yaş, cinsiyet, fotoğraf</li>
            <li>İsteğe bağlı ses kaydı (sesli kitap için)</li>
          </ul>

          <h3 className="mb-1 mt-3 font-semibold text-slate-700">2.2. Otomatik toplanan bilgiler</h3>
          <ul className="ml-6 list-disc space-y-1">
            <li>Tarayıcı türü ve sürümü</li>
            <li>IP adresi (güvenlik ve kötüye kullanım önleme amacıyla)</li>
            <li>Sayfa görüntüleme ve etkileşim verileri</li>
          </ul>

          <h3 className="mb-1 mt-3 font-semibold text-slate-700">2.3. Yerel depolama (localStorage)</h3>
          <p>
            Tarayıcınızda oturum bilgileri ve sipariş sürecinin devamlılığı için yerel depolama
            kullanılmaktadır. Bu veriler yalnızca tarayıcınızda saklanır ve sunucularımıza aktarılmaz.
            Tarayıcı ayarlarınızdan yerel depolamayı temizleyebilirsiniz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">3. Bilgilerin Kullanımı</h2>
          <p>Topladığımız bilgileri şu amaçlarla kullanıyoruz:</p>
          <ul className="ml-6 list-disc space-y-1">
            <li>Kişiye özel çocuk kitabı oluşturma ve üretme</li>
            <li>Sipariş ve teslimat süreçlerini yönetme</li>
            <li>Ödeme işlemlerini gerçekleştirme</li>
            <li>Müşteri destek hizmeti sunma</li>
            <li>Hizmet kalitesini iyileştirme</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">4. Çocuk Fotoğraflarının Korunması</h2>
          <p>Çocuk fotoğrafları konusunda özel hassasiyet gösteriyoruz:</p>
          <ul className="ml-6 list-disc space-y-1">
            <li>Fotoğraflar yalnızca kitap oluşturma amacıyla kullanılır</li>
            <li>Fotoğraflardan GPS ve kamera bilgileri (EXIF) otomatik olarak temizlenir</li>
            <li>Fotoğraflar sipariş tesliminden <strong>30 gün</strong> sonra kalıcı olarak silinir</li>
            <li>Yüz tanıma verileri (face embedding) fotoğraflarla birlikte silinir</li>
            <li>Fotoğraflar üçüncü taraflarla pazarlama amacıyla paylaşılmaz</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">5. Üçüncü Taraf Hizmetler</h2>
          <p>Hizmetlerimizi sunmak için aşağıdaki üçüncü taraf hizmet sağlayıcılarını kullanıyoruz:</p>
          <ul className="ml-6 list-disc space-y-1">
            <li><strong>Google Cloud Platform:</strong> Veri depolama ve sunucu altyapısı (Avrupa bölgesi)</li>
            <li><strong>Google Gemini:</strong> Yapay zeka ile hikaye metni üretimi</li>
            <li><strong>Fal.ai:</strong> Yapay zeka ile görsel üretimi</li>
            <li><strong>iyzico:</strong> Güvenli ödeme altyapısı (PCI DSS uyumlu; kredi kartı bilgileri tarafımızca saklanmaz)</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">6. Veri Güvenliği</h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>SSL/TLS şifreleme ile güvenli bağlantı</li>
            <li>Google Cloud Platform güvenlik standartları</li>
            <li>Erişim kontrolü ve yetkilendirme</li>
            <li>Denetim kayıtları (audit log)</li>
            <li>Düzenli güvenlik değerlendirmeleri</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">7. Çerezler (Cookies)</h2>
          <p>
            Web sitemiz temel işlevsellik için gerekli çerezler kullanmaktadır. Pazarlama veya
            izleme amaçlı üçüncü taraf çerezleri kullanılmamaktadır.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">8. Haklarınız</h2>
          <p>
            KVKK kapsamındaki haklarınız hakkında detaylı bilgi için{" "}
            <a href="/kvkk" className="font-medium text-purple-600 underline hover:text-purple-800">
              KVKK Aydınlatma Metni
            </a>{" "}
            sayfamızı ziyaret edebilirsiniz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">9. İletişim</h2>
          <p>
            Gizlilik politikamız hakkında sorularınız için{" "}
            <a href="mailto:info@benimmasalim.com.tr" className="font-medium text-purple-600 underline hover:text-purple-800">
              info@benimmasalim.com.tr
            </a>{" "}
            adresinden bize ulaşabilirsiniz.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">10. Değişiklikler</h2>
          <p>
            Bu gizlilik politikası zaman zaman güncellenebilir. Önemli değişiklikler
            web sitemiz üzerinden duyurulacaktır.
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
