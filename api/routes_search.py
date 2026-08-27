import logging

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from config import settings
from core.detector import extract_largest_face_embedding
from core.matcher import search_similar_faces
from db.database import get_db
from db.models import Photo
from db.repositories.member_repo import get_consented_member

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])


@router.post("/search")
async def search(
    member_id: str,
    selfie: UploadFile = File(..., description="Selfie do participante (JPEG/PNG). Não é armazenada."),
    event_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Busca fotos do evento que contenham a pessoa da selfie enviada.
    Requer member_id com consentimento aceito (LGPD Art. 7).
    PRIVACIDADE: a selfie NÃO é salva em disco nem no banco — processada em memória e descartada.
    """
    get_consented_member(member_id, db)

    max_bytes = int(settings.max_image_size_mb * 1024 * 1024)
    image_bytes = await selfie.read()

    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail={"code": "IMAGE_TOO_LARGE", "message": f"Imagem maior que {settings.max_image_size_mb} MB."},
        )

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    del image_bytes

    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    del arr

    if img is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_IMAGE", "message": "Não foi possível decodificar a imagem."},
        )

    embedding = extract_largest_face_embedding(img)
    del img

    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "NO_FACE_DETECTED", "message": "Nenhum rosto detectado na selfie enviada."},
        )

    raw_matches = search_similar_faces(embedding, db, event_id=event_id)

    if not raw_matches:
        return {"data": {"total": 0, "results": []}}

    # Busca todos os Photos em um único query — evita N+1
    photo_ids = list({photo_id for photo_id, _ in raw_matches})
    photos_by_id: dict[str, Photo] = {
        p.id: p
        for p in db.query(Photo).options(joinedload(Photo.event)).filter(Photo.id.in_(photo_ids)).all()
    }

    results: list[dict] = []
    seen_photos: set[str] = set()

    for photo_id, similarity in raw_matches:
        if photo_id in seen_photos:
            continue
        seen_photos.add(photo_id)

        photo = photos_by_id.get(photo_id)
        if photo is None:
            logger.warning("photo_id_not_in_db photo_id=%s", photo_id)
            continue

        results.append({
            "photo_id": photo.id,
            "filename": photo.filename,
            "preview_url": photo.preview_path,
            "event_id": photo.event_id,
            "event_name": photo.event.name if photo.event else None,
            "similarity": round(similarity, 4),
        })

    results.sort(key=lambda r: r["similarity"], reverse=True)

    return {"data": {"total": len(results), "results": results}}
