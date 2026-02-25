import type { Metadata } from "next";
import Header from "@/components/landing/Header";
import Footer from "@/components/landing/Footer";

export const metadata: Metadata = {
  title: "KVKK Aydınlatma Metni",
  description: "Benim Masalım KVKK Aydınlatma Metni — Kişisel verilerin korunması hakkında bilgilendirme.",
};

export default function KVKKPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto max-w-3xl flex-1 px-4 py-12 text-slate-700">
      <h1 className="mb-8 text-3xl font-bold text-slate-900">
        KVKK Aydınlatma Metni
      </h1>
      <p className="mb-4 text-sm text-slate-500">
        Son güncelleme: 14 Şubat 2026
      </p>

      <section className="space-y-6 leading-relaxed">
        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">1. Veri Sorumlusu</h2>
          <p>
            6698 sayılı Kişisel Verilerin Korunması Kanunu (&quot;KVKK&quot;) kapsamında,
            kişisel verileriniz veri sorumlusu sıfatıyla aşağıda bilgileri yer alan
            gerçek kişi tarafından işlenmektedir.
          </p>
          <ul className="ml-6 mt-2 list-disc space-y-1">
            <li><strong>Ad Soyad:</strong> Abdullah Alpaslan</li>
            <li><strong>İşletme Adı:</strong> Benim Masalım</li>
            <li><strong>Vergi Dairesi / VKN:</strong> İkitelli / 16106557652</li>
            <li><strong>Adres:</strong> İkitelli OSB Mah. Heskoop M2 Blok Sk. Heskoop M2 Blok No: 20 Başakşehir / İstanbul</li>
            <li><strong>KEP Adresi:</strong>{" "}
              <a href="mailto:abdullah.alpaslan.2@hs01.kep.tr" className="font-medium text-purple-600 underline hover:text-purple-800">
                abdullah.alpaslan.2@hs01.kep.tr
              </a>
            </li>
            <li><strong>E-posta:</strong>{" "}
              <a href="mailto:info@benimmasalim.com.tr" className="font-medium text-purple-600 underline hover:text-purple-800">
                info@benimmasalim.com.tr
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">2. İşlenen Kişisel Veriler</h2>
          <p className="mb-2">Hizmetlerimizi sunabilmek için aşağıdaki kişisel verileri işlemekteyiz:</p>
          <ul className="ml-6 list-disc space-y-1">
            <li><strong>Kimlik bilgileri:</strong> Ad, soyad</li>
            <li><strong>İletişim bilgileri:</strong> E-posta adresi, telefon numarası</li>
            <li><strong>Çocuk bilgileri:</strong> Çocuğun adı, yaşı, cinsiyeti</li>
            <li><strong>Görsel veriler:</strong> Çocuk fotoğrafı (yapay zeka ile hikaye kitabı oluşturmak amacıyla)</li>
            <li><strong>Ses verileri:</strong> Sesli kitap için ses kaydı (isteğe bağlı)</li>
            <li><strong>Adres bilgileri:</strong> Teslimat adresi</li>
            <li><strong>Ödeme bilgileri:</strong> Ödeme işlem bilgileri (kredi kartı bilgileri tarafımızca saklanmaz, ödeme altyapı sağlayıcısı tarafından işlenir)</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">3. Kişisel Verilerin İşlenme Amaçları</h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>Kişiye özel çocuk kitabı oluşturulması</li>
            <li>Yapay zeka ile hikaye ve görsel üretimi</li>
            <li>Sipariş ve teslimat süreçlerinin yürütülmesi</li>
            <li>Müşteri iletişimi ve destek hizmetleri</li>
            <li>Yasal yükümlülüklerin yerine getirilmesi</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">4. Fotoğraf ve Ses Verilerinin İşlenmesi</h2>
          <p>
            Yüklediğiniz çocuk fotoğrafları yalnızca hikaye kitabı oluşturma amacıyla yapay zeka
            tarafından işlenir. <strong>Fotoğraflar, siparişin teslim edilmesinden 30 gün sonra
            otomatik olarak sunucularımızdan kalıcı şekilde silinir.</strong>
          </p>
          <p className="mt-2">
            Sesli kitap için gönderilen ses kayıtları aynı süre içerisinde silinir.
            Sistem sesleri (önceden tanımlı sesler) kişisel veri içermez ve bu kapsam dışındadır.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">5. Kişisel Verilerin Aktarımı</h2>
          <p>Kişisel verileriniz aşağıdaki taraflarla paylaşılabilir:</p>
          <ul className="ml-6 list-disc space-y-1">
            <li>Yapay zeka hizmet sağlayıcıları (Google Gemini — hikaye üretimi, Fal.ai — görsel üretimi)</li>
            <li>Bulut depolama hizmetleri (Google Cloud Storage)</li>
            <li>Ödeme altyapı sağlayıcısı (iyzico)</li>
            <li>Kargo ve teslimat firmaları</li>
            <li>Yasal zorunluluk halinde yetkili kamu kurum ve kuruluşları</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">6. Veri Saklama Süreleri</h2>
          <ul className="ml-6 list-disc space-y-1">
            <li><strong>Fotoğraflar:</strong> Teslimattan itibaren 30 gün</li>
            <li><strong>Ses kayıtları (klonlanmış):</strong> Teslimattan itibaren 30 gün</li>
            <li><strong>Sipariş bilgileri:</strong> Yasal saklama süresi boyunca (ticari defterler için 10 yıl)</li>
            <li><strong>İletişim bilgileri:</strong> Hesap aktif olduğu sürece</li>
            <li><strong>Geçici dosyalar:</strong> 24 saat içinde otomatik silinir</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">7. KVKK Kapsamındaki Haklarınız</h2>
          <p className="mb-2">KVKK&apos;nın 11. maddesi gereğince aşağıdaki haklara sahipsiniz:</p>
          <ul className="ml-6 list-disc space-y-1">
            <li>Kişisel verilerinizin işlenip işlenmediğini öğrenme</li>
            <li>Kişisel verileriniz işlenmişse buna ilişkin bilgi talep etme</li>
            <li>Kişisel verilerinizin işlenme amacını ve bunların amacına uygun kullanılıp kullanılmadığını öğrenme</li>
            <li>Yurt içinde veya yurt dışında kişisel verilerin aktarıldığı üçüncü kişileri bilme</li>
            <li>Kişisel verilerin eksik veya yanlış işlenmişse düzeltilmesini isteme</li>
            <li>KVKK&apos;nın 7. maddesi kapsamında kişisel verilerin silinmesini veya yok edilmesini isteme</li>
            <li>Düzeltme ve silme işlemlerinin verilerin aktarıldığı üçüncü kişilere bildirilmesini isteme</li>
            <li>İşlenen verilerin münhasıran otomatik sistemler vasıtasıyla analiz edilmesi suretiyle aleyhinize bir sonuç ortaya çıkmasına itiraz etme</li>
            <li>Kişisel verilerin kanuna aykırı olarak işlenmesi sebebiyle zarara uğramanız halinde zararın giderilmesini talep etme</li>
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">8. Başvuru Yöntemi</h2>
          <p>
            Yukarıda sayılan haklarınıza ilişkin taleplerinizi{" "}
            <a href="/data-request" className="font-medium text-purple-600 underline hover:text-purple-800">
              Veri Talebi Formu
            </a>{" "}
            üzerinden veya{" "}
            <a href="mailto:info@benimmasalim.com.tr" className="font-medium text-purple-600 underline hover:text-purple-800">
              info@benimmasalim.com.tr
            </a>{" "}
            adresine e-posta göndererek iletebilirsiniz.
            Başvurularınız en geç 30 gün içerisinde yanıtlanacaktır.
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-xl font-semibold text-slate-800">9. Güvenlik Önlemleri</h2>
          <ul className="ml-6 list-disc space-y-1">
            <li>Tüm veri iletişimi SSL/TLS şifrelemesi ile korunmaktadır</li>
            <li>Fotoğraflardan EXIF meta verileri (GPS, kamera bilgisi) yükleme sırasında otomatik olarak temizlenir</li>
            <li>Veriler Google Cloud Platform üzerinde Avrupa (europe-west1) bölgesinde saklanmaktadır</li>
            <li>Erişim yetkilendirmesi ve denetim kayıtları (audit log) tutulmaktadır</li>
          </ul>
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
