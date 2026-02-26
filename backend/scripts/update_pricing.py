"""
Update Product Pricing - Set all books to base 1250 TL with discount to 299 TL
"""

import asyncio
from sqlalchemy import select, update
from app.core.database import async_session_factory
from app.models.product import Product


async def update_product_pricing():
    """Tüm ürünlerin fiyatını güncelle: 1250 TL → 299 TL indiriml"""
    
    print("\n" + "=" * 60)
    print("ÜRÜN FİYATLANDIRMA GÜNCELLEMESİ")
    print("=" * 60 + "\n")
    
    async with async_session_factory() as db:
        # Get all products
        result = await db.execute(select(Product))
        products = result.scalars().all()
        
        if not products:
            print("[ERROR] Hiç ürün bulunamadı!")
            return
        
        print(f"[INFO] {len(products)} ürün bulundu\n")
        
        for product in products:
            print(f"Ürün: {product.name}")
            print(f"  Önceki fiyat: {product.base_price} TL")
            print(f"  Önceki indirim: {product.discounted_price} TL")
            
            # Update pricing
            await db.execute(
                update(Product)
                .where(Product.id == product.id)
                .values(
                    base_price=1250.00,
                    discounted_price=299.00,
                    promo_badge="🔥 %76 İNDİRİM!",
                    social_proof_text="1000+ mutlu aile!",
                    feature_list=[
                        "Kişiye özel AI hikaye oluşturma",
                        "Çocuğunuzun fotoğrafıyla illüstrasyonlar",
                        "Profesyonel kalite baskı",
                        "Eğitici değerler içeriği",
                        "Sipariş öncesi hikaye önizleme",
                        "KVKK uyumlu veri güvenliği",
                        "Ücretsiz kargo",
                        "30 gün iade garantisi"
                    ]
                )
            )
            
            print(f"  Yeni fiyat: 1250 TL → 299 TL")
            print(f"  ✅ Güncellendi!\n")
        
        await db.commit()
        
        print("=" * 60)
        print(f"[SUCCESS] {len(products)} ürün fiyatı güncellendi!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(update_product_pricing())
