"""Companion Kütüphanesi — Tüm companion tanımları tek merkezde.

Kullanım:
    from app.scenarios._companions import COMPANIONS

    # Tek companion al
    tilki = COMPANIONS.get("cappadocia_fox")

    # Liste halinde al
    companions = COMPANIONS.get_many("cappadocia_horse", "cappadocia_fox")

    # Tümünü al
    all_companions = COMPANIONS.all()

    # Tür bazında filtrele
    cats = COMPANIONS.by_species("cat")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.scenarios._base import CompanionAnchor


# ─────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────

@dataclass
class CompanionLibrary:
    """Tüm CompanionAnchor tanımlarının merkezi havuzu."""

    _pool: Dict[str, CompanionAnchor] = field(default_factory=dict)

    # -- mutators --

    def register(self, companion_id: str, anchor: CompanionAnchor) -> CompanionAnchor:
        """Havuza companion ekle. Aynı ID varsa uyar."""
        if companion_id in self._pool:
            import warnings
            warnings.warn(
                f"Companion '{companion_id}' zaten kayıtlı — üzerine yazılıyor.",
                stacklevel=2,
            )
        self._pool[companion_id] = anchor
        return anchor

    # -- accessors --

    def get(self, companion_id: str) -> CompanionAnchor:
        """Tek companion döndür. Bulunamazsa KeyError."""
        return self._pool[companion_id]

    def get_many(self, *companion_ids: str) -> List[CompanionAnchor]:
        """Birden fazla companion'ı sıralı liste olarak döndür."""
        return [self._pool[cid] for cid in companion_ids]

    def find(self, companion_id: str) -> Optional[CompanionAnchor]:
        """Tek companion döndür. Bulunamazsa None."""
        return self._pool.get(companion_id)

    def all(self) -> Dict[str, CompanionAnchor]:
        """Tüm companion'ları {id: anchor} olarak döndür."""
        return dict(self._pool)

    def by_species(self, species: str) -> Dict[str, CompanionAnchor]:
        """Belirli türdeki companion'ları filtrele."""
        return {
            cid: a for cid, a in self._pool.items()
            if a.species.lower() == species.lower()
        }

    def ids(self) -> List[str]:
        """Kayıtlı tüm companion ID'lerini döndür."""
        return list(self._pool.keys())

    @property
    def count(self) -> int:
        return len(self._pool)


# ─────────────────────────────────────────────────────────
# Singleton havuz
# ─────────────────────────────────────────────────────────

COMPANIONS = CompanionLibrary()
_r = COMPANIONS.register          # kısa yardımcı


# ═══════════════════════════════════════════════════════════
#  ABU SİMBEL
# ═══════════════════════════════════════════════════════════

_r("abusimbel_hawk", CompanionAnchor(
    name_tr="Altın Çöl Şahini",
    name_en="small golden desert hawk",
    species="hawk",
    appearance=(
        "small golden-feathered desert hawk with sharp amber eyes, "
        "dark brown wing tips, compact powerful build, regal posture"
    ),
    short_name="Horus",
))

# ═══════════════════════════════════════════════════════════
#  AMAZON
# ═══════════════════════════════════════════════════════════

_r("amazon_parrot", CompanionAnchor(
    name_tr="Renkli Papağan",
    name_en="colorful scarlet macaw parrot",
    species="macaw parrot",
    appearance=(
        "colorful scarlet macaw parrot with bright red, blue and yellow feathers, "
        "shiny black eyes, curved dark beak, and long tail feathers"
    ),
    short_name="Kızıl",
))

# ═══════════════════════════════════════════════════════════
#  KAPADOKYA
# ═══════════════════════════════════════════════════════════

_r("cappadocia_horse", CompanionAnchor(
    name_tr="Cesur Yılkı Atı",
    name_en="brave wild Cappadocian horse",
    species="wild horse",
    appearance=(
        "small brown wild Cappadocian horse with flowing dark mane, "
        "gentle dark eyes, and sturdy short legs"
    ),
    short_name="Yılkı",
))

