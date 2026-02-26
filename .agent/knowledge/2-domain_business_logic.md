# "Benim Masalım" İş Mantığı (Domain Logic)

## 1. Ürün Çeşitliliği
Sistem çocukların kişisel özelliklerine (ad, saç rengi, arkadaş, sevdiği oyuncak vs.) göre özel içerikler üretir. İki temel ürün vardır:
- **Kişiselleştirilmiş Masal Kitapları**: Metinleri ve sahneleri Gemini ve Imagen 3 motorlarıyla çocuğa özel oluşturulur.
- **Boyama Kitapları**: Hikayeden bağımsız veya hikayeye bağlı, sipariş edilen senaryoya özel siyah-beyaz line-art (çizgi film tarzı) boyama resimleridir.

## 2. Order State Machine (Sipariş Durumları)
Bir sipariş platformda ilerlerken belirli bir yaşam döngüsüne (State Machine) sahiptir. Manuel durum değiştirme (`status = "COMPLETED"`) projenin güvenliği için yasaktır. Her zaman `transition_order()` metodunu kullanın.

### Durum Akışı
1. `PENDING`: Müşteri siparişi oluşturdu ancak ödeme yapmadı.
2. `PAID`: Ödeme Iyzico veya benzeri bir entegrasyondan başarıyla alındı.
3. `CONFIRMED`: Sipariş onaylandı ve AI (kuyruk) işlemleri başlamayı bekliyor.
4. `PROCESSING`: ARQ Workers tarafından yapay zeka işlemleri (masal metni ya da resim) şuan üretiliyor.
5. `COMPLETED`: Tüm ürünler tamamen üretildi ve PDF'ler S3 (veya GCP Bucket) tarzı bulut deposunda hazır.
6. `CANCELLED`: Siparişte (ödeme, üretim vb.) geri dönüşü olmayan bir hata yaşandı (örn: prompt injection) ve sipariş iptal edildi.
7. `REFUNDED`: Sipariş parası müşteriye geri iade edildi.

## 3. Güvenlik ve Uyumluluk
- **Çocuk Güvenliği (Child Safety)**: Üretilen her masal ve görsel, yaş kısıtlarına ve şiddet/kötü örnek teşkil edecek materyallere karşı tam kısıtlama altındadır. AI promptlarında her zaman negatif child-safety filtreleri uygulanır.
- **KVKK ve Veri Gizliliği**: Kullanıcıya ait sipariş (çocuk ismi vs.) silindiğinde veya sansürlenmesi gerektiğinde Audit Log mekanizmaları işletilir. Loglar asla kullanıcının tam ismini clear-text tutmamalıdır (şifreleme/maskeleme uygulanır).
