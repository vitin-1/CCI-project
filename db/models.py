import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String, nullable=False)
    # path dentro do bucket originals no Supabase Storage
    original_path: Mapped[str] = mapped_column(String, nullable=False)
    # URL pública do preview no bucket previews do Supabase Storage
    preview_path: Mapped[str] = mapped_column(String, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # LGPD: dado biométrico vinculado — expiração obrigatória (Art. 11)
    # TODO(lgpd): implementar job de limpeza automática — issue #3
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0)

    faces: Mapped[list["FaceEntry"]] = relationship(
        "FaceEntry", back_populates="photo", cascade="all, delete-orphan"
    )


class FaceEntry(Base):
    __tablename__ = "face_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_id: Mapped[str] = mapped_column(String, ForeignKey("photos.id"), nullable=False, index=True)
    # Embedding facial 512-d armazenado direto no Postgres via pgvector — substitui faiss_id
    embedding: Mapped[list[float]] = mapped_column(Vector(512), nullable=False)
    bbox: Mapped[dict] = mapped_column(JSON, nullable=False)  # {x1, y1, x2, y2}
    # LGPD: embedding é dado biométrico sensível — expirar junto com a foto
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    photo: Mapped["Photo"] = relationship("Photo", back_populates="faces")