_r("cappadocia_fox", CompanionAnchor(
    name_tr="Sevimli Kapadokya Tilkisi",
    name_en="small reddish-orange Cappadocian fox",
    species="fox",
    appearance=(
        "small reddish-orange Cappadocian fox with fluffy tail, "
        "bright green eyes, and white chest patch"
    ),
    short_name="Tilki",
))

_r("cappadocia_eagle", CompanionAnchor(
    name_tr="Cesur Dağ Kartalı",
    name_en="brave mountain eagle",
    species="eagle",
    appearance=(
        "brave dark brown mountain eagle with wide powerful wingspan, "
        "piercing golden eyes, sharp curved beak, and white-tipped tail feathers"
    ),
    short_name="Kartal",
))

_r("cappadocia_rabbit", CompanionAnchor(
    name_tr="Sevimli Step Tavşanı",
    name_en="small sandy-brown steppe rabbit with long ears",
    species="rabbit",
    appearance=(
        "small sandy-brown steppe rabbit with long upright ears, "
        "white cotton tail, bright curious dark eyes, and soft fluffy fur"
    ),
    short_name="Tavşan",
))

# ═══════════════════════════════════════════════════════════
#  ÇATALHÖYÜK
# ═══════════════════════════════════════════════════════════

_r("catalhoyuk_dog", CompanionAnchor(
    name_tr="Köpek",
    name_en="small playful sandy-brown village dog",
    species="dog",
    appearance=(
        "small playful sandy-brown village dog with floppy ears, "
        "a short wagging tail, warm brown eyes, and a dusty tan muzzle"
    ),
    short_name="Köy Köpeği",
))

# ═══════════════════════════════════════════════════════════
#  DİNOZOR
# ═══════════════════════════════════════════════════════════

_r("dinosaur_baby", CompanionAnchor(
    name_tr="Minik Bebek Dinozor",
    name_en="tiny friendly baby triceratops",
    species="baby dinosaur",
    appearance=(
        "tiny friendly light green baby triceratops with big curious brown eyes, "
        "small rounded horns, a cream-colored frill, and stubby legs"
    ),
    short_name="Bebek Dino",
))

# ═══════════════════════════════════════════════════════════
#  EFES
# ═══════════════════════════════════════════════════════════

_r("ephesus_cat", CompanionAnchor(
    name_tr="Efes Kedisi",
    name_en="sleek gray and white Ephesus street cat",
    species="cat",
    appearance=(
        "sleek gray and white Ephesus street cat with amber eyes "
        "and a small notch on the left ear"
    ),
    short_name="Efes Kedisi",
))

# ═══════════════════════════════════════════════════════════
#  MASAL DÜNYASI
# ═══════════════════════════════════════════════════════════

_r("fairy_tale_owl", CompanionAnchor(
    name_tr="Konuşan Masal Baykuşu",
    name_en="wise small purple owl with golden spectacles",
    species="owl",
    appearance=(
        "wise small purple owl with golden spectacles perched on its beak, "
        "bright golden eyes, soft purple-lavender feathers, tiny size"
    ),
    short_name="Bilge",
))

# ═══════════════════════════════════════════════════════════
#  GÖBEKLİTEPE
# ═══════════════════════════════════════════════════════════

_r("gobeklitepe_fox", CompanionAnchor(
    name_tr="Cesur Step Tilkisi",
    name_en="brave steppe fox",
    species="fox",
    appearance=(
        "small reddish-brown steppe fox with bushy tail, "
        "bright amber eyes, pointed ears, and a white-tipped snout"
    ),
    short_name="Step Tilkisi",
))

_r("gobeklitepe_eagle", CompanionAnchor(
    name_tr="Step Kartalı",
    name_en="majestic dark brown steppe eagle",
    species="eagle",
    appearance=(
        "majestic dark brown steppe eagle with golden-tipped feathers, "
        "piercing amber eyes, broad powerful wings, and sharp curved talons"
    ),
    short_name="Step Kartalı",
))

_r("gobeklitepe_goat", CompanionAnchor(
    name_tr="Neolitik Keçi",
    name_en="small brown Neolithic wild goat kid",
    species="goat",
    appearance=(
        "small brown Neolithic wild goat kid with curved tiny horns, "
        "a white chest patch, soft woolly coat, and curious dark eyes"
    ),
    short_name="Neolitik Keçi",
))

