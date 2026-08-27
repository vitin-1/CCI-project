from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

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


def test_create_event_requires_admin(client_db):
    client, _ = client_db
    response = client.post("/events", json={"name": "Casamento Silva"})
    assert response.status_code == 422  # header obrigatório ausente


def test_create_event_wrong_token(client_db):
    client, _ = client_db
    response = client.post("/events", headers={"x-admin-token": "errado"}, json={"name": "Casamento"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"


def test_create_event_success(client_db):
    client, mock_db = client_db

    created_event = MagicMock()
    created_event.id = "evt-uuid-1"
    created_event.name = "Formatura Turma 2025"
    created_event.created_at = datetime(2025, 8, 27, tzinfo=timezone.utc)

    mock_db.refresh.side_effect = lambda obj: None

    # db.add não faz nada no mock; simulamos o estado pós-commit via refresh
    def fake_refresh(obj):
        obj.id = created_event.id
        obj.name = created_event.name
        obj.created_at = created_event.created_at

    mock_db.refresh.side_effect = fake_refresh

    response = client.post("/events", headers=ADMIN_HEADERS, json={"name": "Formatura Turma 2025"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == "evt-uuid-1"
    assert data["name"] == "Formatura Turma 2025"


def test_list_events_public(client_db):
    """GET /events é público — não exige x-admin-token."""
    client, mock_db = client_db

    mock_event = MagicMock()
    mock_event.id = "evt-1"
    mock_event.name = "Casamento"
    mock_event.created_at = datetime(2025, 8, 1, tzinfo=timezone.utc)

    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_event]

    response = client.get("/events")  # sem header de admin
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == "evt-1"
    assert data[0]["name"] == "Casamento"


def test_delete_event_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None
    response = client.delete("/events/nao-existe", headers=ADMIN_HEADERS)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "EVENT_NOT_FOUND"


def test_delete_event_success(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()
    response = client.delete("/events/evt-1", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True
