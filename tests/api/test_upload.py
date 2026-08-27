import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

ADMIN_HEADERS = {"x-admin-token": "changeme"}


def _make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(100, 100, 100)).save(buf, "JPEG")
    return buf.getvalue()


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


def test_upload_requires_admin(client_db):
    client, _ = client_db
    response = client.post(
        "/upload",
        params={"event_id": "evt-1"},
        files={"photo": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 422  # header obrigatório ausente


def test_upload_wrong_admin_token(client_db):
    client, _ = client_db
    response = client.post(
        "/upload",
        params={"event_id": "evt-1"},
        headers={"x-admin-token": "errado"},
        files={"photo": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"


def test_upload_event_not_found(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = None  # evento não existe
    response = client.post(
        "/upload",
        params={"event_id": "nao-existe"},
        headers=ADMIN_HEADERS,
        files={"photo": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "EVENT_NOT_FOUND"


def test_upload_unsupported_format(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()  # evento existe
    response = client.post(
        "/upload",
        params={"event_id": "evt-1"},
        headers=ADMIN_HEADERS,
        files={"photo": ("foto.gif", b"GIF89a", "image/gif")},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_FORMAT"


def test_upload_image_too_large(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()
    from config import settings
    original = settings.max_image_size_mb
    settings.max_image_size_mb = 0.00001
    try:
        response = client.post(
            "/upload",
            params={"event_id": "evt-1"},
            headers=ADMIN_HEADERS,
            files={"photo": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "IMAGE_TOO_LARGE"
    finally:
        settings.max_image_size_mb = original


def test_upload_unreadable_image(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()
    with patch("api.routes_upload.index_photo", return_value=None):
        response = client.post(
            "/upload",
            params={"event_id": "evt-1"},
            headers=ADMIN_HEADERS,
            files={"photo": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNREADABLE_IMAGE"


def test_upload_success(client_db):
    client, mock_db = client_db
    mock_db.get.return_value = MagicMock()  # evento existe

    mock_result = MagicMock()
    mock_result.id = "photo-uuid-1"
    mock_result.filename = "test.jpg"
    mock_result.face_count = 2
    mock_result.preview_path = "https://example.com/preview.jpg"

    with patch("api.routes_upload.index_photo", return_value=mock_result):
        response = client.post(
            "/upload",
            params={"event_id": "evt-1"},
            headers=ADMIN_HEADERS,
            files={"photo": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["photo_id"] == "photo-uuid-1"
    assert data["face_count"] == 2
    assert data["preview_url"] == "https://example.com/preview.jpg"
