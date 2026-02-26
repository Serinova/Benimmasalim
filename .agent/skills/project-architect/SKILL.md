---
name: Project Architect
description: Projedeki ana geliştirme mimarisini, kuralları ve standartları yürütmek için kullanılması ZORUNLU mimar danışmanlık becerisi. Herhangi bir kod yazmadan veya değişiklik yapmadan önce MUTLAKA bu beceriyi OKU ve uygula.
---

# Project Architect (Proje Mimarı)

Benim Masalım projesinde Antigravity'nin (senin) kod yazarken uymak ZORUNDA olduğu mutlak mimari ve mühendislik kurallarıdır. Bu doküman projedeki `.cursor/rules/` dosyalarını projeyle bütünleştiren köprüdür.

## ⚠️ Kritik Zorunluluklar

1. **Önce Kural Oku**: Frontend veya Backend üzerinde herhangi bir işlem yapmadan önce MUTLAKA `.cursor/rules/` klasöründeki karşılık gelen dosyayı (`frontend.mdc`, `backend.mdc`, `database.mdc`, `state-machine.mdc` vb.) okuyup belleğine al. O kuralları ihlal etmek kesinlikle yasaktır!

2. **Otonom Geliştirme**: 
   - Hata ayıklarken: Kod yazdıktan sonra mutlaka test et (örn. `npm run build`, `pytest`), hatayı kendin teşhis et ve onar. Kullanıcıya net açıklamalar yap.
   - Değişiklik yaparken: Eski dosyayı baştan yaratmak yerine, `replace_file_content` veya `multi_replace_file_content` kullanarak yama yöntemiyle sadece gerekli yerleri değiştir.

3. **State Machine & Asenkron Mimari**:
   - Python/FastAPI tarafında yazacağın her şey **async** olmak zorundadır (`await db.execute(...)`).
   - Bir siparişin durumu (`order.status = "..."`) manuel olarak değiştirilemez. Asenkron `transition_order` aracı kullanılmalıdır! Detaylar için: `.cursor/rules/state-machine.mdc`

4. **Klasör Disiplini**:
   - Geçiçi dosyalar, loglar veya deneme amaçlı md dosyalarını `root` dizinine yayma. İzole `/tmp` veya yerel dizinleri kullan, işin bitince sil.
   - Yayın (Deployment) sadece `.agent/workflows/deploy.md` üzerinden yapılır. `infra/` klasörü sadece referans içindir, değiştirmemelisin.

## Görevler ve Denetim:
Herhangi bir ticket veya iş isteği aldığında, kafana göre bir dosya açmak yerine, bu kurallara dayanarak "Nasıl yapmalıyım?" algoritmasını kur.
