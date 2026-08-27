import random
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings
from db.models import Member, VerificationCode


def get_consented_member(member_id: str, db: Session) -> Member:
    """Retorna o Member se existe e aceitou consentimento; lança HTTPException caso contrário."""
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Membro não encontrado."},
        )
    # LGPD: bloquear qualquer operação sensível sem consentimento explícito (Art. 7 LGPD)
    if member.consent_accepted_at is None:
        raise HTTPException(
            status_code=403,
            detail={"code": "CONSENT_REQUIRED", "message": "Consentimento não aceito. Acesse /consent primeiro."},
        )
    return member


def create_verification_code(member_id: str, purpose: str, db: Session) -> str:
    """Gera, persiste e retorna código de 6 dígitos com TTL configurado em settings.code_ttl_minutes."""
    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.code_ttl_minutes)
    db.add(VerificationCode(
        member_id=member_id,
        code=code,
        purpose=purpose,
        expires_at=expires_at,
    ))
    db.commit()
    return code


def validate_and_use_code(member_id: str, code: str, purpose: str, db: Session) -> None:
    """
    Valida o código e marca como usado.
    Lança HTTPException com código de erro específico:
      INVALID_CODE  — código não encontrado ou já usado
      CODE_EXPIRED  — código expirado (mas era válido)
    """
    row = db.execute(
        text("""
            SELECT id, expires_at < NOW() AS expired
            FROM verification_codes
            WHERE member_id = :member_id
              AND code      = :code
              AND purpose   = :purpose
              AND used_at IS NULL
            ORDER BY expires_at DESC
            LIMIT 1
        """),
        {"member_id": member_id, "code": code, "purpose": purpose},
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_CODE", "message": "Código inválido."},
        )
    if row.expired:
        raise HTTPException(
            status_code=400,
            detail={"code": "CODE_EXPIRED", "message": "Código expirado. Solicite um novo via /send-code."},
        )

    db.execute(text("UPDATE verification_codes SET used_at = NOW() WHERE id = :id"), {"id": row.id})
    db.commit()
