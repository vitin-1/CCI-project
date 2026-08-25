import logging
import numpy as np
import faiss
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 512

_cached_index: faiss.Index | None = None


def load_or_create_index() -> faiss.Index:
    path = settings.faiss_index_path
    if path.exists():
        logger.info("loading_faiss_index path=%s ntotal=%s", path, faiss.read_index(str(path)).ntotal)
        return faiss.read_index(str(path))
    logger.info("creating_new_faiss_index dim=%d", EMBEDDING_DIM)
    return faiss.IndexFlatIP(EMBEDDING_DIM)


def get_index() -> faiss.Index:
    """Retorna índice em cache (carrega do disco na primeira chamada)."""
    global _cached_index
    if _cached_index is None:
        _cached_index = load_or_create_index()
    return _cached_index


def invalidate_index_cache() -> None:
    global _cached_index
    _cached_index = None


def save_index(index: faiss.Index) -> None:
    settings.faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(settings.faiss_index_path))
    logger.info("faiss_index_saved path=%s ntotal=%d", settings.faiss_index_path, index.ntotal)


def add_embeddings(index: faiss.Index, embeddings: list[np.ndarray]) -> list[int]:
    """
    Insere `embeddings` no índice e retorna os faiss_ids atribuídos.
    Os IDs são posicionais (base_id + i), válidos apenas com IndexFlatIP.
    """
    if not embeddings:
        return []
    base_id = index.ntotal
    vectors = np.stack(embeddings).astype(np.float32)
    index.add(vectors)
    return list(range(base_id, base_id + len(embeddings)))
