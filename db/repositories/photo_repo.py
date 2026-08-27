import logging
import mimetypes
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
from sqlalchemy.orm import Session

from config import settings
from core.detector import detect_faces
from core.watermark import apply_watermark
from db.models import FaceEntry, Photo
from db.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def _cleanup_storage(uploaded: list[tuple[str, str]]) -> None:
    """Remove do Storage os arquivos já enviados em caso de erro (best-effort — não lança)."""
    if not uploaded:
        return
    supabase = get_supabase()
    for bucket, key in uploaded:
        try:
            supabase.storage.from_(bucket).remove([key])
            logger.info("storage_cleanup_ok bucket=%s key=%s", bucket, key)
        except Exception:
            logger.warning("storage_cleanup_failed bucket=%s key=%s", bucket, key)


def index_photo(
    photo_path: Path,
    event_id: str,
    db: Session,
    original_filename: str | None = None,
) -> Photo | None:
    """
    Indexa uma foto: detecta rostos, faz upload ao Supabase Storage e persiste no Postgres.
    Retorna o Photo persistido, ou None se a imagem for ilegível.
    Lança exceção em outros erros — o chamador é responsável pelo rollback do DB.
    Em erro de storage, reverte os uploads já realizados (best-effort).
    """
    img = cv2.imread(str(photo_path))
    if img is None:
        logger.warning("unreadable_photo path=%s", photo_path)
        return None

    faces = detect_faces(img)
    if not faces:
        logger.warning("no_faces_detected path=%s", photo_path)

    filename = original_filename or photo_path.name
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.embedding_ttl_days)
    photo_id = str(uuid.uuid4())
    suffix = Path(filename).suffix.lower() or photo_path.suffix.lower()
    original_key = f"{photo_id}{suffix}"
    preview_key = f"{photo_id}.jpg"
    preview_url = ""
    uploaded: list[tuple[str, str]] = []

    try:
        if not settings.dry_run:
            supabase = get_supabase()
            content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"

            with open(photo_path, "rb") as f:
                original_bytes = f.read()
            supabase.storage.from_(settings.supabase_bucket_originals).upload(
                original_key, original_bytes, {"content-type": content_type}
            )
            uploaded.append((settings.supabase_bucket_originals, original_key))

            preview_bytes = apply_watermark(photo_path)
            if preview_bytes:
                supabase.storage.from_(settings.supabase_bucket_previews).upload(
                    preview_key, preview_bytes, {"content-type": "image/jpeg"}
                )
                uploaded.append((settings.supabase_bucket_previews, preview_key))
                preview_url = supabase.storage.from_(settings.supabase_bucket_previews).get_public_url(preview_key)

        photo = Photo(
            id=photo_id,
            event_id=event_id,
            filename=filename,
            original_path=original_key,
            preview_path=preview_url,
            expires_at=expires_at,
            face_count=len(faces),
        )
        db.add(photo)
        db.flush()

        if faces and not settings.dry_run:
            for face in faces:
                db.add(FaceEntry(
                    photo_id=photo.id,
                    embedding=face["embedding"].tolist(),
                    bbox=face["bbox"],
                    expires_at=expires_at,
                ))

        if not settings.dry_run:
            db.commit()
        else:
            db.rollback()

        return photo

    except Exception:
        _cleanup_storage(uploaded)
        raise
