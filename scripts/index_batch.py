#!/usr/bin/env python3
"""
CLI para indexar uma pasta de fotos de evento no FAISS e banco de dados.

Uso:
    python -m scripts.index_batch /caminho/para/fotos
    python -m scripts.index_batch /caminho/para/fotos --dry-run
    python -m scripts.index_batch /caminho/para/fotos --threshold 0.45
"""
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa fotos de uma pasta no FAISS e banco de dados.")
    parser.add_argument("folder", help="Caminho da pasta com as fotos do evento")
    parser.add_argument("--dry-run", action="store_true", help="Processa sem salvar no banco/índice")
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
    from core.indexer import get_index, save_index, invalidate_index_cache
    from core.detector import detect_faces
    from core.watermark import apply_watermark
    from db.models import Photo, FaceEntry
    from core.indexer import add_embeddings
    import cv2
    import uuid
    from datetime import datetime, timedelta, timezone

    init_db()
    index = get_index()
    db = SessionLocal()

    photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in _SUPPORTED_EXTENSIONS)
    if not photos:
        logger.warning("nenhuma_foto_encontrada path=%s", folder)
        db.close()
        sys.exit(0)

    logger.info("iniciando_indexacao total=%d folder=%s dry_run=%s", len(photos), folder, settings.dry_run)
    indexed = failed = total_faces = 0

    for i, photo_path in enumerate(photos, 1):
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
            preview_path = settings.storage_previews / photo_path.name
            apply_watermark(photo_path, preview_path)

            photo = Photo(
                id=str(uuid.uuid4()),
                filename=photo_path.name,
                original_path=str(photo_path.resolve()),
                preview_path=str(preview_path.resolve()),
                expires_at=expires_at,
                face_count=len(faces),
            )
            db.add(photo)
            db.flush()

            if faces and not settings.dry_run:
                faiss_ids = add_embeddings(index, [f["embedding"] for f in faces])
                for face, faiss_id in zip(faces, faiss_ids):
                    db.add(FaceEntry(
                        photo_id=photo.id,
                        faiss_id=faiss_id,
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
            failed += 1

    if not settings.dry_run:
        save_index(index)
        invalidate_index_cache()

    db.close()
    logger.info(
        "concluido indexed=%d failed=%d total_faces=%d dry_run=%s",
        indexed, failed, total_faces, settings.dry_run,
    )


if __name__ == "__main__":
    main()
