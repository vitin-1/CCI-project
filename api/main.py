import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from db.database import init_db
from api.routes_search import router as search_router
from api.routes_upload import router as upload_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
)

app = FastAPI(
    title="CCI — Reconhecimento Facial de Evento",
    description=(
        "API para indexação e busca de fotos por reconhecimento facial.\n\n"
        "**Privacidade**: selfies de busca nunca são armazenadas. "
        "Fotos originais só são acessíveis via rota de resgate autenticada."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(search_router)


@app.on_event("startup")
async def startup() -> None:
    settings.storage_originals.mkdir(parents=True, exist_ok=True)
    settings.storage_previews.mkdir(parents=True, exist_ok=True)
    init_db()


# Serve previews como arquivos estáticos — nunca servir storage/originals diretamente
app.mount("/previews", StaticFiles(directory=str(settings.storage_previews)), name="previews")
