"""Negatif prompt builder testleri — child safety, gender lock, face reference, stil negatifi.

BASE_NEGATIVE çocuk güvenliği terimlerini içermeli.
Gender-specific negatives yanlış cinsiyet kıyafetini engeller.
face_reference_url ANTI_PHOTO_FACE'i tetikler.
Her stil kendi negative bloğunu ekler.
"""

import pytest

from app.prompt.book_context import BookContext
from app.prompt.negative_builder import (
    _BOY_NEGATIVE,
    _GIRL_NEGATIVE,
    BASE_NEGATIVE,
    build_negative,
)
from app.prompt.style_config import STYLES


class TestBaseNegativeChildSafety:
    """BASE_NEGATIVE çocuk güvenliği için zorunlu terimleri içermeli."""

    CHILD_SAFETY_TERMS = [
        "scary",
        "horror",
        "weapons",
        "violence",
        "blood",
        "adult themes",
        "monsters",
        "creepy",
        "nightmare",
        "threatening",
    ]

    @pytest.mark.parametrize("term", CHILD_SAFETY_TERMS)
    def test_base_negative_contains_safety_term(self, term: str):
        assert term in BASE_NEGATIVE, f"BASE_NEGATIVE '{term}' içermeli — çocuk güvenliği"

    def test_base_negative_blocks_closeups(self):
        """Yakın çekim kompozisyon kısıtları mevcut."""
        for term in ("close-up", "portrait", "headshot"):
            assert term in BASE_NEGATIVE, f"BASE_NEGATIVE '{term}' içermeli"

    def test_base_negative_blocks_bad_anatomy(self):
        """Anatomik bozukluklar engellenmeli."""
        for term in ("extra fingers", "deformed hands", "bad anatomy"):
            assert term in BASE_NEGATIVE, f"BASE_NEGATIVE '{term}' içermeli"

    def test_base_negative_blocks_text_watermark(self):
        """Metin ve watermark engellenmeli."""
        for term in ("text", "watermark"):
            assert term in BASE_NEGATIVE


class TestGenderSpecificNegatives:
    """Gender-specific negative terimler yanlış cinsiyet öğelerini engeller."""

    def test_boy_negative_excludes_feminine_clothing(self):
        """Erkek çocuk negatifi feminen kıyafetleri içermeli."""
        for term in ("dress", "skirt", "girly clothes", "feminine clothing"):
            assert term in _BOY_NEGATIVE, f"_BOY_NEGATIVE '{term}' içermeli"

    def test_girl_negative_excludes_masculine_features(self):
        """Kız çocuk negatifi erkek özelliklerini içermeli."""
        for term in ("male clothing", "masculine features", "boy's outfit"):
            assert term in _GIRL_NEGATIVE, f"_GIRL_NEGATIVE '{term}' içermeli"

    def test_build_negative_boy_adds_boy_negative(self):
        """Erkek çocuk için build_negative() boy negative'i ekler."""
        ctx = BookContext.build(
            child_name="Can",
            child_age=6,
            child_gender="erkek",
        )
        negative = build_negative(ctx)
        assert "dress" in negative
        assert "skirt" in negative
        assert "girly clothes" in negative

    def test_build_negative_girl_adds_girl_negative(self):
        """Kız çocuk için build_negative() girl negative'i ekler."""
        ctx = BookContext.build(
            child_name="Ela",
            child_age=5,
            child_gender="kız",
        )
        negative = build_negative(ctx)
        assert "male clothing" in negative
        assert "masculine features" in negative

    def test_build_negative_erkek_maps_to_boy(self):
        """'erkek' cinsiyet boy negative'ini tetikler."""
        ctx = BookContext.build(
            child_name="Ali",
            child_age=7,
            child_gender="erkek",
        )
        negative = build_negative(ctx)
        assert "dress" in negative  # _BOY_NEGATIVE

    def test_build_negative_kiz_maps_to_girl(self):
        """'kız' cinsiyet girl negative'ini tetikler."""
        ctx = BookContext.build(
            child_name="Zeynep",
            child_age=4,
            child_gender="kız",
        )
        negative = build_negative(ctx)
        assert "male clothing" in negative  # _GIRL_NEGATIVE

    def test_build_negative_boy_excludes_girl_negative(self):
        """Erkek için girl negative eklenmemeli."""
        ctx = BookContext.build(
            child_name="Mert",
            child_age=6,
            child_gender="erkek",
        )
        negative = build_negative(ctx)
        assert "male clothing" not in negative  # _GIRL_NEGATIVE erkek için eklenmez

    def test_build_negative_girl_excludes_boy_negative(self):
        """Kız için boy negative eklenmemeli."""
        ctx = BookContext.build(
            child_name="Selin",
            child_age=5,
            child_gender="kız",
        )
        negative = build_negative(ctx)
        assert "skirt" not in negative  # _BOY_NEGATIVE kız için eklenmez


