from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from db.models import Base
from config import settings

_engine: Engine | None = None
_SessionLocal = None


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(str(settings.db_url))
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


def get_session() -> Session:
    """Para uso em scripts CLI — retorna uma Session que o chamador deve fechar."""
    return _get_session_factory()()


def init_db() -> None:
    engine = _get_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        # Índice HNSW para busca vetorial eficiente (cosine)
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS face_entries_embedding_hnsw "
            "ON face_entries USING hnsw (embedding vector_cosine_ops)"
        ))
        # Índice para o job de limpeza LGPD (WHERE expires_at <= NOW())
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS face_entries_expires_at_idx "
            "ON face_entries (expires_at)"
        ))
        conn.commit()


def get_db():
    db: Session = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()
