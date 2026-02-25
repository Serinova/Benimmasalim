"""Remove scary/negative content and deity references from scenario prompts for child safety.

Changes per scenario:
- gobeklitepe: Remove Gizemli Yılan + Meraklı Akrep (venomous animals); replace with friendlier animals
- ephesus:     Remove gladyatör kabartmaları (violence); replace with antik spor sahneleri
              Remove Athena deity reference from owl character
              Remove Artemis deity reference from temple name
- catalhoyuk:  Remove boyalı kafatasları (skulls); replace with boncuklar ve el sanatları; soften dark tunnel
              Remove Ana Tanrıça (goddess) references; replace with neutral arkeolojik eser
- yerebatan:   Remove Gizemli Medusa Fısıltısı + fear confrontation phrasing; add gentler characters
- abusimbel:   Remove Kadeş Savaşı / savaş kabartmaları (battle); replace with tarihi sahneler
              Remove Osiris deity name from column description
              Remove Hathor deity name from column description
              Replace Hayalet (ghost) with Ses/Ruhu
- tacmahal:    Replace Hayalet (ghost) with Ses/Ruhu
- galata:      Replace Hayalet (ghost) with Ses/Anısı

Revision ID: 065_fix_child_safe_scenario_prompts
Revises: 064_populate_all_scenario_story_prompts
Create Date: 2026-02-21
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "065_fix_child_safe_scenario_prompts"
down_revision: str = "064_populate_all_scenario_story_prompts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_FIXES: list[tuple[str, str, str]] = [
    # (theme_key, old_text, new_text)
    # --- Deity / goddess references ---
    (
        "ephesus",
        "5. Artemis Tapınağı — Dünyanın Yedi Harikası'ndan biri, tek ayakta kalan sütun",
        "5. Antik tapınak kalıntıları — Dünyanın Yedi Harikası'ndan biri, tek ayakta kalan görkemli sütun",
    ),
    (
        "ephesus",
        "Bilge Baykuş (Athena'nın kutsal kuşu), Cesur Yunus (Ege Denizi'nden), Meraklı Kedi (antik Efes sokaklarından),",
        "Bilge Baykuş (Efes'in bilge kuşu), Cesur Yunus (Ege Denizi'nden), Meraklı Kedi (antik Efes sokaklarından),",
    ),
    (
        "catalhoyuk",
        "3. Ana Tanrıça figürini — leoparların arasında tahtında oturan kadın figürini, bereket sembolü",
        "3. Antik bereket figürini — 9.000 yıllık kadın heykeli, insanlığın en eski sanat eserlerinden biri",
    ),
    (
        "catalhoyuk",
        "Bilge Boğa (duvar resminden canlanan aurochs), Kurnaz Leopar (Ana Tanrıça'nın koruyucusu),",
        "Bilge Boğa (duvar resminden canlanan aurochs), Kurnaz Leopar (Neolitik çağdan canlanan, mağara duvarından çıkmış),",
    ),
    (
        "catalhoyuk",
        "Ana Tanrıça figürini \"bereket ve koruma\" sembolü olarak, dini figür olarak DEĞİL.",
        "Antik bereket figürini \"arkeolojik eser ve sanat\" perspektifinden, dini obje olarak DEĞİL.",
    ),
    (
        "catalhoyuk",
        "\"Obsidyen ayna atölyesinde parlak taş aletlerin arasında\", \"Ana Tanrıça figürininin bulunduğu niş önünde\".",
        "\"Obsidyen ayna atölyesinde parlak taş aletlerin arasında\", \"Antik bereket heykelinin bulunduğu sergi nişinin önünde\".",
    ),
    (
        "abusimbel",
        "2. Hipostil salon — 8 devasa Osiris sütunu, tavan kanatları, giriş ışığının karanlığı yaran dramatik ışık demetleri",
        "2. Hipostil salon — 8 devasa taş sütun, tavan kanatları, giriş ışığının karanlığı yaran dramatik ışık demetleri",
    ),
    (
        "abusimbel",
        "5. Nefertari Tapınağı — Kraliçe Nefertari'ye adanmış zarif tapınak, 6 ayakta duran dev heykel, Hathor başlı sütunlar",
        "5. Nefertari Yapısı — Kraliçe Nefertari'ye yapılmış zarif anıt, 6 ayakta duran dev heykel, dekoratif başlıklı sütunlar",
    ),
    (
        "abusimbel",
        "Antik Mısır tanrıları \"mitolojik figürler ve heykel sanatı\" olarak sunulsun.",
        "Antik Mısır mitleri \"efsaneler ve heykel sanatı\" perspektifinden sunulsun, tanrı/tanrıça isimlerine odaklanılmasın.",
    ),
    (
        "abusimbel",
        "\"Nefertari Tapınağı'nın Hathor başlı sütunları arasında\".",
        "\"Nefertari Yapısı'nın dekoratif başlıklı sütunları arasında\".",
    ),
    # --- Scary / negative content ---
    (
        "gobeklitepe",
        "Bilge Tilki (dikilitaştaki tilki kabartmasından esinlenmiş), Cesur Akbaba, Gizemli Yılan,\nMeraklı Akrep veya Konuşan Turna kuşu.",
        "Bilge Tilki (dikilitaştaki tilki kabartmasından esinlenmiş), Cesur Akbaba (gökyüzünün rehberi),\nNeşeli Tavşan veya Konuşan Turna kuşu.",
    ),
    (
        "ephesus",
        "Efes Arkeoloji Müzesi — Artemis heykeli, gladyatör kabartmaları, altın sikkeler, antik takılar",
        "Efes Arkeoloji Müzesi — Artemis heykeli, antik spor sahneleri kabartmaları, altın sikkeler, antik takılar",
    ),
    (
        "catalhoyuk",
        "10. Gizli geçitler — evlerin altında gömü alanları, ataların hikayeleri, boyalı kafatasları",
        "10. Gizli geçitler — evlerin altında ataların hatıra alanları, renkli boncuklar ve el sanatları eserleri",
    ),
    (
        "catalhoyuk",
        "- Cesaret seçildiyse: 18 katman derinliğindeki karanlık katmanlara inmek zorunda kalsın",
        "- Cesaret seçildiyse: gizemli geçitten geçerek antik katmanları keşfetmek zorunda kalsın",
    ),
    (
        "yerebatan",
        "Konuşan Yusufçuk (sarnıcın sularında yaşayan ışıltılı böcek, yansımaların sırrını bilen),\nGizemli Medusa Fısıltısı (heykelden çıkan ses, 1.500 yıl öncesinin hikayelerini anlatan),\nIşıltılı Balık (kehribar ışıkta suyun altında parıldayan, gizli geçitleri bilen),\nBilge Su Ruhu (sarnıcın derinliklerinden yükselen, binlerce yılın bilgeliğini taşıyan)\nveya Meraklı Fare (sütunların arasında koşan, her gizli köşeyi bilen neşeli rehber).\nKarakter, Bizans döneminden veya sarnıcın büyülü atmosferinden \"uyanmış\" olabilir.",
        "Konuşan Yusufçuk (sarnıcın sularında yaşayan ışıltılı böcek, yansımaların sırrını bilen),\nIşıltılı Balık (kehribar ışıkta suyun altında parıldayan, gizli geçitleri bilen),\nBilge Su Ruhu (sarnıcın derinliklerinden yükselen, binlerce yılın bilgeliğini taşıyan),\nNeşeli Fare (sütunların arasında koşan, her gizli köşeyi bilen sevimli rehber)\nveya Renkli Kelebek (ışık yansımalarından doğan, mekanın büyüsünü gösteren).\nKarakter, Bizans döneminden veya sarnıcın büyülü atmosferinden \"uyanmış\" olabilir.",
    ),
    (
        "yerebatan",
        "Medusa başlarının gizemi çocuğu kendi korkusuyla yüzleştiriyor.",
        "Medusa başlarının gizemli hikayesi çocuğu merakla dolduruyor.",
    ),
    (
        "abusimbel",
        "6. Savaş kabartmaları — Kadeş Savaşı'nı gösteren devasa duvar oymaları, savaş arabaları, atlar, okçular",
        "6. Tarihi sahneler — eski yaşamı ve kahramanlıkları anlatan devasa duvar oymaları, atlar, arabalar, antik figürler",
    ),
    (
        "abusimbel",
        "veya Usta Taş Yontucu Hayaleti (3.000 yıl önce heykelleri oymuş antik ustanın neşeli hayaleti, sabrın sırrını öğreten).",
        "veya Bilge Taş Yontucu Sesi (3.000 yıl önce heykelleri oymuş antik ustanın ruhu, sabrın sırrını öğreten).",
    ),
    (
        "tacmahal",
        "Usta Taş Kakmacı Hayaleti (yüzlerce yıl önce en güzel çiçek desenini yapmış ustanın neşeli hayaleti)",
        "Bilge Taş Kakmacı Sesi (yüzlerce yıl önce en güzel çiçek desenini yapmış ustanın ruhu ve anısı)",
    ),
    (
        "galata",
        "Hezarfen'in Hayaleti (yapma kanatlarla uçmuş Osmanlı mucidinin neşeli hayaleti, çocuğa cesaret veren),",
        "Hezarfen'in Sesi (yapma kanatlarla uçmuş Osmanlı mucidinin neşeli anısı, çocuğa cesaret veren),",
    ),
]


def upgrade() -> None:
    for theme_key, old_text, new_text in _FIXES:
        op.execute(
            sa.text(
                "UPDATE scenarios "
                "SET story_prompt_tr = REPLACE(story_prompt_tr, :old, :new) "
                "WHERE theme_key = :key "
                "AND story_prompt_tr LIKE :like_pattern"
            ).bindparams(
                old=old_text,
                new=new_text,
                key=theme_key,
                like_pattern=f"%{old_text[:40]}%",
            )
        )


def downgrade() -> None:
    pass
