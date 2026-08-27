"""
Testes unitários para a lógica de verificação de código (db/repositories/member_repo.py).
Seguem o estilo de tests/core/test_matcher.py — testam a função diretamente com mock de Session.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.repositories.member_repo import validate_and_use_code, create_verification_code, get_consented_member


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mock_db_returning(row) -> Session:
    db = MagicMock(spec=Session)
    db.execute.return_value.fetchone.return_value = row
    return db


def _make_row(expired: bool, code_id: str = "code-uuid-1"):
    row = MagicMock()
    row.id = code_id
    row.expired = expired
    return row


# ── validate_and_use_code ──────────────────────────────────────────────────────

def test_valid_code_marks_used():
    db = _mock_db_returning(_make_row(expired=False))
    validate_and_use_code("member-1", "123456", "download", db)
    db.commit.assert_called_once()


def test_expired_code_raises_code_expired():
    db = _mock_db_returning(_make_row(expired=True))
    with pytest.raises(HTTPException) as exc:
        validate_and_use_code("member-1", "123456", "download", db)
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "CODE_EXPIRED"


def test_invalid_code_raises_invalid_code():
    db = _mock_db_returning(None)
    with pytest.raises(HTTPException) as exc:
        validate_and_use_code("member-1", "999999", "download", db)
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "INVALID_CODE"


def test_valid_code_executes_update():
    row = _make_row(expired=False, code_id="my-code-id")
    db = _mock_db_returning(row)
    validate_and_use_code("member-1", "123456", "register", db)
    # Deve ter chamado execute duas vezes: SELECT e UPDATE
    assert db.execute.call_count == 2


# ── create_verification_code ───────────────────────────────────────────────────

def test_create_code_has_six_digits():
    db = MagicMock(spec=Session)
    code = create_verification_code("member-1", "register", db)
    assert len(code) == 6
    assert code.isdigit()


def test_create_code_persists_and_commits():
    db = MagicMock(spec=Session)
    create_verification_code("member-1", "download", db)
    db.add.assert_called_once()
    db.commit.assert_called_once()


# ── get_consented_member ──────────────────────────────────────────────────────

def test_member_not_found_raises():
    db = MagicMock(spec=Session)
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_consented_member("nao-existe", db)
    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "MEMBER_NOT_FOUND"


def test_member_without_consent_raises():
    member = MagicMock()
    member.consent_accepted_at = None
    db = MagicMock(spec=Session)
    db.get.return_value = member
    with pytest.raises(HTTPException) as exc:
        get_consented_member("member-1", db)
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "CONSENT_REQUIRED"


def test_member_with_consent_returns_member():
    member = MagicMock()
    member.consent_accepted_at = datetime.now(timezone.utc)
    db = MagicMock(spec=Session)
    db.get.return_value = member
    result = get_consented_member("member-1", db)
    assert result is member
