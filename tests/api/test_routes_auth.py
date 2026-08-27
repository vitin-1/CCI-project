"""
Testes HTTP para as rotas de auth (api/routes_auth.py).
Complementam os testes unitários de test_auth.py (que testam o repo diretamente).
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.fixture
def client_db():
    from api.main import app
    from db.database import get_db
    from fastapi.testclient import TestClient

    mock_db = MagicMock()

    def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    with patch("api.main.init_db"):
        with TestClient(app) as c:
            yield c, mock_db
    app.dependency_overrides.clear()


# ── POST /register ─────────────────────────────────────────────────────────────

def test_register_success(client_db):
    client, mock_db = client_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    def fake_refresh(obj):
        obj.id = "member-uuid-1"

    mock_db.refresh.side_effect = fake_refresh

    response = client.post("/register", json={"full_name": "João Silva", "whatsapp": "+5511999999999"})
    assert response.status_code == 200
    assert response.json()["data"]["member_id"] == "member-uuid-1"


def test_register_duplicate_whatsapp(client_db):
    client, mock_db = client_db
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

    response = client.post("/register", json={"full_name": "João", "whatsapp": "+5511999999999"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "WHATSAPP_ALREADY_REGISTERED"


# ── POST /consent ──────────────────────────────────────────────────────────────

def test_consent_success(client_db):
    client, mock_db = client_db
    mock_member = MagicMock()
    mock_member.id = "member-1"
    mock_member.consent_accepted_at = None  # ainda não aceitou
    mock_db.get.return_value = mock_member

    response = client.post("/consent", json={"member_id": "member-1"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["consented"] is True
    mock_db.commit.assert_called_once()


def test_consent_member_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.post("/consent", json={"member_id": "nao-existe"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "MEMBER_NOT_FOUND"


def test_consent_idempotent(client_db):
    """Chamar /consent quando já foi aceito não gera erro nem commit extra."""
    from datetime import datetime, timezone
    client, mock_db = client_db
    mock_member = MagicMock()
    mock_member.id = "member-1"
    mock_member.consent_accepted_at = datetime.now(timezone.utc)  # já aceito
    mock_db.get.return_value = mock_member

    response = client.post("/consent", json={"member_id": "member-1"})
    assert response.status_code == 200
    assert response.json()["data"]["consented"] is True
    mock_db.commit.assert_not_called()


# ── POST /send-code ────────────────────────────────────────────────────────────

def test_send_code_success(client_db):
    client, mock_db = client_db
    mock_member = MagicMock()
    mock_member.id = "member-1"
    mock_member.whatsapp = "+5511999999999"
    mock_db.get.return_value = mock_member

    with patch("api.routes_auth.create_verification_code", return_value="123456"), \
         patch("api.routes_auth.send_whatsapp_code") as mock_send:
        response = client.post("/send-code", json={"member_id": "member-1", "purpose": "register"})

    assert response.status_code == 200
    assert response.json()["data"]["sent"] is True
    mock_send.assert_called_once_with(mock_member.whatsapp, "123456")


def test_send_code_invalid_purpose(client_db):
    client, _ = client_db
    response = client.post("/send-code", json={"member_id": "m-1", "purpose": "invalido"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_PURPOSE"


def test_send_code_member_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.post("/send-code", json={"member_id": "nao-existe", "purpose": "register"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "MEMBER_NOT_FOUND"


# ── POST /confirm-code ─────────────────────────────────────────────────────────

def test_confirm_code_success(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()

    with patch("api.routes_auth.validate_and_use_code"):
        response = client.post(
            "/confirm-code",
            json={"member_id": "member-1", "code": "123456", "purpose": "register"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["confirmed"] is True


def test_confirm_code_invalid_purpose(client_db):
    client, _ = client_db
    response = client.post(
        "/confirm-code",
        json={"member_id": "m-1", "code": "123456", "purpose": "invalido"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_PURPOSE"


def test_confirm_code_member_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.post(
        "/confirm-code",
        json={"member_id": "nao-existe", "code": "123456", "purpose": "download"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "MEMBER_NOT_FOUND"


def test_confirm_code_propagates_invalid_code(client_db):
    """validate_and_use_code levanta INVALID_CODE → rota propaga o erro."""
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()

    with patch(
        "api.routes_auth.validate_and_use_code",
        side_effect=HTTPException(400, {"code": "INVALID_CODE", "message": "Código inválido."}),
    ):
        response = client.post(
            "/confirm-code",
            json={"member_id": "member-1", "code": "000000", "purpose": "download"},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_CODE"
