import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import settings
from core.detector import detect_faces
from core.indexer import add_embeddings, get_index, invalidate_index_cache, save_index
from core.watermark import apply_watermark
from db.database import get_db
from db.models import FaceEntry, Photo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])


def require_admin(x_admin_token: str = Header(...)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Token de admin inválido."},
        )


def _index_single_photo(photo_path: Path, index, db: Session) -> int:
    """
    Indexa uma foto: detecta rostos, gera watermark, persiste no banco e no FAISS.
    Retorna o número de rostos indexados. Nunca lança — erros são logados.
    """
    img = cv2.imread(str(photo_path))
    if img is None:
        logger.warning("unreadable_photo path=%s", photo_path)
        return 0

    faces = detect_faces(img)
    if not faces:
        logger.warning("no_faces_detected path=%s", photo_path)

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.embedding_ttl_days)
    preview_path = settings.storage_previews / photo_path.name
    apply_watermark(photo_path, preview_path)

    photo = Photo(
        id=str(uuid.uuid4()),
        filename=photo_path.name,
        original_path=str(photo_path.resolve()),
        preview_path=str(preview_path.resolve()),
        expires_at=expires_at,
        face_count=len(faces),
    )
    db.add(photo)
    db.flush()

    if faces and not settings.dry_run:
        faiss_ids = add_embeddings(index, [f["embedding"] for f in faces])
        for face, faiss_id in zip(faces, faiss_ids):
            db.add(FaceEntry(
                photo_id=photo.id,
                faiss_id=faiss_id,
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

    index = get_index()
    indexed = failed = total_faces = 0

    for photo_path in photos:
        try:
            faces = _index_single_photo(photo_path, index, db)
            total_faces += faces
            indexed += 1
            logger.info("indexed photo=%s faces=%d", photo_path.name, faces)
        except Exception:
            logger.exception("index_failed photo=%s", photo_path.name)
            db.rollback()
            failed += 1

    if not settings.dry_run:
        save_index(index)
        invalidate_index_cache()

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
def get_original(photo_id: str, db: Session = Depends(get_db)) -> FileResponse:
    """
    Retorna a foto original para resgate (admin-only por enquanto).
    TODO(auth): substituir por token de resgate por participante — issue #1
    TODO(lgpd): validar que o solicitante é a pessoa identificada na foto — issue #2
    """
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PHOTO_NOT_FOUND", "message": "Foto não encontrada."},
        )

    original = Path(photo.original_path)
    if not original.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "FILE_NOT_FOUND", "message": "Arquivo original não encontrado no disco."},
        )

    return FileResponse(str(original), media_type="image/jpeg", filename=photo.filename)
