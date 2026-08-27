"""
Testes HTTP para a rota de denúncia (api/routes_report.py).
"""
from unittest.mock import MagicMock, patch

import pytest


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


def test_report_photo_success(client_db):
    client, mock_db = client_db
    mock_photo = MagicMock()
    mock_db.get.return_value = mock_photo

    def fake_refresh(obj):
        obj.id = "report-uuid-1"

    mock_db.refresh.side_effect = fake_refresh

    response = client.post(
        "/report-photo",
        json={"photo_id": "photo-1", "member_id": "member-1", "reason": "Foto inapropriada"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["report_id"] == "report-uuid-1"


def test_report_photo_anonymous(client_db):
    """Denúncia sem member_id deve ser aceita (LGPD: denúncias anônimas permitidas)."""
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()

    def fake_refresh(obj):
        obj.id = "report-uuid-2"

    mock_db.refresh.side_effect = fake_refresh

    response = client.post(
        "/report-photo",
        json={"photo_id": "photo-1", "reason": "Menor de idade"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["report_id"] == "report-uuid-2"


def test_report_photo_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None

    response = client.post(
        "/report-photo",
        json={"photo_id": "nao-existe", "reason": "Foto ruim"},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PHOTO_NOT_FOUND"
