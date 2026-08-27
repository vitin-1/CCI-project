# CCI — Sistema de Reconhecimento Facial para Eventos

API REST para indexar fotos de evento e permitir que participantes encontrem e baixem suas fotos enviando uma selfie.

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

A API também executa isso automaticamente no startup via `init_db()`.

### 3. Criar os buckets de Storage

Em **Storage** do Dashboard, crie dois buckets:

| Bucket | Visibilidade | Descrição |
|---|---|---|
| `originals` | **Privado** | Fotos originais — acesso via signed URL (5 min) |
| `previews` | **Público** | Previews com watermark — URL pública permanente |

---

## Setup local

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
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
| `SECRET_KEY` | Chave para assinar tokens — gere com `python -c "import secrets; print(secrets.token_hex(32))"` |

### Variáveis opcionais

| Variável | Padrão | Descrição |
|---|---|---|
| `SIMILARITY_THRESHOLD` | `0.40` | Limiar de similaridade cosine (calibrado para buffalo_l) |
| `EMBEDDING_TTL_DAYS` | `90` | Dias até expiração dos dados biométricos (LGPD) |
| `CODE_TTL_MINUTES` | `5` | Validade do código de verificação WhatsApp |
| `MAX_IMAGE_SIZE_MB` | `10.0` | Tamanho máximo de imagem aceito |
| `DRY_RUN` | `false` | Processar sem salvar no banco/storage |

```bash
uvicorn api.main:app --reload
```

Acesse a documentação interativa em: http://localhost:8000/docs

---

## Fluxo do participante

```
1. POST /register          → cadastra nome + WhatsApp
2. POST /consent           → aceite LGPD (obrigatório antes de buscar)
3. POST /search            → envia selfie → recebe galeria com previews
4. POST /request-download  → solicita download de uma foto → código enviado via WhatsApp
5. POST /confirm-download  → informa o código → recebe signed URL da foto original (5 min)
```

Para denunciar uma foto: `POST /report-photo` (não exige login).

---

## Endpoints de participante

### Cadastro e autenticação

```bash
# 1. Cadastrar
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"full_name": "João Silva", "whatsapp": "+5511999999999"}'
# → {"data": {"member_id": "uuid..."}}

# 2. Aceitar consentimento LGPD
curl -X POST http://localhost:8000/consent \
  -H "Content-Type: application/json" \
  -d '{"member_id": "uuid..."}'

# 3. Enviar código de verificação (WhatsApp)
curl -X POST http://localhost:8000/send-code \
  -H "Content-Type: application/json" \
  -d '{"member_id": "uuid...", "purpose": "register"}'

# 4. Confirmar código
curl -X POST http://localhost:8000/confirm-code \
  -H "Content-Type: application/json" \
  -d '{"member_id": "uuid...", "code": "123456", "purpose": "register"}'
```

### Busca por selfie

```bash
curl -X POST "http://localhost:8000/search?event_id=EVT_ID&member_id=MBR_ID" \
  -F "selfie=@/caminho/para/selfie.jpg"
```

**Resposta:**
```json
{
  "data": {
    "total": 3,
    "results": [
      {
        "photo_id": "uuid...",
        "filename": "foto_001.jpg",
        "preview_url": "https://...supabase.co/storage/v1/object/public/previews/...",
        "similarity": 0.8734
      }
    ]
  }
}
```

### Download da foto original

```bash
# 1. Solicitar download → código enviado por WhatsApp
curl -X POST http://localhost:8000/request-download \
  -H "Content-Type: application/json" \
  -d '{"photo_id": "uuid...", "member_id": "uuid..."}'
# → {"data": {"download_request_id": "uuid...", "expires_in_minutes": 5}}

# 2. Confirmar com o código recebido → receber signed URL (válida 5 min)
curl -X POST http://localhost:8000/confirm-download \
  -H "Content-Type: application/json" \
  -d '{"download_request_id": "uuid...", "code": "123456"}'
# → {"data": {"signed_url": "https://...", "expires_in_seconds": 300}}
```

### Denunciar foto

```bash
curl -X POST http://localhost:8000/report-photo \
  -H "Content-Type: application/json" \
  -d '{"photo_id": "uuid...", "reason": "Foto com menor de idade"}'
# → {"data": {"report_id": "uuid..."}}
```

