from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from db.models import Base
from config import settings

engine = create_engine(str(settings.db_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    # Habilita a extensão pgvector (idempotente — não falha se já existir)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    # Índice HNSW para busca vetorial eficiente com distância cosine
    # Criado após create_all para garantir que a tabela já existe
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS face_entries_embedding_hnsw "
            "ON face_entries USING hnsw (embedding vector_cosine_ops)"
        ))
        conn.commit()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
