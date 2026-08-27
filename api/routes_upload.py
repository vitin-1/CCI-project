import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from config import settings
from db.database import get_db
from db.models import Event
from db.repositories.photo_repo import index_photo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])

_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/upload-batch", dependencies=[Depends(require_admin)])
def upload_batch(folder: str, event_id: str, db: Session = Depends(get_db)) -> dict:
    """Indexa todas as fotos de uma pasta acessível pelo servidor (admin-only)."""
    if db.get(Event, event_id) is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": f"Evento não encontrado: {event_id}"},
        )

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
            result = index_photo(photo_path, event_id, db)
            if result is not None:
                total_faces += result.face_count
                indexed += 1
                logger.info("indexed photo=%s faces=%d", photo_path.name, result.face_count)
            else:
                failed += 1
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


@router.post("/upload", dependencies=[Depends(require_admin)])
async def upload_single(
    event_id: str,
    photo: UploadFile = File(..., description="Foto do evento (JPEG/PNG/WebP). Indexada e enviada ao Storage."),
    db: Session = Depends(get_db),
) -> dict:
    """Indexa uma única foto enviada via HTTP (admin-only)."""
    if db.get(Event, event_id) is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": f"Evento não encontrado: {event_id}"},
        )

    suffix = Path(photo.filename or "").suffix.lower()
    if suffix not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_FORMAT",
                "message": f"Formato não suportado. Aceitos: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}",
            },
        )

    image_bytes = await photo.read()
    max_bytes = int(settings.max_image_size_mb * 1024 * 1024)
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail={"code": "IMAGE_TOO_LARGE", "message": f"Imagem maior que {settings.max_image_size_mb} MB."},
        )

    # cv2.imread precisa de um path — escrevemos em tempfile e limpamos no finally
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = Path(tmp.name)
    del image_bytes

    try:
        result = index_photo(tmp_path, event_id, db, original_filename=photo.filename)
    except Exception:
        logger.exception("upload_single_failed filename=%s", photo.filename)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"code": "INDEX_ERROR", "message": "Erro ao indexar a foto."},
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    if result is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "UNREADABLE_IMAGE", "message": "Não foi possível ler a imagem enviada."},
        )

    return {
        "data": {
            "photo_id": result.id,
            "filename": result.filename,
            "face_count": result.face_count,
            "preview_url": result.preview_path,
            "dry_run": settings.dry_run,
        }
    }
