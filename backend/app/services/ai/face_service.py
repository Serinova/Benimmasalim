"""Face detection, embedding extraction, and reference preparation using InsightFace."""

import io
import uuid
from typing import TYPE_CHECKING

import cv2
import numpy as np
import structlog
from PIL import Image

if TYPE_CHECKING:
    from app.services.storage_service import StorageService

from app.core.exceptions import FaceDetectionError

logger = structlog.get_logger()

# Lazy load InsightFace to avoid startup delay
_face_app = None
_face_app_failed = False


def get_face_app():
    """Get or initialize the InsightFace application. Returns None if unavailable."""
    global _face_app, _face_app_failed
    if _face_app_failed:
        return None
    if _face_app is None:
        try:
            from insightface.app import FaceAnalysis

            _face_app = FaceAnalysis(
                name="buffalo_l",
                providers=["CPUExecutionProvider"],
            )
            _face_app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace initialized")
        except Exception as exc:
            _face_app_failed = True
            logger.warning("InsightFace unavailable, face features disabled", error=str(exc))
            return None
    return _face_app


class FaceService:
    """Service for face detection and embedding extraction."""

    SCORE_THRESHOLD = 0.8
    MIN_IMAGE_SIZE = 512

    async def detect_and_extract(
        self,
        image_bytes: bytes,
    ) -> tuple[float, list[float], bytes]:
        """
        Detect face and extract embedding from image.

        Args:
            image_bytes: Raw image bytes (JPG/PNG)

        Returns:
            Tuple of (face_score, embedding, cropped_face_bytes)

        Raises:
            FaceDetectionError: If no face detected or quality too low
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))

            # Validate size
            if min(image.size) < self.MIN_IMAGE_SIZE:
                raise FaceDetectionError(
                    f"Fotoğraf çok küçük. Minimum {self.MIN_IMAGE_SIZE}x{self.MIN_IMAGE_SIZE} piksel gerekli."
                )

            # Convert to OpenCV format
            img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)

            # Get face analysis app
            app = get_face_app()
            if app is None:
                raise FaceDetectionError("Yüz analiz servisi kullanılamıyor.")

            # Detect faces
            faces = app.get(img_cv)

            if not faces:
                raise FaceDetectionError(
                    "Yüz tespit edilemedi. Lütfen yüzün net göründüğü bir fotoğraf yükleyin."
                )

            # Get the largest/best face
            face = max(faces, key=lambda f: f.det_score)

            # Check quality
            if face.det_score < self.SCORE_THRESHOLD:
                raise FaceDetectionError(
                    f"Yüz kalitesi yetersiz (skor: {face.det_score:.2f}). "
                    "Daha net bir fotoğraf deneyin."
                )

            # Extract embedding
            embedding = face.embedding.tolist()

            # Crop face region with generous padding for PuLID identity injection
            bbox = face.bbox.astype(int)
            padding = 80
            x1, y1, x2, y2 = bbox
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(img_cv.shape[1], x2 + padding)
            y2 = min(img_cv.shape[0], y2 + padding)

            cropped = img_cv[y1:y2, x1:x2]

            # Convert cropped face to bytes
            _, buffer = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 95])
            cropped_bytes = buffer.tobytes()

            logger.info(
                "Face detected and extracted",
                score=face.det_score,
                embedding_dim=len(embedding),
            )

            return face.det_score, embedding, cropped_bytes

        except FaceDetectionError:
            raise
        except Exception as e:
            logger.exception("Face detection failed", error=str(e))
            raise FaceDetectionError(
                "Fotoğraf işlenirken bir hata oluştu. Lütfen farklı bir fotoğraf deneyin."
            )

    async def compare_faces(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """Compare two face embeddings using cosine similarity (0-1)."""
        e1 = np.array(embedding1)
        e2 = np.array(embedding2)
        similarity = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
        return float(similarity)

    async def detect_face_in_generated(
        self,
        image_bytes: bytes,
    ) -> tuple[float, list[float]] | None:
        """Detect face in a generated (illustrated) image. Returns (score, embedding) or None."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
            app = get_face_app()
            if app is None:
                return None
            faces = app.get(img_cv)
            if not faces:
                return None
            face = max(faces, key=lambda f: f.det_score)
            if face.det_score < 0.5:
                return None
            return face.det_score, face.embedding.tolist()
        except Exception:
            logger.debug("Face detection in generated image failed (expected for some scenes)")
            return None


