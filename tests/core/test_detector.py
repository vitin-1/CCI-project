import numpy as np
import pytest
from unittest.mock import patch

from core.detector import normalize, extract_largest_face_embedding, detect_faces, EMBEDDING_DIM


def test_normalize_produces_unit_vector():
    vec = np.array([3.0, 4.0], dtype=np.float32)
    result = normalize(vec)
    assert abs(np.linalg.norm(result) - 1.0) < 1e-6


def test_normalize_zero_vector_safe():
    vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
    result = normalize(vec)
    assert np.all(result == 0.0)


def _make_face(area: int) -> dict:
    return {
        "embedding": np.ones(EMBEDDING_DIM, dtype=np.float32) * area,
        "bbox": {"x1": 0, "y1": 0, "x2": area, "y2": area},
    }


def test_extract_largest_face_picks_biggest():
    small = _make_face(50)
    large = _make_face(200)

    with patch("core.detector.detect_faces", return_value=[small, large]):
        dummy = np.zeros((300, 300, 3), dtype=np.uint8)
        result = extract_largest_face_embedding(dummy)

    assert result is not None
    expected = normalize(large["embedding"])
    assert np.allclose(result, expected)


def test_extract_no_face_returns_none():
    with patch("core.detector.detect_faces", return_value=[]):
        dummy = np.zeros((300, 300, 3), dtype=np.uint8)
        result = extract_largest_face_embedding(dummy)
    assert result is None


def test_detect_faces_handles_inference_exception():
    with patch("core.detector.get_model") as mock_model:
        mock_model.return_value.get.side_effect = RuntimeError("onnx error")
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        result = detect_faces(dummy)
    assert result == []
