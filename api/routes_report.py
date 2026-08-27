import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Photo, ReportedPhoto

logger = logging.getLogger(__name__)
router = APIRouter(tags=["report"])


class ReportPhotoBody(BaseModel):
    photo_id: str
    member_id: str | None = None  # LGPD: denúncias anônimas permitidas
    reason: str


@router.post("/report-photo")
def report_photo(body: ReportPhotoBody, db: Session = Depends(get_db)) -> dict:
    """
    Registra uma denúncia de foto inadequada.
    Não exige autenticação — qualquer um pode denunciar.
    O admin revisa a fila em GET /admin/queue.
    """
    photo = db.get(Photo, body.photo_id)
    if photo is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PHOTO_NOT_FOUND", "message": "Foto não encontrada."},
        )

    report = ReportedPhoto(
        photo_id=body.photo_id,
        member_id=body.member_id,
        reason=body.reason,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    logger.info("photo_reported report_id=%s photo_id=%s", report.id, body.photo_id)

    return {"data": {"report_id": report.id}}
