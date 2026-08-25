import logging
import mimetypes
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
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


def _index_single_photo(
    photo_path: Path,
    db: Session,
    original_filename: str | None = None,
) -> Photo | None:
    """
    Indexa uma foto: detecta rostos, faz upload para Supabase Storage e persiste
    embeddings direto no Postgres.
    Retorna o objeto Photo persistido, ou None se a imagem for ilegível.
    Lança exceção em outros erros — o chamador é responsável pelo rollback de DB.
    Em erro, reverte os uploads já realizados no Storage (best-effort).
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
    uploaded: list[tuple[str, str]] = []  # rastro para cleanup em caso de erro

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
            result = _index_single_photo(photo_path, db)
            if result is not None:
                total_faces += result.face_count
                indexed += 1
                logger.info("indexed photo=%s faces=%d", photo_path.name, result.face_count)
            else:
                failed += 1  # imagem ilegível
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
    photo: UploadFile = File(..., description="Foto do evento (JPEG/PNG/WebP). Indexada e enviada ao Storage."),
    db: Session = Depends(get_db),
) -> dict:
    """Indexa uma única foto enviada via HTTP (admin-only)."""
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
        result = _index_single_photo(tmp_path, db, original_filename=photo.filename)
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
        # supabase-py v2 retorna objeto com .signed_url; versões anteriores retornavam dict {"signedURL": ...}
        if isinstance(response, dict):
            signed_url = response.get("signedURL") or response.get("signed_url", "")
        else:
            signed_url = getattr(response, "signed_url", "") or getattr(response, "signedURL", "")
    except Exception:
        logger.exception("signed_url_failed photo_id=%s path=%s", photo_id, photo.original_path)
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "Erro ao gerar URL de acesso ao original."},
        )

    if not signed_url:
        logger.error("empty_signed_url photo_id=%s path=%s", photo_id, photo.original_path)
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "URL de acesso ao original não pôde ser gerada."},
        )

    return RedirectResponse(url=signed_url, status_code=302)
