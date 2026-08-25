import logging
import mimetypes
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import settings
from core.detector import detect_faces
from core.watermark import apply_watermark
from db.database import get_db
from db.models import FaceEntry, Photo
from db.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])


def require_admin(x_admin_token: str = Header(...)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Token de admin inválido."},
        )


def _index_single_photo(photo_path: Path, db: Session) -> int:
    """
    Indexa uma foto: detecta rostos, faz upload para Supabase Storage e persiste
    embeddings direto no Postgres. Retorna o número de rostos indexados. Nunca lança.
    """
    img = cv2.imread(str(photo_path))
    if img is None:
        logger.warning("unreadable_photo path=%s", photo_path)
        return 0

    faces = detect_faces(img)
    if not faces:
        logger.warning("no_faces_detected path=%s", photo_path)

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.embedding_ttl_days)
    photo_id = str(uuid.uuid4())
    suffix = photo_path.suffix.lower()
    original_key = f"{photo_id}{suffix}"
    preview_key = f"{photo_id}.jpg"

    supabase = get_supabase()
    content_type = mimetypes.guess_type(str(photo_path))[0] or "image/jpeg"

    # Upload do original para bucket privado
    with open(photo_path, "rb") as f:
        original_bytes = f.read()
    supabase.storage.from_(settings.supabase_bucket_originals).upload(
        original_key, original_bytes, {"content-type": content_type}
    )

    # Gera preview com watermark em memória e faz upload para bucket público
    preview_bytes = apply_watermark(photo_path)
    preview_url = ""
    if preview_bytes:
        supabase.storage.from_(settings.supabase_bucket_previews).upload(
            preview_key, preview_bytes, {"content-type": "image/jpeg"}
        )
        preview_url = supabase.storage.from_(settings.supabase_bucket_previews).get_public_url(preview_key)

    photo = Photo(
        id=photo_id,
        filename=photo_path.name,
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

    return len(faces)


_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/upload-batch", dependencies=[Depends(require_admin)])
def upload_batch(folder: str, db: Session = Depends(get_db)) -> dict:
    """Indexa todas as fotos de uma pasta acessível pelo servidor (admin-only)."""
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FOLDER", "message": f"Pasta não encontrada: {folder}"},
        )

    photos = [p for p in sorted(folder_path.iterdir()) if p.suffix.lower() in _SUPPORTED_EXTENSIONS]
    if not photos:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_PHOTOS", "message": "Nenhuma foto encontrada na pasta."},
        )

    indexed = failed = total_faces = 0

    for photo_path in photos:
        try:
            faces = _index_single_photo(photo_path, db)
            total_faces += faces
            indexed += 1
            logger.info("indexed photo=%s faces=%d", photo_path.name, faces)
        except Exception:
            logger.exception("index_failed photo=%s", photo_path.name)
            db.rollback()
            failed += 1

    return {
        "data": {
            "total_photos": len(photos),
            "indexed": indexed,
            "failed": failed,
            "total_faces": total_faces,
            "dry_run": settings.dry_run,
        }
    }


@router.get("/photo/{photo_id}/original", dependencies=[Depends(require_admin)])
def get_original(photo_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Gera signed URL do bucket originals e redireciona (admin-only por enquanto).
    TODO(auth): substituir por token de resgate por participante — issue #1
    TODO(lgpd): validar que o solicitante é a pessoa identificada na foto — issue #2
    """
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PHOTO_NOT_FOUND", "message": "Foto não encontrada."},
        )

    supabase = get_supabase()
    try:
        response = supabase.storage.from_(settings.supabase_bucket_originals).create_signed_url(
            photo.original_path, expires_in=300
        )
        signed_url = response.signed_url
    except Exception:
        logger.exception("signed_url_failed photo_id=%s path=%s", photo_id, photo.original_path)
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "Erro ao gerar URL de acesso ao original."},
        )

    return RedirectResponse(url=signed_url, status_code=302)
