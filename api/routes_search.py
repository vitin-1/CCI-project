import logging

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import settings
from core.detector import extract_largest_face_embedding
from core.matcher import search_similar_faces
from db.database import get_db
from db.models import Photo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])


@router.post("/search")
async def search(
    selfie: UploadFile = File(..., description="Selfie do participante (JPEG/PNG). Não é armazenada."),
    db: Session = Depends(get_db),
) -> dict:
    """
    Busca fotos do evento que contenham a pessoa da selfie enviada.
    PRIVACIDADE: a selfie NÃO é salva em disco nem no banco — processada em memória e descartada.
    """
    max_bytes = int(settings.max_image_size_mb * 1024 * 1024)
    image_bytes = await selfie.read()

    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail={"code": "IMAGE_TOO_LARGE", "message": f"Imagem maior que {settings.max_image_size_mb} MB."},
        )

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    del image_bytes  # liberar memória antes da inferência

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

    # matcher retorna (photo_id, similarity) diretamente via query pgvector
    raw_matches = search_similar_faces(embedding, db)

    results: list[dict] = []
    seen_photos: set[str] = set()

    for photo_id, similarity in raw_matches:
        if photo_id in seen_photos:
            continue
        seen_photos.add(photo_id)

        photo = db.get(Photo, photo_id)
        if photo is None:
            logger.warning("photo_id_not_in_db photo_id=%s", photo_id)
            continue

        results.append({
            "photo_id": photo.id,
            "filename": photo.filename,
            "preview_url": photo.preview_path,  # URL pública do Supabase Storage
            "similarity": round(similarity, 4),
        })

    results.sort(key=lambda r: r["similarity"], reverse=True)

    return {"data": {"total": len(results), "results": results}}
