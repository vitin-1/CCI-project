from fastapi import Header, HTTPException
from config import settings


def require_admin(x_admin_token: str = Header(...)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Token de admin inválido."},
        )
