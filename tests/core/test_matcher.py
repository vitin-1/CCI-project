import numpy as np
import pytest
import faiss
from unittest.mock import MagicMock, patch

from core.detector import normalize, EMBEDDING_DIM
from core.matcher import search_similar_faces


def _make_index(*vecs: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    if vecs:
        index.add(np.stack(vecs).astype(np.float32))
    return index


def _rand_unit() -> np.ndarray:
    v = np.random.rand(EMBEDDING_DIM).astype(np.float32)
    return normalize(v)


def test_empty_index_returns_empty():
    index = _make_index()
    result = search_similar_faces(_rand_unit(), index, threshold=0.5)
    assert result == []


def test_identical_vector_returns_similarity_one():
    vec = _rand_unit()
    index = _make_index(vec)
    matches = search_similar_faces(vec, index, threshold=0.5)
    assert len(matches) == 1
    faiss_id, similarity = matches[0]
    assert faiss_id == 0
    assert abs(similarity - 1.0) < 1e-5


def test_below_threshold_excluded():
    vec_a = _rand_unit()
    # Vetor ortogonal a vec_a via Gram-Schmidt aproximado
    vec_b = _rand_unit()
    vec_b = vec_b - np.dot(vec_b, vec_a) * vec_a
    vec_b = normalize(vec_b)

    index = _make_index(vec_b)
    matches = search_similar_faces(vec_a, index, threshold=0.99)
    assert matches == []


def test_multiple_results_ordered_by_similarity():
    base = _rand_unit()
    # vec_close é mais similar a base do que vec_far
    noise_small = np.random.rand(EMBEDDING_DIM).astype(np.float32) * 0.05
    noise_large = np.random.rand(EMBEDDING_DIM).astype(np.float32) * 0.5
    vec_close = normalize(base + noise_small)
    vec_far = normalize(base + noise_large)

    index = _make_index(vec_close, vec_far)
    matches = search_similar_faces(base, index, threshold=0.0)

    assert len(matches) == 2
    # resultado deve estar em ordem decrescente de similaridade
    assert matches[0][1] >= matches[1][1]
