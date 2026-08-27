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
    event_id: str | None = None,
) -> list[tuple[str, float]]:
    """
    Busca os `k` embeddings mais próximos de `query_embedding` via pgvector (cosine distance).
    Quando `event_id` é fornecido, restringe a busca às fotos daquele evento.
    Retorna lista de (photo_id, similarity) filtrada pelo threshold, ordenada por similaridade desc.
    O embedding deve estar normalizado (L2-norm = 1).
    """
    min_similarity = threshold if threshold is not None else settings.similarity_threshold
    vec_str = "[" + ",".join(f"{x:.8f}" for x in query_embedding.tolist()) + "]"

    if event_id:
        rows = db.execute(
            text("""
                SELECT fe.photo_id,
                       (1.0 - (fe.embedding <=> CAST(:vec AS vector))) AS similarity
                FROM face_entries fe
                JOIN photos p ON p.id = fe.photo_id
                WHERE fe.expires_at > NOW()
                  AND p.event_id = :event_id
                  AND (1.0 - (fe.embedding <=> CAST(:vec AS vector))) >= :threshold
                ORDER BY fe.embedding <=> CAST(:vec AS vector) ASC
                LIMIT :k
            """),
            {"vec": vec_str, "threshold": float(min_similarity), "k": k, "event_id": event_id},
        ).fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT photo_id,
                       (1.0 - (embedding <=> CAST(:vec AS vector))) AS similarity
                FROM face_entries
                WHERE expires_at > NOW()
                  AND (1.0 - (embedding <=> CAST(:vec AS vector))) >= :threshold
                ORDER BY embedding <=> CAST(:vec AS vector) ASC
                LIMIT :k
            """),
            {"vec": vec_str, "threshold": float(min_similarity), "k": k},
        ).fetchall()

    return [(row.photo_id, float(row.similarity)) for row in rows]
