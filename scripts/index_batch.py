#!/usr/bin/env python3
"""
CLI para indexar uma pasta de fotos de evento no Postgres (pgvector) e Supabase Storage.

Uso:
    python -m scripts.index_batch /caminho/para/fotos
    python -m scripts.index_batch /caminho/para/fotos --dry-run
    python -m scripts.index_batch /caminho/para/fotos --threshold 0.45
"""
import argparse
import logging
import mimetypes
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa fotos de uma pasta no Postgres e Supabase Storage.")
    parser.add_argument("folder", help="Caminho da pasta com as fotos do evento")
    parser.add_argument("--dry-run", action="store_true", help="Processa sem salvar no banco/storage")
    parser.add_argument("--threshold", type=float, help="Override do threshold de similaridade")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        logger.error("pasta_nao_encontrada path=%s", folder)
        sys.exit(1)

    from config import settings
    if args.dry_run:
        settings.dry_run = True
    if args.threshold:
        settings.similarity_threshold = args.threshold

    from db.database import init_db, SessionLocal
    from db.models import Photo, FaceEntry
    from db.supabase_client import get_supabase
    from core.detector import detect_faces
    from core.watermark import apply_watermark
    import cv2

    init_db()
    db = SessionLocal()
    supabase = get_supabase()

    photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in _SUPPORTED_EXTENSIONS)
    if not photos:
        logger.warning("nenhuma_foto_encontrada path=%s", folder)
        db.close()
        sys.exit(0)

    logger.info("iniciando_indexacao total=%d folder=%s dry_run=%s", len(photos), folder, settings.dry_run)
    indexed = failed = total_faces = 0

    for i, photo_path in enumerate(photos, 1):
        uploaded: list[tuple[str, str]] = []  # rastro para cleanup em caso de erro
        try:
            img = cv2.imread(str(photo_path))
            if img is None:
                logger.warning("[%d/%d] unreadable photo=%s", i, len(photos), photo_path.name)
                failed += 1
                continue

            faces = detect_faces(img)
            if not faces:
                logger.warning("[%d/%d] no_faces photo=%s", i, len(photos), photo_path.name)

            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.embedding_ttl_days)
            photo_id = str(uuid.uuid4())
            suffix = photo_path.suffix.lower()
            original_key = f"{photo_id}{suffix}"
            preview_key = f"{photo_id}.jpg"
            preview_url = ""

            if not settings.dry_run:
                content_type = mimetypes.guess_type(str(photo_path))[0] or "image/jpeg"
                with open(photo_path, "rb") as f:
                    original_bytes = f.read()
                supabase.storage.from_(settings.supabase_bucket_originals).upload(
                    original_key, original_bytes, {"content-type": content_type}
                )
                uploaded.append((settings.supabase_bucket_originals, original_key))

                preview_bytes = apply_watermark(photo_path)
                if preview_bytes:
                    supabase.storage.from_(settings.supabase_bucket_previews).upload(
                        preview_key, preview_bytes, {"content-type": "image/jpeg"}
                    )
                    uploaded.append((settings.supabase_bucket_previews, preview_key))
                    preview_url = supabase.storage.from_(settings.supabase_bucket_previews).get_public_url(preview_key)

            photo = Photo(
                id=photo_id,
                filename=photo_path.name,
                original_path=original_key,
                preview_path=preview_url,
                expires_at=expires_at,
                face_count=len(faces),
            )
            db.add(photo)
            db.flush()

            if faces and not settings.dry_run:
                for face in faces:
                    db.add(FaceEntry(
                        photo_id=photo.id,
                        embedding=face["embedding"].tolist(),
                        bbox=face["bbox"],
                        expires_at=expires_at,
                    ))
                db.commit()
            elif not settings.dry_run:
                db.commit()
            else:
                db.rollback()

            total_faces += len(faces)
            indexed += 1
            logger.info("[%d/%d] ok photo=%s faces=%d", i, len(photos), photo_path.name, len(faces))

        except Exception:
            logger.exception("[%d/%d] falha photo=%s", i, len(photos), photo_path.name)
            db.rollback()
            for bucket, key in uploaded:
                try:
                    supabase.storage.from_(bucket).remove([key])
                    logger.info("storage_cleanup_ok bucket=%s key=%s", bucket, key)
                except Exception:
                    logger.warning("storage_cleanup_failed bucket=%s key=%s", bucket, key)
            failed += 1

    db.close()
    logger.info(
        "concluido indexed=%d failed=%d total_faces=%d dry_run=%s",
        indexed, failed, total_faces, settings.dry_run,
    )


if __name__ == "__main__":
    main()
