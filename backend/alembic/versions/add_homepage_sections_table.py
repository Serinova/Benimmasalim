"""add_homepage_sections_table

Revision ID: a1b2c3d4e5f6
Revises: 045_yerebatan_fields
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "045_yerebatan_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type if not exists
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE section_type_enum AS ENUM (
                'HERO', 'TRUST_BAR', 'HOW_IT_WORKS', 'FEATURES',
                'PREVIEW', 'TESTIMONIALS', 'PRICING', 'FAQ',
                'CTA_BAND', 'FOOTER'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Create table if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS homepage_sections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            section_type section_type_enum NOT NULL UNIQUE,
            title VARCHAR(200),
            subtitle TEXT,
            is_visible BOOLEAN NOT NULL DEFAULT true,
            sort_order INTEGER NOT NULL DEFAULT 0,
            data JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_homepage_sections_type ON homepage_sections (section_type);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_homepage_sections_visible ON homepage_sections (is_visible, sort_order);
    """)

    # Seed default data (only if table is empty)
    op.execute("""
        INSERT INTO homepage_sections (id, section_type, title, subtitle, is_visible, sort_order, data)
        SELECT * FROM (VALUES
            (gen_random_uuid(), 'HERO'::section_type_enum, 'Çocuğunuzun Adıyla Yazılan Kişiye Özel Masal Kitabı', 'Yapay zeka ile çocuğunuzun fotoğrafı ve adını kullanarak tamamen özgün, eğitici değerler içeren profesyonel basılı hikaye kitapları oluşturun. Hediye çocuk kitabı için en özel seçim.', true, 0,
             '{"badge": "Yapay Zeka Destekli", "primary_cta_text": "Masalını Oluştur", "primary_cta_url": "/create", "secondary_cta_text": "Nasıl Çalışır?", "secondary_cta_url": "#nasil-calisir", "micro_trust": "Kredi kartı gerekmez • 2-3 iş günü teslimat • KVKK uyumlu"}'::jsonb),

            (gen_random_uuid(), 'TRUST_BAR'::section_type_enum, NULL, NULL, true, 1,
             '{"items": [{"icon": "Shield", "label": "KVKK Uyumlu", "description": "Veri güvenliği"}, {"icon": "Lock", "label": "Güvenli Ödeme", "description": "256-bit SSL"}, {"icon": "Truck", "label": "Hızlı Teslimat", "description": "2-3 iş günü"}, {"icon": "Star", "label": "Memnuniyet", "description": "4.9/5 puan"}]}'::jsonb),

            (gen_random_uuid(), 'HOW_IT_WORKS'::section_type_enum, 'Nasıl Çalışır?', 'Üç kolay adımda çocuğunuza özel kişiselleştirilmiş masal kitabı oluşturun.', true, 2,
             '{"steps": [{"number": "1", "icon": "UserPlus", "title": "Bilgileri Girin", "description": "Çocuğunuzun adını, fotoğrafını ve hikaye temasını seçin. Sadece birkaç dakika sürer."}, {"number": "2", "icon": "Wand2", "title": "Hikayenizi İnceleyin", "description": "Yapay zeka çocuğunuza özel benzersiz bir hikaye oluşturur. İnceleyip düzenleyebilirsiniz."}, {"number": "3", "icon": "Package", "title": "Kapınıza Gelsin!", "description": "Profesyonel baskı kalitesiyle hazırlanan kitabınız 2-3 iş günü içinde adresinize ulaşır."}]}'::jsonb),

            (gen_random_uuid(), 'FEATURES'::section_type_enum, 'Neden Benim Masalım?', 'Kişiye özel çocuk kitabı oluşturmanın en kolay ve kaliteli yolu.', true, 3,
             '{"items": [{"icon": "Sparkles", "title": "AI Kişiselleştirme", "description": "Her kitap %100 özgün. Yapay zeka çocuğunuzun adı ve özellikleriyle benzersiz hikayeler oluşturur."}, {"icon": "BookOpen", "title": "Eğitici Değerler", "description": "Özgüven, paylaşma, cesaret gibi değerleri eğlenceli hikayelerle çocuğunuza öğretin."}, {"icon": "Palette", "title": "Profesyonel Baskı", "description": "Yüksek kalite kağıt ve canlı renklerle baskı. Gerçek bir kitap deneyimi sunar."}, {"icon": "Headphones", "title": "Sesli Kitap Seçeneği", "description": "Hikayenizi sesli kitap olarak da dinleyin. Kendi sesinizle veya profesyonel seslendirme ile."}, {"icon": "Camera", "title": "Çocuğunuzun Fotoğrafıyla", "description": "Fotoğraf yükleyin, yapay zeka çocuğunuzu hikayenin kahramanı yapsın. Tam kişiselleştirilmiş masal."}, {"icon": "Fingerprint", "title": "%100 Özgün Hikaye", "description": "Hazır şablonlar değil, tamamen sıfırdan yazılan çocuğun adıyla masal. Her kitap tek ve benzersiz."}]}'::jsonb),

            (gen_random_uuid(), 'PREVIEW'::section_type_enum, 'Örnek Kitap Sayfaları', 'Her kitap benzersiz ve çocuğunuza özel olarak oluşturulur.', true, 4,
             '{"items": [{"title": "Kapak Sayfası", "description": "Çocuğunuzun adıyla kişiselleştirilmiş kapak tasarımı", "color": "from-purple-100 to-pink-100"}, {"title": "Hikaye Sayfası", "description": "Renkli illüstrasyonlarla zenginleştirilmiş sayfalar", "color": "from-blue-100 to-cyan-100"}, {"title": "Karakter Sayfası", "description": "Çocuğunuzun fotoğrafıyla oluşturulan kahraman", "color": "from-amber-100 to-orange-100"}, {"title": "Son Sayfa", "description": "Eğitici mesajla biten anlamlı bir kapanış", "color": "from-green-100 to-emerald-100"}]}'::jsonb),

            (gen_random_uuid(), 'TESTIMONIALS'::section_type_enum, 'Aileler Ne Diyor?', 'Binlerce aile çocuklarına özel hikaye kitapları ile mutlu.', true, 5,
             '{"items": [{"name": "Ayşe Y.", "badge": "Doğrulanmış Alıcı", "rating": 5, "text": "Kızımın doğum günü için sipariş verdik. Kitabı görünce gözleri parladı! Kendi adını ve fotoğrafını kitapta görmek onu çok mutlu etti."}, {"name": "Mehmet K.", "badge": "Doğrulanmış Alıcı", "rating": 5, "text": "Yeğenime hediye olarak aldım. Ailesi çok beğendi. Baskı kalitesi beklediğimden çok daha iyi. Herkese tavsiye ederim."}, {"name": "Elif D.", "badge": "Doğrulanmış Alıcı", "rating": 5, "text": "Oğlum her gece bu kitabı okumamı istiyor. Hikaye gerçekten kişiselleştirilmiş, hazır şablon değil. Çok etkileyici bir deneyim."}]}'::jsonb),

            (gen_random_uuid(), 'PRICING'::section_type_enum, 'Fiyatlandırma', 'Tek paket, eksiksiz deneyim. Ek ücret veya gizli maliyet yok.', true, 6,
             '{"package_name": "Kişiye Özel Masal Kitabı", "package_description": "Çocuğunuzun kahramanı olduğu benzersiz hikaye kitabı", "price_text": "Uygun fiyatlarla", "price_note": "Ürün formatına göre fiyat belirlenir", "cta_text": "Hemen Sipariş Ver", "cta_url": "/create", "badge_text": "En Popüler Seçim", "included": ["Kişiye özel AI hikaye oluşturma", "Çocuğunuzun fotoğrafıyla illüstrasyonlar", "Profesyonel kalite baskı", "Eğitici değerler içeriği", "Sesli kitap seçeneği", "2-3 iş günü kargo ile teslimat", "Sipariş öncesi hikaye önizleme", "KVKK uyumlu veri güvenliği"]}'::jsonb),

            (gen_random_uuid(), 'FAQ'::section_type_enum, 'Sıkça Sorulan Sorular', 'Merak ettiğiniz her şeyin yanıtı burada.', true, 7,
             '{"items": [{"question": "Kitap ne zaman teslim edilir?", "answer": "Siparişiniz onaylandıktan sonra profesyonel baskıya alınır ve 2-3 iş günü içinde kargo ile adresinize teslim edilir. Kargo takip numarası e-posta ile paylaşılır."}, {"question": "Çocuğumun fotoğrafı güvende mi?", "answer": "Evet, tamamen güvendedir. KVKK mevzuatına uygun şekilde işlenir ve fotoğraflar sipariş tamamlandıktan 30 gün sonra sunucularımızdan otomatik olarak silinir. Verileriniz üçüncü taraflarla paylaşılmaz."}, {"question": "Hangi yaş gruplarına uygun?", "answer": "Kitaplarımız 2-10 yaş arası çocuklar için tasarlanmıştır. Hikaye temaları ve dil seviyesi çocuğunuzun yaşına göre otomatik olarak uyarlanır."}, {"question": "Hikayeyi kendim düzenleyebilir miyim?", "answer": "Evet! Yapay zeka hikayeyi oluşturduktan sonra sipariş öncesinde tüm metni inceleyebilir ve dilediğiniz gibi düzenleyebilirsiniz. Tam kontrol sizdedir."}, {"question": "Ödeme yöntemleri nelerdir?", "answer": "Kredi kartı ve banka kartı ile güvenli ödeme yapabilirsiniz. Tüm ödemeler 256-bit SSL şifreleme ile korunur."}, {"question": "İade politikanız nedir?", "answer": "Ürün kişiye özel üretildiği için standart iade kabul edilmez. Ancak baskı hatası veya hasarlı ürün durumunda ücretsiz yeniden basım yapılır. Memnuniyetiniz bizim için önemlidir."}]}'::jsonb),

            (gen_random_uuid(), 'CTA_BAND'::section_type_enum, 'Çocuğunuza Özel Bir Masal Başlatıyor musunuz?', 'Sadece birkaç dakikada çocuğunuza özel, unutulmaz bir hediye çocuk kitabı oluşturun.', true, 8,
             '{"cta_text": "Şimdi Oluştur", "cta_url": "/create"}'::jsonb),

            (gen_random_uuid(), 'FOOTER'::section_type_enum, NULL, NULL, true, 9,
             '{"brand_description": "Yapay zeka destekli kişiye özel çocuk kitabı platformu. Çocuğunuzun adıyla masal oluşturun.", "nav_sections": [{"title": "Ürün", "links": [{"label": "Kitap Oluştur", "href": "/create"}, {"label": "Nasıl Çalışır?", "href": "#nasil-calisir"}, {"label": "Örnek Sayfalar", "href": "#ornekler"}, {"label": "Fiyatlandırma", "href": "#fiyat"}]}, {"title": "Destek", "links": [{"label": "Sıkça Sorulan Sorular", "href": "#sss"}, {"label": "İletişim", "href": "mailto:destek@benimmasalim.com"}]}, {"title": "Yasal", "links": [{"label": "KVKK Aydınlatma Metni", "href": "/kvkk"}, {"label": "Gizlilik Politikası", "href": "/privacy"}, {"label": "Kullanım Şartları", "href": "/terms"}]}], "bottom_text": "Türkiye''de sevgiyle yapıldı"}'::jsonb)
        ) AS v(id, section_type, title, subtitle, is_visible, sort_order, data)
        WHERE NOT EXISTS (SELECT 1 FROM homepage_sections LIMIT 1);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS homepage_sections;")
    op.execute("DROP TYPE IF EXISTS section_type_enum;")