---

## Endpoints de admin

Todos exigem o header `x-admin-token`.

### Gerenciar eventos e fotos

```bash
# Criar evento
curl -X POST http://localhost:8000/events \
  -H "x-admin-token: changeme" \
  -H "Content-Type: application/json" \
  -d '{"name": "Formatura Turma 2025"}'
# → {"data": {"id": "EVT_ID", "name": "...", "created_at": "..."}}

# Listar eventos
curl http://localhost:8000/events -H "x-admin-token: changeme"

# Indexar uma foto (via HTTP)
curl -X POST "http://localhost:8000/upload?event_id=EVT_ID" \
  -H "x-admin-token: changeme" \
  -F "photo=@foto.jpg"

# Indexar pasta inteira (via CLI — recomendado para lotes grandes)
python -m scripts.index_batch /caminho/para/fotos --event-id EVT_ID
python -m scripts.index_batch /caminho/para/fotos --event-id EVT_ID --dry-run
```

### Fila de denúncias

```bash
# Ver fila pendente
curl http://localhost:8000/admin/queue -H "x-admin-token: changeme"

# Aprovar denúncia
curl -X POST http://localhost:8000/admin/queue/REPORT_ID/approve \
  -H "x-admin-token: changeme"

# Rejeitar denúncia
curl -X POST http://localhost:8000/admin/queue/REPORT_ID/reject \
  -H "x-admin-token: changeme"

# Acessar foto original diretamente (fallback admin)
curl http://localhost:8000/admin/photo/PHOTO_ID/original \
  -H "x-admin-token: changeme"
```

---

## Manutenção (LGPD)

```bash
# Remover embeddings e fotos expirados (rodar periodicamente como cron)
python -m scripts.cleanup_expired

# Simular sem deletar
python -m scripts.cleanup_expired --dry-run
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
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── dependencies.py      # require_admin (header x-admin-token)
│   ├── routes_admin.py      # GET /admin/queue, approve/reject, GET /admin/photo/{id}/original
│   ├── routes_auth.py       # POST /register, /consent, /send-code, /confirm-code
│   ├── routes_download.py   # POST /request-download, /confirm-download
│   ├── routes_events.py     # POST/GET/DELETE /events
│   ├── routes_report.py     # POST /report-photo
│   ├── routes_search.py     # POST /search
│   └── routes_upload.py     # POST /upload-batch, /upload
├── core/
│   ├── detector.py          # InsightFace: detecção + embeddings
│   ├── matcher.py           # pgvector: busca por similaridade cosine
│   ├── notifications.py     # send_whatsapp_code (TODO: plugar provedor real)
│   └── watermark.py         # Pillow: preview com marca d'água
├── db/
│   ├── models.py            # Event, Member, Photo, FaceEntry, VerificationCode, DownloadRequest, ReportedPhoto
│   ├── database.py          # Engine Postgres lazy, sessão, init_db
│   ├── supabase_client.py   # Client Supabase singleton (Storage)
│   └── repositories/
│       ├── photo_repo.py    # index_photo — lógica de indexação compartilhada
│       └── member_repo.py   # get_consented_member, create_verification_code, validate_and_use_code
├── scripts/
│   ├── index_batch.py       # CLI de indexação em lote (--event-id obrigatório)
│   └── cleanup_expired.py   # LGPD: remove embeddings e fotos expirados
├── tests/
│   ├── api/                 # Testes HTTP das rotas (TestClient + mocks)
│   └── core/                # Testes unitários de detector, matcher, watermark, auth
├── config.py                # Configurações via variáveis de ambiente
└── requirements.txt
```

---

## Notas de privacidade (LGPD)

- Embeddings faciais são **dados biométricos sensíveis** (Art. 11 LGPD)
- **Consentimento explícito** é coletado via `POST /consent` antes de qualquer busca ou download
- Selfies de busca são processadas em memória e **nunca armazenadas**
- Fotos originais são acessíveis somente após verificação de identidade por código WhatsApp
- Previews têm marca d'água; originais geram signed URL efêmera (5 min)
- Todos os dados biométricos têm `expires_at` (padrão: 90 dias) — removidos por `cleanup_expired.py`
- Denúncias de fotos podem ser anônimas (`member_id` opcional em `/report-photo`)
