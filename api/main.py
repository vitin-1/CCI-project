import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.database import init_db
from api.routes_admin import router as admin_router
from api.routes_auth import router as auth_router
from api.routes_download import router as download_router
from api.routes_events import router as events_router
from api.routes_report import router as report_router
from api.routes_search import router as search_router
from api.routes_upload import router as upload_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria extensão pgvector (se necessário), tabelas e índices no Postgres
    init_db()
    yield


app = FastAPI(
    title="CCI — Reconhecimento Facial de Evento",
    description=(
        "API para indexação e busca de fotos por reconhecimento facial.\n\n"
        "**Privacidade (LGPD)**: selfies de busca nunca são armazenadas. "
        "Fotos originais exigem cadastro, consentimento e verificação via WhatsApp."
    ),
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas de administração
app.include_router(admin_router)
app.include_router(events_router)
app.include_router(upload_router)

# Rotas de participante
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(download_router)
app.include_router(report_router)