_r("gobeklitepe_wildcat", CompanionAnchor(
    name_tr="Yabani Kedi",
    name_en="small striped tawny wildcat",
    species="wildcat",
    appearance=(
        "small striped tawny wildcat with bright green eyes, "
        "a bushy ringed tail, pointed tufted ears, and silent soft paws"
    ),
    short_name="Yabani Kedi",
))

# ═══════════════════════════════════════════════════════════
#  KUDÜS
# ═══════════════════════════════════════════════════════════

_r("kudus_sparrow", CompanionAnchor(
    name_tr="Sevimli Zeytin Dalı Serçesi",
    name_en="tiny olive-brown sparrow with a small olive branch in its beak",
    species="sparrow",
    appearance=(
        "tiny olive-brown sparrow with a small olive branch in its beak "
        "and bright curious dark eyes"
    ),
    short_name="Serçe",
))

# ═══════════════════════════════════════════════════════════
#  OKYANUS
# ═══════════════════════════════════════════════════════════

_r("ocean_dolphin", CompanionAnchor(
    name_tr="Dostça Yunus",
    name_en="friendly grey bottlenose dolphin",
    species="dolphin",
    appearance=(
        "friendly medium-sized grey bottlenose dolphin with bright intelligent eyes, "
        "a permanent gentle smile, smooth silver-grey skin, and a small notch on dorsal fin"
    ),
    short_name="Dalga",
))

# ═══════════════════════════════════════════════════════════
#  UZAY
# ═══════════════════════════════════════════════════════════

_r("space_robot", CompanionAnchor(
    name_tr="Gümüş Robot Nova",
    name_en="small silver robot companion named Nova",
    species="robot",
    appearance=(
        "small silver robot companion named Nova with glowing blue LED eyes, "
        "a rotating silver antenna on top, rounded body with panel lines, "
        "two short articulated arms, and small wheel tracks for feet"
    ),
    short_name="Nova",
))

# ═══════════════════════════════════════════════════════════
#  SULTANAHMET
# ═══════════════════════════════════════════════════════════

_r("sultanahmet_dove", CompanionAnchor(
    name_tr="Minik Beyaz Güvercin",
    name_en="small pure white dove with gentle dark eyes",
    species="dove",
    appearance=(
        "small pure white dove with gentle dark eyes, "
        "soft pearly feathers, delicate outstretched wings, and a petite coral beak"
    ),
    short_name="Beyaz Güvercin",
))

# ═══════════════════════════════════════════════════════════
#  SÜMELA
# ═══════════════════════════════════════════════════════════

_r("sumela_squirrel", CompanionAnchor(
    name_tr="Fındık",
    name_en="small cute hazelnut-brown squirrel",
    species="squirrel",
    appearance=(
        "small cute hazelnut-brown squirrel with a bushy fluffy tail, "
        "bright curious eyes, and tiny agile paws"
    ),
    short_name="Fındık",
))

# ═══════════════════════════════════════════════════════════
#  OYUNCAK DÜNYASI
# ═══════════════════════════════════════════════════════════

_r("toy_world_teddy", CompanionAnchor(
    name_tr="Pelüş Ayıcık",
    name_en="fluffy teddy bear plushie",
    species="teddy bear plushie",
    appearance=(
        "fluffy golden-brown teddy bear plushie with a red bow tie, "
        "sewn button eyes, soft fuzzy fur, small and child-sized"
    ),
    short_name="Ponçik",
))

# ═══════════════════════════════════════════════════════════
#  YEREBATAN
# ═══════════════════════════════════════════════════════════

_r("yerebatan_cat", CompanionAnchor(
    name_tr="Gizemli Sarnıç Kedisi",
    name_en="mysterious black and white cat with bright green eyes",
    species="cat",
    appearance=(
        "elegant black and white tuxedo cat with bright emerald green eyes, "
        "silent soft paws, graceful posture, small and agile"
    ),
    short_name="Gölge",
))


# ─────────────────────────────────────────────────────────
# Temizlik
# ─────────────────────────────────────────────────────────
del _r  # modül namespace'ini temiz tut
