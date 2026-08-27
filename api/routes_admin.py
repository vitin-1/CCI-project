import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from config import settings
from db.database import get_db
from db.models import Photo, ReportedPhoto
from db.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/queue")
def get_queue(db: Session = Depends(get_db)) -> dict:
    """Lista denúncias pendentes de revisão, com preview_url e dados do denunciante quando disponíveis."""
    reports = (
        db.query(ReportedPhoto)
        .filter(ReportedPhoto.status == "pending")
        .order_by(ReportedPhoto.created_at.asc())
        .all()
    )

    # Batch fetch das fotos — evita N+1
    photo_ids = list({r.photo_id for r in reports})
    photos_by_id: dict[str, Photo] = {}
    if photo_ids:
        photos_by_id = {
            p.id: p
            for p in db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
        }

    result = []
    for r in reports:
        photo = photos_by_id.get(r.photo_id)
        item = {
            "report_id": r.id,
            "photo_id": r.photo_id,
            "preview_url": photo.preview_path if photo else None,
            "reason": r.reason,
            "created_at": r.created_at.isoformat(),
            "reporter": None,
        }
        if r.member_id and r.member:
            item["reporter"] = {"member_id": r.member_id, "full_name": r.member.full_name}
        result.append(item)

    return {"data": {"total": len(result), "queue": result}}


@router.post("/queue/{report_id}/approve")
def approve_report(report_id: str, db: Session = Depends(get_db)) -> dict:
    """Aprova a denúncia (foto será removida ou tratada pelo admin manualmente)."""
    report = db.get(ReportedPhoto, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "REPORT_NOT_FOUND", "message": "Denúncia não encontrada."},
        )
    if report.status != "pending":
        raise HTTPException(
            status_code=400,
            detail={"code": "REPORT_ALREADY_REVIEWED", "message": f"Denúncia já revisada (status: {report.status})."},
        )
    report.status = "approved"
    report.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("report_approved report_id=%s", report_id)
    return {"data": {"report_id": report_id, "status": "approved"}}


@router.post("/queue/{report_id}/reject")
def reject_report(report_id: str, db: Session = Depends(get_db)) -> dict:
    """Rejeita a denúncia (foto permanece no acervo)."""
    report = db.get(ReportedPhoto, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "REPORT_NOT_FOUND", "message": "Denúncia não encontrada."},
        )
    if report.status != "pending":
        raise HTTPException(
            status_code=400,
            detail={"code": "REPORT_ALREADY_REVIEWED", "message": f"Denúncia já revisada (status: {report.status})."},
        )
    report.status = "rejected"
    report.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("report_rejected report_id=%s", report_id)
    return {"data": {"report_id": report_id, "status": "rejected"}}


@router.get("/photo/{photo_id}/original")
def get_original_admin(photo_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Fallback administrativo — gera signed URL do original sem necessidade de verificação de participante.
    O fluxo padrão do app passa por POST /request-download → POST /confirm-download.
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
        if isinstance(response, dict):
            signed_url = response.get("signedURL") or response.get("signed_url", "")
        else:
            signed_url = getattr(response, "signed_url", "") or getattr(response, "signedURL", "")
    except Exception:
        logger.exception("admin_signed_url_failed photo_id=%s", photo_id)
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "Erro ao gerar URL de acesso ao original."},
        )

    if not signed_url:
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "URL de acesso ao original não pôde ser gerada."},
        )

    return {"data": {"signed_url": signed_url, "expires_in_seconds": 300}}
