import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from core.notifications import send_whatsapp_code
from db.database import get_db
from db.models import DownloadRequest, Photo
from db.repositories.member_repo import (
    create_verification_code,
    get_consented_member,
    validate_and_use_code,
)
from db.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["download"])


class RequestDownloadBody(BaseModel):
    photo_id: str
    member_id: str


class ConfirmDownloadBody(BaseModel):
    download_request_id: str
    code: str


@router.post("/request-download")
def request_download(body: RequestDownloadBody, db: Session = Depends(get_db)) -> dict:
    """
    Inicia o fluxo de download da foto original.
    Valida consentimento do membro, cria DownloadRequest e envia código via WhatsApp.
    LGPD: download só é liberado após verificação de identidade via código.
    """
    member = get_consented_member(body.member_id, db)

    photo = db.get(Photo, body.photo_id)
    if photo is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PHOTO_NOT_FOUND", "message": "Foto não encontrada."},
        )

    req = DownloadRequest(photo_id=body.photo_id, member_id=body.member_id, status="pending_code")
    db.add(req)
    db.commit()
    db.refresh(req)

    code = create_verification_code(member.id, "download", db)
    send_whatsapp_code(member.whatsapp, code)
    logger.info("download_requested member_id=%s photo_id=%s request_id=%s", member.id, body.photo_id, req.id)

    return {"data": {"download_request_id": req.id, "expires_in_minutes": settings.code_ttl_minutes}}


@router.post("/confirm-download")
def confirm_download(body: ConfirmDownloadBody, db: Session = Depends(get_db)) -> dict:
    """
    Confirma o código recebido via WhatsApp e retorna a signed URL da foto original (válida 5 min).
    LGPD: só libera o original após verificação de identidade confirmada.
    """
    req = db.get(DownloadRequest, body.download_request_id)
    if req is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "REQUEST_NOT_FOUND", "message": "Solicitação de download não encontrada."},
        )
    if req.status != "pending_code":
        raise HTTPException(
            status_code=400,
            detail={"code": "REQUEST_ALREADY_PROCESSED", "message": f"Solicitação já processada (status: {req.status})."},
        )

    validate_and_use_code(req.member_id, body.code, "download", db)

    photo = db.get(Photo, req.photo_id)
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
        logger.exception("signed_url_failed photo_id=%s", req.photo_id)
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "Erro ao gerar URL de acesso ao original."},
        )

    if not signed_url:
        raise HTTPException(
            status_code=500,
            detail={"code": "STORAGE_ERROR", "message": "URL de acesso ao original não pôde ser gerada."},
        )

    req.status = "confirmed"
    db.commit()
    logger.info("download_confirmed request_id=%s photo_id=%s", req.id, req.photo_id)

    return {"data": {"signed_url": signed_url, "expires_in_seconds": 300}}
