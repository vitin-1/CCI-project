# CCI — Sistema de Reconhecimento Facial para Eventos

API REST para indexar fotos de evento e permitir que participantes encontrem suas fotos enviando uma selfie.

## Stack

- **InsightFace** (`buffalo_l`) — detecção e geração de embeddings faciais
- **FAISS** (`IndexFlatIP`) — busca vetorial por similaridade
- **FastAPI** — API REST com Swagger UI automático
- **SQLite** — metadados de fotos e rostos
- **Pillow** — geração de previews com marca d'água

## Setup

```bash
# 1. Criar e ativar ambiente virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env e troque ADMIN_TOKEN

# 4. Subir a API
uvicorn api.main:app --reload
```

Acesse a documentação interativa em: http://localhost:8000/docs

## Como indexar fotos

### Via CLI (recomendado para indexação em lote)

```bash
# Indexar uma pasta de fotos
python -m scripts.index_batch /caminho/para/fotos

# Testar sem salvar (dry-run)
python -m scripts.index_batch /caminho/para/fotos --dry-run

# Usar threshold diferente do padrão
python -m scripts.index_batch /caminho/para/fotos --threshold 0.45
```

### Via API (com servidor rodando)

```bash
curl -X POST "http://localhost:8000/upload-batch?folder=/caminho/para/fotos" \
  -H "x-admin-token: changeme"
```

## Como testar a busca

### Via curl

```bash
curl -X POST "http://localhost:8000/search" \
  -F "selfie=@/caminho/para/selfie.jpg"
```

### Via Swagger UI

1. Acesse http://localhost:8000/docs
2. Expanda `POST /search`
3. Clique em "Try it out"
4. Faça upload de uma selfie
5. Execute

### Resposta esperada

```json
{
  "data": {
    "total": 3,
    "results": [
      {
        "photo_id": "uuid-aqui",
        "filename": "foto_001.jpg",
        "preview_url": "/previews/foto_001.jpg",
        "similarity": 0.8734
      }
    ]
  }
}
```

## Resgatar foto original

```bash
curl "http://localhost:8000/photo/{photo_id}/original" \
  -H "x-admin-token: changeme" \
  --output foto_original.jpg
```

## Rodar os testes

```bash
pytest tests/ -v
```

## Estrutura do projeto

```
├── api/
│   ├── main.py              # FastAPI app, CORS, startup
│   ├── routes_search.py     # POST /search
│   └── routes_upload.py     # POST /upload-batch, GET /photo/{id}/original
├── core/
│   ├── detector.py          # InsightFace: detecção + embeddings
│   ├── indexer.py           # FAISS: load/save/add/cache
│   ├── matcher.py           # FAISS: busca por similaridade
│   └── watermark.py         # Pillow: preview com marca d'água
├── db/
│   ├── models.py            # SQLAlchemy: Photo, FaceEntry
│   └── database.py          # Engine, sessão, init_db
├── scripts/
│   └── index_batch.py       # CLI de indexação
├── storage/
│   ├── originals/           # Fotos originais (nunca servidas diretamente pela API pública)
│   └── previews/            # Fotos com watermark (servidas em /previews/)
├── tests/
│   └── core/                # Testes de detector e matcher
├── config.py                # Configurações via variáveis de ambiente
└── requirements.txt
```

## Configuração

| Variável | Padrão | Descrição |
|---|---|---|
| `SIMILARITY_THRESHOLD` | `0.5` | Limiar de similaridade cosine (0–1) |
| `EMBEDDING_TTL_DAYS` | `90` | Dias até expiração dos dados biométricos (LGPD) |
| `ADMIN_TOKEN` | `changeme` | Token para rotas de admin |
| `MAX_IMAGE_SIZE_MB` | `10.0` | Tamanho máximo de imagem aceito |
| `DRY_RUN` | `false` | Processar sem salvar no banco/índice |
| `DB_URL` | SQLite local | URL de conexão do banco |

## Notas de privacidade (LGPD)

- Embeddings faciais são **dados biométricos sensíveis** (Art. 11 LGPD)
- O consentimento para processamento deve ser coletado antes do evento
- Selfies de busca são processadas em memória e nunca armazenadas
- Previews são servidos com marca d'água; fotos originais exigem autenticação
- Todos os dados têm campo `expires_at` (padrão: 90 dias após indexação)
- TODOs pendentes: job de limpeza automática (issue #3), autenticação por participante (issue #1), validação de titularidade no resgate (issue #2)
