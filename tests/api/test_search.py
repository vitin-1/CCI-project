import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

EMBEDDING_DIM = 512


def _make_jpeg_bytes(width: int = 100, height: int = 100) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(128, 128, 128)).save(buf, "JPEG")
    return buf.getvalue()


def _rand_unit() -> np.ndarray:
    v = np.random.rand(EMBEDDING_DIM).astype(np.float32)
    return v / np.linalg.norm(v)


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


def test_image_too_large(client_db):
    client, _ = client_db
    from config import settings
    original = settings.max_image_size_mb
    settings.max_image_size_mb = 0.00001  # ~10 bytes — qualquer JPEG passa disso
    try:
        response = client.post(
            "/search",
            params={"event_id": "evt-1", "member_id": "member-1"},
            files={"selfie": ("selfie.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "IMAGE_TOO_LARGE"
    finally:
        settings.max_image_size_mb = original


def test_invalid_image_bytes(client_db):
    client, _ = client_db
    with patch("api.routes_search.cv2.imdecode", return_value=None):
        response = client.post(
            "/search",
            params={"event_id": "evt-1", "member_id": "member-1"},
            files={"selfie": ("selfie.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_IMAGE"


def test_no_face_detected(client_db):
    client, _ = client_db
    with patch("api.routes_search.extract_largest_face_embedding", return_value=None):
        response = client.post(
            "/search",
            params={"event_id": "evt-1", "member_id": "member-1"},
            files={"selfie": ("selfie.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "NO_FACE_DETECTED"


def test_search_returns_results(client_db):
    client, mock_db = client_db
    photo_id = "photo-uuid-1"

    mock_photo = MagicMock()
    mock_photo.id = photo_id
    mock_photo.filename = "foto.jpg"
    mock_photo.preview_path = "https://example.com/preview.jpg"
    mock_photo.event_id = "evt-1"
    mock_photo.event.name = "Evento Teste"
    mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [mock_photo]

    with patch("api.routes_search.extract_largest_face_embedding", return_value=_rand_unit()), \
         patch("api.routes_search.search_similar_faces", return_value=[(photo_id, 0.92)]):
        response = client.post(
            "/search",
            params={"event_id": "evt-1", "member_id": "member-1"},
            files={"selfie": ("selfie.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["results"][0]["photo_id"] == photo_id
    assert data["results"][0]["similarity"] == 0.92
    assert data["results"][0]["preview_url"] == "https://example.com/preview.jpg"
    assert data["results"][0]["event_name"] == "Evento Teste"


def test_search_no_matches(client_db):
    client, _ = client_db
    with patch("api.routes_search.extract_largest_face_embedding", return_value=_rand_unit()), \
         patch("api.routes_search.search_similar_faces", return_value=[]):
        response = client.post(
            "/search",
            params={"event_id": "evt-1", "member_id": "member-1"},
            files={"selfie": ("selfie.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["results"] == []


def test_search_deduplicates_same_photo(client_db):
    """Mesmo photo_id retornado duas vezes (rostos diferentes) deve aparecer uma vez no resultado."""
    client, mock_db = client_db
    photo_id = "photo-uuid-dup"

    mock_photo = MagicMock()
    mock_photo.id = photo_id
    mock_photo.filename = "group.jpg"
    mock_photo.preview_path = "https://example.com/group.jpg"
    mock_photo.event_id = "evt-1"
    mock_photo.event.name = "Evento Teste"
    mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [mock_photo]

    with patch("api.routes_search.extract_largest_face_embedding", return_value=_rand_unit()), \
         patch("api.routes_search.search_similar_faces", return_value=[(photo_id, 0.95), (photo_id, 0.80)]):
        response = client.post(
            "/search",
            params={"event_id": "evt-1", "member_id": "member-1"},
            files={"selfie": ("selfie.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1
