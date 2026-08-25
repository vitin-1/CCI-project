import logging
import numpy as np
import faiss
from config import settings

logger = logging.getLogger(__name__)


def search_similar_faces(
    query_embedding: np.ndarray,
    index: faiss.Index,
    k: int = 20,
    threshold: float | None = None,
) -> list[tuple[int, float]]:
    """
    Busca os `k` embeddings mais próximos de `query_embedding` no índice FAISS.
    Retorna lista de (faiss_id, similarity) filtrada pelo threshold (cosine via inner product).
    Nunca acessa o banco — a resolução de faiss_id → foto é responsabilidade do chamador.
    """
    if index.ntotal == 0:
        return []

    min_similarity = threshold if threshold is not None else settings.similarity_threshold
    query = query_embedding.reshape(1, -1).astype(np.float32)
    distances, indices = index.search(query, min(k, index.ntotal))

    results: list[tuple[int, float]] = []
    for faiss_id, similarity in zip(indices[0], distances[0]):
        if int(faiss_id) == -1:
            continue
        if float(similarity) < min_similarity:
            continue
        results.append((int(faiss_id), float(similarity)))

    return results