async def prepare_face_reference(
    photo_url: str,
    storage_service: "StorageService | None" = None,
) -> dict:
    """Download photo, detect face, crop, upload crop, return metadata.

    Returns dict with:
        face_crop_url: str | None   - GCS URL of cropped face (for PuLID)
        face_embedding: list[float] | None - 512-d embedding (for quality gate)
        face_score: float | None
        error: str | None           - human-readable error if face detection failed

    On any failure, returns the original photo_url as face_crop_url (graceful fallback).
    """
    import httpx

    result: dict = {
        "face_crop_url": photo_url,
        "face_embedding": None,
        "face_score": None,
        "error": None,
    }

    if not photo_url:
        result["error"] = "no_photo_url"
        return result

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(photo_url)
            resp.raise_for_status()
            image_bytes = resp.content

        face_svc = FaceService()
        face_svc.SCORE_THRESHOLD = 0.5  # Lower threshold: accept more photos
        face_svc.MIN_IMAGE_SIZE = 128   # Generated crops can be smaller

        score, embedding, cropped_bytes = await face_svc.detect_and_extract(image_bytes)

        if storage_service and cropped_bytes:
            crop_blob = f"temp/face-crops/{uuid.uuid4().hex}.jpg"
            crop_url = storage_service.provider.upload_bytes(cropped_bytes, crop_blob, "image/jpeg")
            result["face_crop_url"] = crop_url
        else:
            result["face_crop_url"] = photo_url

        result["face_embedding"] = embedding
        result["face_score"] = score

        logger.info(
            "FACE_REFERENCE_PREPARED",
            face_score=score,
            has_crop_url=result["face_crop_url"] != photo_url,
            embedding_dim=len(embedding),
        )

    except FaceDetectionError as e:
        logger.warning("Face detection failed for reference photo, using original", error=str(e))
        result["error"] = str(e)
    except Exception as e:
        logger.warning("Face reference preparation failed, using original photo", error=str(e))
        result["error"] = str(e)

    return result


async def resolve_face_reference(
    photo_url: str,
    storage_service: "StorageService | None" = None,
) -> tuple[str, str, list[float] | None]:
    """High-level helper: prepare face reference and return (face_crop_url, original_photo_url, embedding).

    Wraps ``prepare_face_reference`` with graceful fallback + logging.

    Returns:
        3-tuple of (face_crop_url, original_photo_url, embedding).
        - face_crop_url: kırpılmış yüz URL'si (veya orijinal, kırpma başarısızsa)
        - original_photo_url: orijinal tam fotoğraf URL'si (kırpma yapıldıysa);
          kırpma yapılmadıysa boş string (çift gönderimi engellemek için)
        - embedding: 512-d yüz embedding'i veya None
    """
    effective_url = photo_url or ""
    original_url = ""  # Kırpma yapıldığında orijinal fotoğrafı sakla
    embedding: list[float] | None = None
    if not photo_url:
        return effective_url, original_url, embedding
    try:
        ref = await prepare_face_reference(photo_url, storage_service=storage_service)
        effective_url = ref.get("face_crop_url") or photo_url
        embedding = ref.get("face_embedding")
        # Eğer yüz kırpma yapıldıysa, orijinal fotoğrafı da sakla
        # Kırpma yapılmadıysa (effective == original), boş bırak — çift gönderim gereksiz
        if effective_url != photo_url:
            original_url = photo_url
            logger.info(
                "DUAL_PHOTO_REFERENCE_ENABLED",
                face_crop_url_prefix=effective_url[:60],
                original_url_prefix=photo_url[:60],
            )
    except Exception as exc:
        logger.warning("resolve_face_reference failed, using original photo", error=str(exc))
    return effective_url, original_url, embedding
