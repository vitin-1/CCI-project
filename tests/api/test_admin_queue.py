"""
Testes HTTP para as rotas de admin (api/routes_admin.py).
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

ADMIN_HEADERS = {"x-admin-token": "changeme"}


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


def _make_report(
    report_id: str = "rep-1",
    photo_id: str = "photo-1",
    member_id: str | None = None,
    reason: str = "Foto inapropriada",
    status: str = "pending",
) -> MagicMock:
    r = MagicMock()
    r.id = report_id
    r.photo_id = photo_id
    r.member_id = member_id
    r.member = None
    r.reason = reason
    r.status = status
    r.created_at.isoformat.return_value = "2025-08-27T00:00:00"
    return r


# ── GET /admin/queue ───────────────────────────────────────────────────────────

def test_queue_requires_admin_token(client_db):
    client, _ = client_db
    response = client.get("/admin/queue")
    assert response.status_code == 422  # header obrigatório ausente


def test_queue_wrong_token(client_db):
    client, _ = client_db
    response = client.get("/admin/queue", headers={"x-admin-token": "errado"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"


def test_queue_returns_pending_reports(client_db):
    client, mock_db = client_db
    from db.models import Photo, ReportedPhoto

    mock_report = _make_report(report_id="rep-1", photo_id="photo-1")
    mock_photo = MagicMock()
    mock_photo.id = "photo-1"
    mock_photo.preview_path = "https://example.com/preview.jpg"

    def mock_query(model):
        q = MagicMock()
        if model is ReportedPhoto:
            q.filter.return_value.order_by.return_value.all.return_value = [mock_report]
        elif model is Photo:
            q.filter.return_value.all.return_value = [mock_photo]
        else:
            q.filter.return_value.all.return_value = []
        return q

    mock_db.query.side_effect = mock_query

    response = client.get("/admin/queue", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["queue"][0]["report_id"] == "rep-1"
    assert data["queue"][0]["preview_url"] == "https://example.com/preview.jpg"
    assert data["queue"][0]["reporter"] is None


def test_queue_report_with_reporter(client_db):
    client, mock_db = client_db
    from db.models import Photo, ReportedPhoto

    mock_member = MagicMock()
    mock_member.full_name = "João Silva"

    mock_report = _make_report(report_id="rep-2", photo_id="photo-2", member_id="member-1")
    mock_report.member = mock_member

    mock_photo = MagicMock()
    mock_photo.id = "photo-2"
    mock_photo.preview_path = "https://example.com/preview2.jpg"

    def mock_query(model):
        q = MagicMock()
        if model is ReportedPhoto:
            q.filter.return_value.order_by.return_value.all.return_value = [mock_report]
        elif model is Photo:
            q.filter.return_value.all.return_value = [mock_photo]
        else:
            q.filter.return_value.all.return_value = []
        return q

    mock_db.query.side_effect = mock_query

    response = client.get("/admin/queue", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    reporter = response.json()["data"]["queue"][0]["reporter"]
    assert reporter is not None
    assert reporter["full_name"] == "João Silva"


def test_queue_empty(client_db):
    client, mock_db = client_db
    from db.models import ReportedPhoto

    def mock_query(model):
        q = MagicMock()
        q.filter.return_value.order_by.return_value.all.return_value = []
        return q

    mock_db.query.side_effect = mock_query

    response = client.get("/admin/queue", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 0


# ── POST /admin/queue/{id}/approve ─────────────────────────────────────────────

def test_approve_report_success(client_db):
    client, mock_db = client_db
    mock_report = _make_report(status="pending")
    mock_db.get.return_value = mock_report

    response = client.post("/admin/queue/rep-1/approve", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "approved"
    assert mock_report.status == "approved"
    assert mock_report.reviewed_at is not None


def test_approve_report_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.post("/admin/queue/nao-existe/approve", headers=ADMIN_HEADERS)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "REPORT_NOT_FOUND"


def test_approve_report_already_reviewed(client_db):
    client, mock_db = client_db
    mock_report = _make_report(status="approved")
    mock_db.get.return_value = mock_report

    response = client.post("/admin/queue/rep-1/approve", headers=ADMIN_HEADERS)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "REPORT_ALREADY_REVIEWED"


# ── POST /admin/queue/{id}/reject ──────────────────────────────────────────────

def test_reject_report_success(client_db):
    client, mock_db = client_db
    mock_report = _make_report(status="pending")
    mock_db.get.return_value = mock_report

    response = client.post("/admin/queue/rep-1/reject", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rejected"
    assert mock_report.status == "rejected"


def test_reject_report_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.post("/admin/queue/nao-existe/reject", headers=ADMIN_HEADERS)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "REPORT_NOT_FOUND"


# ── GET /admin/photo/{id}/original ─────────────────────────────────────────────

def test_admin_get_original_success(client_db):
    client, mock_db = client_db
    mock_photo = MagicMock()
    mock_photo.original_path = "evt-1/photo-1.jpg"
    mock_db.get.return_value = mock_photo

    mock_supa = MagicMock()
    mock_supa.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://example.com/signed"
    }

    with patch("api.routes_admin.get_supabase", return_value=mock_supa):
        response = client.get("/admin/photo/photo-1/original", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json()["data"]["signed_url"] == "https://example.com/signed"


def test_admin_get_original_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.get("/admin/photo/nao-existe/original", headers=ADMIN_HEADERS)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PHOTO_NOT_FOUND"
