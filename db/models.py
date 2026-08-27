import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


# ── Evento ────────────────────────────────────────────────────────────────────

class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    photos: Mapped[list["Photo"]] = relationship("Photo", back_populates="event", cascade="all, delete-orphan")


# ── Participante ──────────────────────────────────────────────────────────────

class Member(Base):
    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    # LGPD: whatsapp é dado pessoal — único por participante
    whatsapp: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    # LGPD: consentimento explícito obrigatório antes de busca ou download (Art. 7 e 11 LGPD)
    consent_accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    codes: Mapped[list["VerificationCode"]] = relationship(
        "VerificationCode", back_populates="member", cascade="all, delete-orphan"
    )
    download_requests: Mapped[list["DownloadRequest"]] = relationship(
        "DownloadRequest", back_populates="member", cascade="all, delete-orphan"
    )


# ── Foto e embedding facial ───────────────────────────────────────────────────

class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String, ForeignKey("events.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    # chave dentro do bucket originals no Supabase Storage
    original_path: Mapped[str] = mapped_column(String, nullable=False)
    # URL pública do preview no bucket previews
    preview_path: Mapped[str] = mapped_column(String, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # LGPD Art. 11 — dado biométrico vinculado; job de limpeza em scripts/cleanup_expired.py
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0)

    event: Mapped["Event"] = relationship("Event", back_populates="photos")
    faces: Mapped[list["FaceEntry"]] = relationship(
        "FaceEntry", back_populates="photo", cascade="all, delete-orphan"
    )
    download_requests: Mapped[list["DownloadRequest"]] = relationship(
        "DownloadRequest", back_populates="photo"
    )
    reports: Mapped[list["ReportedPhoto"]] = relationship(
        "ReportedPhoto", back_populates="photo"
    )


class FaceEntry(Base):
    __tablename__ = "face_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_id: Mapped[str] = mapped_column(String, ForeignKey("photos.id"), nullable=False, index=True)
    # LGPD: embedding é dado biométrico sensível — expirar junto com a foto
    embedding: Mapped[list[float]] = mapped_column(Vector(512), nullable=False)
    bbox: Mapped[dict] = mapped_column(JSON, nullable=False)  # {x1, y1, x2, y2}
    # Indexado para o job de limpeza (WHERE expires_at <= NOW())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    # Reservado para futura vinculação a um Member — não preenchido automaticamente
    member_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("members.id"), nullable=True, index=True
    )

    photo: Mapped["Photo"] = relationship("Photo", back_populates="faces")
    member: Mapped["Member | None"] = relationship("Member")


# ── Verificação de identidade via WhatsApp ────────────────────────────────────

class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id: Mapped[str] = mapped_column(String, ForeignKey("members.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    purpose: Mapped[str] = mapped_column(String, nullable=False)  # "register" | "download"
    # Indexado para limpeza de códigos expirados
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    member: Mapped["Member"] = relationship("Member", back_populates="codes")


# ── Download de foto original ─────────────────────────────────────────────────

class DownloadRequest(Base):
    __tablename__ = "download_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_id: Mapped[str] = mapped_column(String, ForeignKey("photos.id"), nullable=False, index=True)
    member_id: Mapped[str] = mapped_column(String, ForeignKey("members.id"), nullable=False, index=True)
    # "pending_code" → "confirmed" | "expired"
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending_code")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    photo: Mapped["Photo"] = relationship("Photo", back_populates="download_requests")
    member: Mapped["Member"] = relationship("Member", back_populates="download_requests")


# ── Fila de revisão de conteúdo (admin) ──────────────────────────────────────

class ReportedPhoto(Base):
    __tablename__ = "reported_photos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_id: Mapped[str] = mapped_column(String, ForeignKey("photos.id"), nullable=False, index=True)
    # LGPD: denúncias anônimas permitidas — member_id nullable
    member_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("members.id"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(String, nullable=False)
    # "pending" → "approved" | "rejected"
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    photo: Mapped["Photo"] = relationship("Photo", back_populates="reports")
    member: Mapped["Member | None"] = relationship("Member")
