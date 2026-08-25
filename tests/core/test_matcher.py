import numpy as np
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from core.matcher import search_similar_faces

# Constantes definidas localmente para evitar import pesado de insightface
EMBEDDING_DIM = 512


def _normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    return v / norm if norm > 0.0 else v


def _rand_unit() -> np.ndarray:
    v = np.random.rand(EMBEDDING_DIM).astype(np.float32)
    return _normalize(v)


def _mock_db(*rows: tuple[str, float]) -> Session:
    """Cria um mock de Session cujo execute retorna as linhas dadas."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        MagicMock(photo_id=photo_id, similarity=similarity)
        for photo_id, similarity in rows
    ]
    db = MagicMock(spec=Session)
    db.execute.return_value = mock_result
    return db


def test_empty_index_returns_empty():
    # Quando não há linhas no banco a query retorna vazio
    db = _mock_db()
    result = search_similar_faces(_rand_unit(), db, threshold=0.5)
    assert result == []


def test_identical_vector_returns_similarity_one():
    # Banco retorna similarity=1.0 para embedding idêntico — função deve repassar
    db = _mock_db(("photo-uuid-1", 1.0))
    matches = search_similar_faces(_rand_unit(), db, threshold=0.5)
    assert len(matches) == 1
    photo_id, similarity = matches[0]
    assert isinstance(photo_id, str)
    assert abs(similarity - 1.0) < 1e-5


def test_below_threshold_excluded():
    # SQL filtra pelo WHERE — banco retorna vazio quando nada passa no threshold
    db = _mock_db()
    matches = search_similar_faces(_rand_unit(), db, threshold=0.99)
    assert matches == []


def test_multiple_results_ordered_by_similarity():
    # SQL ordena pelo ORDER BY — função deve preservar a ordem retornada pelo banco
    db = _mock_db(("photo-a", 0.95), ("photo-b", 0.72))
    matches = search_similar_faces(_rand_unit(), db, threshold=0.0)
    assert len(matches) == 2
    assert matches[0][1] >= matches[1][1]
