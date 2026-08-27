#!/usr/bin/env python3
"""
Remove embeddings e fotos com expires_at no passado.
Cobre obrigação LGPD Art. 11 — dado biométrico não pode ser retido além do prazo.

Uso:
    python -m scripts.cleanup_expired
    python -m scripts.cleanup_expired --dry-run
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove dados biométricos expirados (LGPD Art. 11).")
    parser.add_argument("--dry-run", action="store_true", help="Conta sem deletar")
    args = parser.parse_args()

    from config import settings
    from db.database import init_db, get_session
    from db.models import DownloadRequest, FaceEntry, Photo
    from db.supabase_client import get_supabase

    init_db()
    db = get_session()

    try:
        now = datetime.now(timezone.utc)

        expired_photos = db.query(Photo).filter(Photo.expires_at <= now).all()
        expired_embeddings_q = db.query(FaceEntry).filter(FaceEntry.expires_at <= now)
        count_embeddings = expired_embeddings_q.count()

        # DownloadRequests que ficaram presos em pending_code além do TTL do código
        stale_cutoff = now - timedelta(minutes=settings.code_ttl_minutes)
        stale_requests_q = db.query(DownloadRequest).filter(
            DownloadRequest.status == "pending_code",
            DownloadRequest.created_at <= stale_cutoff,
        )
        count_stale_requests = stale_requests_q.count()

        logger.info(
            "expirados_encontrados photos=%d embeddings=%d stale_requests=%d dry_run=%s",
            len(expired_photos), count_embeddings, count_stale_requests, args.dry_run,
        )

        if args.dry_run:
            logger.info("dry_run — nenhum dado removido")
            return

        # Expira requests presos
        expired_req_count = stale_requests_q.delete(synchronize_session=False)
        if expired_req_count:
            logger.info("stale_requests_expired count=%d", expired_req_count)

        # Remove arquivos do Supabase Storage (best-effort — não bloqueia a limpeza do banco)
        if expired_photos:
            supabase = get_supabase()
            original_keys = [p.original_path for p in expired_photos if p.original_path]
            # preview_path armazena URL pública; a chave no bucket é sempre "{photo.id}.jpg"
            preview_keys = [f"{p.id}.jpg" for p in expired_photos]

            if original_keys:
                try:
                    supabase.storage.from_(settings.supabase_bucket_originals).remove(original_keys)
                    logger.info("storage_originals_removed count=%d", len(original_keys))
                except Exception:
                    logger.warning("storage_originals_remove_failed — continuando limpeza do banco")

            if preview_keys:
                try:
                    supabase.storage.from_(settings.supabase_bucket_previews).remove(preview_keys)
                    logger.info("storage_previews_removed count=%d", len(preview_keys))
                except Exception:
                    logger.warning("storage_previews_remove_failed — continuando limpeza do banco")

        # Remove do banco (cascade apaga FaceEntry junto com Photo)
        for photo in expired_photos:
            db.delete(photo)

        # Remove embeddings órfãos que possam ter ficado sem foto associada
        orphan_count = expired_embeddings_q.delete(synchronize_session=False)

        db.commit()
        logger.info(
            "limpeza_concluida photos_deletadas=%d embeddings_deletados=%d stale_requests=%d",
            len(expired_photos), orphan_count, expired_req_count,
        )

    except Exception:
        logger.exception("cleanup_failed")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
