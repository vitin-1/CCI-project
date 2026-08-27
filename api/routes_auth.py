import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.notifications import send_whatsapp_code
from db.database import get_db
from db.models import Member
from db.repositories.member_repo import create_verification_code, validate_and_use_code

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    full_name: str
    whatsapp: str  # formato +5511999999999


class ConsentRequest(BaseModel):
    member_id: str


class SendCodeRequest(BaseModel):
    member_id: str
    purpose: str  # "register" | "download"


class ConfirmCodeRequest(BaseModel):
    member_id: str
    code: str
    purpose: str  # "register" | "download"


@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    """Cadastra um novo participante. Consentimento é coletado na etapa seguinte via /consent."""
    existing = db.query(Member).filter(Member.whatsapp == body.whatsapp).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"code": "WHATSAPP_ALREADY_REGISTERED", "message": "WhatsApp já cadastrado."},
        )
    member = Member(full_name=body.full_name, whatsapp=body.whatsapp)
    db.add(member)
    db.commit()
    db.refresh(member)
    logger.info("member_registered id=%s", member.id)
    return {"data": {"member_id": member.id}}


@router.post("/consent")
def accept_consent(body: ConsentRequest, db: Session = Depends(get_db)) -> dict:
    """
    Registra aceite explícito de consentimento LGPD.
    LGPD Art. 7: base legal para processamento de dado pessoal — sem isso, /search e /request-download bloqueados.
    Idempotente — múltiplas chamadas não criam registros duplicados.
    """
    member = db.get(Member, body.member_id)
    if member is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Membro não encontrado."},
        )
    if member.consent_accepted_at is None:
        from datetime import datetime, timezone
        member.consent_accepted_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("consent_accepted member_id=%s", member.id)
    return {"data": {"member_id": member.id, "consented": True}}


@router.post("/send-code")
def send_code(body: SendCodeRequest, db: Session = Depends(get_db)) -> dict:
    """Gera código de 6 dígitos e envia via WhatsApp. Válido por settings.code_ttl_minutes."""
    if body.purpose not in ("register", "download"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PURPOSE", "message": "purpose deve ser 'register' ou 'download'."},
        )
    member = db.get(Member, body.member_id)
    if member is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Membro não encontrado."},
        )
    code = create_verification_code(member.id, body.purpose, db)
    send_whatsapp_code(member.whatsapp, code)
    logger.info("code_sent member_id=%s purpose=%s", member.id, body.purpose)
    from config import settings
    return {"data": {"sent": True, "expires_in_minutes": settings.code_ttl_minutes}}


@router.post("/confirm-code")
def confirm_code(body: ConfirmCodeRequest, db: Session = Depends(get_db)) -> dict:
    """Valida e consome o código de verificação. Retorna erro específico para inválido vs expirado."""
    if body.purpose not in ("register", "download"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PURPOSE", "message": "purpose deve ser 'register' ou 'download'."},
        )
    member = db.get(Member, body.member_id)
    if member is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Membro não encontrado."},
        )
    validate_and_use_code(body.member_id, body.code, body.purpose, db)
    logger.info("code_confirmed member_id=%s purpose=%s", body.member_id, body.purpose)
    return {"data": {"confirmed": True}}
