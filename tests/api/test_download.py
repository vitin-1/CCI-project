"""
Testes HTTP para as rotas de download (api/routes_download.py).
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


def _mock_supabase_signed_url(url: str = "https://example.com/signed") -> MagicMock:
    mock_supa = MagicMock()
    mock_supa.storage.from_.return_value.create_signed_url.return_value = {"signedURL": url}
    return mock_supa


# ── POST /request-download ─────────────────────────────────────────────────────

def test_request_download_success(client_db):
    client, mock_db = client_db

    mock_member = MagicMock()
    mock_member.id = "member-1"
    mock_member.whatsapp = "+5511999999999"

    mock_photo = MagicMock()
    mock_photo.id = "photo-1"

    mock_db.get.return_value = mock_photo

    def fake_refresh(obj):
        obj.id = "req-uuid-1"

    mock_db.refresh.side_effect = fake_refresh

    with patch("api.routes_download.get_consented_member", return_value=mock_member), \
         patch("api.routes_download.create_verification_code", return_value="654321"), \
         patch("api.routes_download.send_whatsapp_code") as mock_send:
        response = client.post(
            "/request-download",
            json={"photo_id": "photo-1", "member_id": "member-1"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["download_request_id"] == "req-uuid-1"
    assert "expires_in_minutes" in data
    mock_send.assert_called_once_with(mock_member.whatsapp, "654321")


def test_request_download_consent_required(client_db):
    client, _ = client_db

    with patch(
        "api.routes_download.get_consented_member",
        side_effect=HTTPException(403, {"code": "CONSENT_REQUIRED", "message": "..."}),
    ):
        response = client.post(
            "/request-download",
            json={"photo_id": "photo-1", "member_id": "sem-consentimento"},
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "CONSENT_REQUIRED"


def test_request_download_member_not_found(client_db):
    client, _ = client_db

    with patch(
        "api.routes_download.get_consented_member",
        side_effect=HTTPException(404, {"code": "MEMBER_NOT_FOUND", "message": "..."}),
    ):
        response = client.post(
            "/request-download",
            json={"photo_id": "photo-1", "member_id": "nao-existe"},
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "MEMBER_NOT_FOUND"


def test_request_download_photo_not_found(client_db):
    client, mock_db = client_db

    mock_member = MagicMock()
    mock_db.get.return_value = None  # foto não existe

    with patch("api.routes_download.get_consented_member", return_value=mock_member):
        response = client.post(
            "/request-download",
            json={"photo_id": "nao-existe", "member_id": "member-1"},
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PHOTO_NOT_FOUND"


# ── POST /confirm-download ─────────────────────────────────────────────────────

def test_confirm_download_success(client_db):
    client, mock_db = client_db
    from db.models import DownloadRequest, Photo

    mock_req = MagicMock()
    mock_req.status = "pending_code"
    mock_req.member_id = "member-1"
    mock_req.photo_id = "photo-1"
    mock_req.id = "req-1"

    mock_photo = MagicMock()
    mock_photo.original_path = "evt-1/photo-1.jpg"

    def db_get(model, id):
        if model is DownloadRequest:
            return mock_req
        if model is Photo:
            return mock_photo
        return None

    mock_db.get.side_effect = db_get

    with patch("api.routes_download.validate_and_use_code"), \
         patch("api.routes_download.get_supabase", return_value=_mock_supabase_signed_url()):
        response = client.post(
            "/confirm-download",
            json={"download_request_id": "req-1", "code": "654321"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["signed_url"] == "https://example.com/signed"
    assert data["expires_in_seconds"] == 300
    assert mock_req.status == "confirmed"


def test_confirm_download_request_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.post(
        "/confirm-download",
        json={"download_request_id": "nao-existe", "code": "123456"},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "REQUEST_NOT_FOUND"


def test_confirm_download_already_processed(client_db):
    client, mock_db = client_db

    mock_req = MagicMock()
    mock_req.status = "confirmed"  # já processado
    mock_db.get.return_value = mock_req

    response = client.post(
        "/confirm-download",
        json={"download_request_id": "req-1", "code": "123456"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "REQUEST_ALREADY_PROCESSED"


def test_confirm_download_invalid_code(client_db):
    client, mock_db = client_db
    from db.models import DownloadRequest

    mock_req = MagicMock()
    mock_req.status = "pending_code"
    mock_req.member_id = "member-1"
    mock_db.get.return_value = mock_req

    with patch(
        "api.routes_download.validate_and_use_code",
        side_effect=HTTPException(400, {"code": "INVALID_CODE", "message": "Código inválido."}),
    ):
        response = client.post(
            "/confirm-download",
            json={"download_request_id": "req-1", "code": "000000"},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_CODE"