class TestFaceReferenceNegative:
    """face_reference_url ANTI_PHOTO_FACE'i tetikler."""

    def test_face_reference_adds_anti_photo_face(self):
        """face_reference_url set edilince ANTI_PHOTO_FACE eklenir."""
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            face_reference_url="https://storage.example.com/photos/enes.jpg",
        )
        negative = build_negative(ctx)
        assert "photorealistic" in negative
        assert "face swap" in negative
        assert "pasted face" in negative

    def test_no_face_reference_no_anti_photo(self):
        """face_reference_url boş → ANTI_PHOTO_FACE eklenmez."""
        ctx = BookContext.build(
            child_name="Ali",
            child_age=6,
            child_gender="erkek",
            face_reference_url="",
        )
        negative = build_negative(ctx)
        assert "pasted face" not in negative
        assert "face swap" not in negative

    def test_face_reference_anti_photo_contains_pores(self):
        """ANTI_PHOTO_FACE 'pores' ve 'realistic skin texture' içermeli."""
        ctx = BookContext.build(
            child_name="Ela",
            child_age=5,
            child_gender="kız",
            face_reference_url="https://example.com/face.jpg",
        )
        negative = build_negative(ctx)
        assert "pores" in negative
        assert "realistic skin texture" in negative


class TestCharacterConsistencyNegative:
    """Karakter tutarlılığı negatif terimleri mevcut."""

    def test_character_consistency_in_all_builds(self):
        """Her build_negative() çağrısında _CHARACTER_CONSISTENCY_NEGATIVE dahil edilir."""
        for gender in ("erkek", "kız"):
            ctx = BookContext.build(
                child_name="Test",
                child_age=6,
                child_gender=gender,
            )
            negative = build_negative(ctx)
            assert "different outfit" in negative
            assert "outfit change" in negative
            assert "different hairstyle" in negative
            assert "hair color change" in negative
            assert "different skin tone" in negative
            assert "age change" in negative
            assert "different child" in negative


class TestStyleNegatives:
    """Her stil kendi negatif bloğunu build_negative()'e ekler."""

    @pytest.mark.parametrize("style_key", list(STYLES.keys()))
    def test_style_negative_present_in_build_negative(self, style_key: str):
        """build_negative() stil negatifini dahil etmeli."""
        style = STYLES[style_key]
        if not style.negative:
            pytest.skip(f"{style_key} stili negatif tanımlamıyor")

        ctx = BookContext.build(
            child_name="Test",
            child_age=6,
            child_gender="erkek",
            style_modifier=style_key,
        )
        negative = build_negative(ctx)
        # Stil negatifinin en azından bir parçası sonuçta bulunmalı
        style_neg_fragment = style.negative[:30]
        assert style_neg_fragment in negative, (
            f"{style_key} stil negatifi build_negative() sonucunda eksik"
        )

    def test_pixar_negative_blocks_2d(self):
        """Pixar stili negatifi 2D üretimini engeller."""
        ctx = BookContext.build(
            child_name="Enes",
            child_age=7,
            child_gender="erkek",
            style_modifier="Pixar 3D CGI",
        )
        negative = build_negative(ctx)
        assert "2d" in negative.lower() or "flat shading" in negative.lower()

    def test_anime_negative_blocks_photorealistic(self):
        """Anime stili negatifi photorealistik üretimi engeller."""
        ctx = BookContext.build(
            child_name="Ela",
            child_age=5,
            child_gender="kız",
            style_modifier="Studio Ghibli anime",
        )
        negative = build_negative(ctx)
        assert "photorealistic" in negative.lower()

    def test_base_negative_always_present_regardless_of_style(self):
        """BASE_NEGATIVE tüm stillerde her zaman dahil edilmeli."""
        base_fragment = "extra fingers"  # BASE_NEGATIVE'den benzersiz bir parça
        for style_key in STYLES:
            ctx = BookContext.build(
                child_name="Test",
                child_age=6,
                child_gender="erkek",
                style_modifier=style_key,
            )
            negative = build_negative(ctx)
            assert base_fragment in negative, (
                f"{style_key} stilinde BASE_NEGATIVE eksik ('{base_fragment}' bulunamadı)"
            )
