import logging
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session
from config import settings

logger = logging.getLogger(__name__)


def search_similar_faces(
    query_embedding: np.ndarray,
    db: Session,
    k: int = 20,
    threshold: float | None = None,
) -> list[tuple[str, float]]:
    """
    Busca os `k` embeddings mais próximos de `query_embedding` via pgvector (cosine distance).
    Retorna lista de (photo_id, similarity) filtrada pelo threshold, ordenada por similaridade desc.
    O embedding deve estar normalizado (L2-norm = 1) — para vetores normalizados,
    cosine similarity = inner product, e pgvector <=> (cosine distance) = 1 - similarity.
    """
    min_similarity = threshold if threshold is not None else settings.similarity_threshold

    vec_str = "[" + ",".join(f"{x:.8f}" for x in query_embedding.tolist()) + "]"

    rows = db.execute(
        text("""
            SELECT photo_id,
                   (1.0 - (embedding <=> CAST(:vec AS vector))) AS similarity
            FROM face_entries
            WHERE (1.0 - (embedding <=> CAST(:vec AS vector))) >= :threshold
            ORDER BY embedding <=> CAST(:vec AS vector) ASC
            LIMIT :k
        """),
        {"vec": vec_str, "threshold": float(min_similarity), "k": k},
    ).fetchall()

    return [(row.photo_id, float(row.similarity)) for row in rows]
