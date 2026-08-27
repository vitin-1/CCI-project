#!/usr/bin/env python3
"""
CLI para indexar uma pasta de fotos de evento no Postgres (pgvector) e Supabase Storage.

Uso:
    python -m scripts.index_batch /caminho/para/fotos --event-id <uuid>
    python -m scripts.index_batch /caminho/para/fotos --event-id <uuid> --dry-run
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
    parser = argparse.ArgumentParser(description="Indexa fotos de uma pasta no Postgres e Supabase Storage.")
    parser.add_argument("folder", help="Caminho da pasta com as fotos do evento")
    parser.add_argument("--event-id", required=True, help="ID do evento ao qual as fotos pertencem")
    parser.add_argument("--dry-run", action="store_true", help="Processa sem salvar no banco/storage")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        logger.error("pasta_nao_encontrada path=%s", folder)
        sys.exit(1)

    from config import settings
    if args.dry_run:
        settings.dry_run = True

    from db.database import init_db, get_session
    from db.models import Event
    from db.repositories.photo_repo import index_photo

    init_db()
    db = get_session()

    event = db.get(Event, args.event_id)
    if event is None:
        logger.error("evento_nao_encontrado event_id=%s", args.event_id)
        db.close()
        sys.exit(1)

    photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in _SUPPORTED_EXTENSIONS)
    if not photos:
        logger.warning("nenhuma_foto_encontrada path=%s", folder)
        db.close()
        sys.exit(0)

    logger.info(
        "iniciando_indexacao total=%d folder=%s event_id=%s dry_run=%s",
        len(photos), folder, args.event_id, settings.dry_run,
    )
    indexed = failed = total_faces = 0

    for i, photo_path in enumerate(photos, 1):
        try:
            result = index_photo(photo_path, args.event_id, db)
            if result is not None:
                total_faces += result.face_count
                indexed += 1
                logger.info("[%d/%d] ok photo=%s faces=%d", i, len(photos), photo_path.name, result.face_count)
            else:
                logger.warning("[%d/%d] unreadable photo=%s", i, len(photos), photo_path.name)
                failed += 1
        except Exception:
            logger.exception("[%d/%d] falha photo=%s", i, len(photos), photo_path.name)
            db.rollback()
            failed += 1

    db.close()
    logger.info(
        "concluido indexed=%d failed=%d total_faces=%d dry_run=%s",
        indexed, failed, total_faces, settings.dry_run,
    )


if __name__ == "__main__":
    main()
