import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from db.database import get_db
from db.models import Event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    name: str


@router.get("")
def list_events(db: Session = Depends(get_db)) -> dict:
    """Lista todos os eventos (público — usado pelo app para exibir cards de eventos)."""
    events = db.query(Event).order_by(Event.created_at.desc()).all()
    return {
        "data": [
            {"id": e.id, "name": e.name, "created_at": e.created_at.isoformat()}
            for e in events
        ]
    }


@router.post("", dependencies=[Depends(require_admin)])
def create_event(body: EventCreate, db: Session = Depends(get_db)) -> dict:
    """Cria um evento (admin-only). O event_id retornado é usado nas rotas de upload e busca."""
    event = Event(name=body.name)
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info("event_created id=%s name=%s", event.id, event.name)
    return {"data": {"id": event.id, "name": event.name, "created_at": event.created_at.isoformat()}}


@router.delete("/{event_id}", dependencies=[Depends(require_admin)])
def delete_event(event_id: str, db: Session = Depends(get_db)) -> dict:
    """Remove um evento e todas as suas fotos e embeddings (admin-only)."""
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": "Evento não encontrado."},
        )
    db.delete(event)
    db.commit()
    logger.info("event_deleted id=%s", event_id)
    return {"data": {"deleted": True}}
