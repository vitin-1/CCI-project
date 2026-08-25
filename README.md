# CCI — Sistema de Reconhecimento Facial para Eventos

API REST para indexar fotos de evento e permitir que participantes encontrem suas fotos enviando uma selfie.

## Stack

- **InsightFace** (`buffalo_l`) — detecção e geração de embeddings faciais
- **pgvector** — busca vetorial por similaridade cosine diretamente no Postgres
- **FastAPI** — API REST com Swagger UI automático
- **Supabase** — Postgres (banco + pgvector) + Storage (fotos originais e previews)
- **Pillow** — geração de previews com marca d'água

---

## Setup do Supabase

### 1. Criar projeto

Acesse [supabase.com](https://supabase.com), crie um novo projeto e anote:
- **Project URL** (ex: `https://abcxyz.supabase.co`)
- **service_role key** — em *Settings → API → Project API keys* (nunca usar a `anon` key no backend)
- **Database connection string** — em *Settings → Database → Connection string → URI*

### 2. Habilitar extensão pgvector

No **SQL Editor** do Supabase, execute:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

A API também executa isso automaticamente no startup via `init_db()`, mas é boa prática habilitar manualmente antes de rodar pela primeira vez.

### 3. Criar os buckets de Storage

Em **Storage** do Dashboard, crie dois buckets:

| Bucket | Visibilidade | Descrição |
|---|---|---|
| `originals` | **Privado** | Fotos originais — acesso só via signed URL (5 min) |
| `previews` | **Público** | Previews com watermark — URL pública permanente |

---

## Setup local

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
# Edite .env com as credenciais do seu projeto Supabase
```

### Variáveis de ambiente obrigatórias

| Variável | Descrição |
|---|---|
| `SUPABASE_URL` | URL do projeto (ex: `https://abcxyz.supabase.co`) |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key do projeto |
| `DB_URL` | Connection string Postgres (formato `postgresql+psycopg2://...`) |
| `ADMIN_TOKEN` | Token para rotas de admin — troque o padrão em produção |

### Variáveis opcionais

| Variável | Padrão | Descrição |
|---|---|---|
| `SIMILARITY_THRESHOLD` | `0.5` | Limiar de similaridade cosine (0–1) |
| `EMBEDDING_TTL_DAYS` | `90` | Dias até expiração dos dados biométricos (LGPD) |
| `SUPABASE_BUCKET_ORIGINALS` | `originals` | Nome do bucket de originais |
| `SUPABASE_BUCKET_PREVIEWS` | `previews` | Nome do bucket de previews |
| `MAX_IMAGE_SIZE_MB` | `10.0` | Tamanho máximo de imagem aceito |
| `DRY_RUN` | `false` | Processar sem salvar no banco/storage |

```bash
# 4. Subir a API
uvicorn api.main:app --reload
```

Acesse a documentação interativa em: http://localhost:8000/docs

---

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

---

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
4. Faça upload de uma selfie e execute

### Resposta esperada

```json
{
  "data": {
    "total": 3,
    "results": [
      {
        "photo_id": "uuid-aqui",
        "filename": "foto_001.jpg",
        "preview_url": "https://abcxyz.supabase.co/storage/v1/object/public/previews/...",
        "similarity": 0.8734
      }
    ]
  }
}
```

---

## Resgatar foto original

Gera uma signed URL com validade de 5 minutos e redireciona para ela.

```bash
curl -L "http://localhost:8000/photo/{photo_id}/original" \
  -H "x-admin-token: changeme" \
  --output foto_original.jpg
```

---

## Rodar os testes

```bash
pytest tests/ -v
```

---

## Estrutura do projeto

```
├── api/
│   ├── main.py              # FastAPI app, CORS, startup
│   ├── routes_search.py     # POST /search
│   └── routes_upload.py     # POST /upload-batch, GET /photo/{id}/original
├── core/
│   ├── detector.py          # InsightFace: detecção + embeddings
│   ├── matcher.py           # pgvector: busca por similaridade cosine
│   └── watermark.py         # Pillow: preview com marca d'água (retorna bytes)
├── db/
│   ├── models.py            # SQLAlchemy: Photo, FaceEntry (embedding vector(512))
│   ├── database.py          # Engine Postgres, sessão, init_db
│   └── supabase_client.py   # Client Supabase singleton (Storage)
├── scripts/
│   └── index_batch.py       # CLI de indexação
├── storage/
│   └── ...                  # Não usado em runtime — Storage agora no Supabase
├── tests/
│   └── core/                # Testes de detector e matcher
├── config.py                # Configurações via variáveis de ambiente
└── requirements.txt
```

---

## Notas de privacidade (LGPD)

- Embeddings faciais são **dados biométricos sensíveis** (Art. 11 LGPD)
- O consentimento para processamento deve ser coletado antes do evento
- Selfies de busca são processadas em memória e nunca armazenadas
- Previews são servidos com marca d'água; fotos originais exigem autenticação e geram signed URL efêmera (5 min)
- Todos os dados têm campo `expires_at` (padrão: 90 dias após indexação)
- TODOs pendentes: job de limpeza automática (issue #3), autenticação por participante (issue #1), validação de titularidade no resgate (issue #2)
