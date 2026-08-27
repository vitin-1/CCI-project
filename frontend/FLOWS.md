# CCI Aliança — Especificação de Fluxos Frontend

> Referência de manutenção. Atualizar sempre que adicionar ou alterar telas.
> Build: `npm run build` | Testes backend: `pytest tests/ -q`

---

## Índice de arquivos

| Arquivo | Fluxo | Papel |
|---|---|---|
| `src/screens/SplashScreen.jsx` | Onboarding | Logo inicial; redireciona por sessão |
| `src/screens/WelcomeScreen.jsx` | Onboarding | Boas-vindas; porta de entrada |
| `src/screens/HowItWorksScreen.jsx` | Onboarding | Tutorial em 6 passos |
| `src/screens/RegisterScreen.jsx` | Onboarding | Cadastro nome + WhatsApp |
| `src/screens/ConsentScreen.jsx` | Onboarding | LGPD; consent obrigatório |
| `src/screens/ChooseOptionScreen.jsx` | Busca | Câmera ou galeria |
| `src/screens/CaptureScreen.jsx` | Busca | Câmera frontal; captura selfie |
| `src/screens/ProcessingScreen.jsx` | Busca | POST /search; estados de carregamento |
| `src/screens/SuccessScreen.jsx` | Busca | Confirmação com confetti |
| `src/screens/ResultsScreen.jsx` | Resultados | Grid; abas Todos/Eventos/Favoritos |
| `src/screens/PhotoDetailScreen.jsx` | Resultados | Detalhe; download OTP + denúncia |
| `src/screens/MyPhotosScreen.jsx` | Minha área | Fotos salvas; filtrável por evento |
| `src/screens/EventsScreen.jsx` | Minha área | Lista GET /events |
| `src/screens/ProfileScreen.jsx` | Minha área | Stats + logout |
| `src/screens/admin/AdminLoginScreen.jsx` | Admin | Login via token |
| `src/screens/admin/AdminQueueScreen.jsx` | Admin | Fila de denúncias |
| `src/screens/admin/AdminCaseScreen.jsx` | Admin | Aprovar / rejeitar caso |
| `src/context/AppContext.jsx` | Global | Estado global + reducer |
| `src/api/client.js` | Global | Todas as chamadas HTTP |
| `src/components/BottomNav.jsx` | Global | Nav inferior 5 abas |
| `src/components/Toast.jsx` | Global | Notificação temporária |
| `src/components/Confetti.jsx` | Global | Animação de celebração |
| `src/App.jsx` | Global | Roteamento + layouts |

---

## Fluxo 1 — Onboarding (novo usuário)

```
[*] ──► /splash (2.2s)
            ├── memberId em sessionStorage ──► /
            └── sem sessão ──────────────────► /welcome
                                                  ├── "Vamos Começar" ──────► /register
                                                  └── "Como funciona?" ──────► /how-it-works
                                                                                    └── "Começar agora" ──► /register
/register ──► POST /register ──► /consent
/consent  ──► POST /consent  ──► /choose   (início da busca)
```

### Etapa 1 — SplashScreen (`/splash`)
- Logo animado (zoom + fade)
- Timer 2,2 s → redireciona automaticamente
- Rota `*` (404) também cai aqui

### Etapa 2 — WelcomeScreen (`/welcome`)
- **Guard**: se `hasAuth` → redireciona para `/` (App.jsx, linha do Route)
- Ilustração de celular com scan line animado
- Dois botões de saída: `/register` e `/how-it-works`

### Etapa 3 — HowItWorksScreen (`/how-it-works`)
- Sem guard de autenticação (informativo; acessível sempre)
- 6 passos com animação stagger (`animationDelay: 0.08 * i`)
- "Começar agora" → `/register`
- Voltar → `navigate(-1)`

### Etapa 4 — RegisterScreen (`/register`)
- **Guard**: se `hasAuth` → `/` (App.jsx)
- Validação local: nome ≥ 2 chars; WhatsApp formatado `+55DDXXXXXXXXX` (≥ 12 dígitos brutos)
- `POST /register { full_name, whatsapp }` → dispatch `SET_MEMBER` → `/consent`
- Erro `WHATSAPP_ALREADY_REGISTERED` → mensagem inline (não lança toast)

### Etapa 5 — ConsentScreen (`/consent`)
- **Guard interno**: `useEffect → if (!memberId) navigate('/register')` — evita acesso direto sem sessão
- Checkbox obrigatório antes de habilitar o botão
- `POST /consent { member_id }` (idempotente — atualiza `consent_accepted_at`)
- Sucesso → `/choose`
- Também acessível via ProfileScreen para re-consent

---

## Fluxo 2 — Busca de fotos

```
/choose ─── "Tirar uma Foto" ──────────────► /capture
        └── "Enviar da Galeria" (file input) ─┐
                                              ▼
                                         /processing
                                              │
                              ┌───────────────┼───────────────┐
                        fotos encontradas   vazio    erro / NO_FACE
                              │               │               │
                          /success      / (empty:true)   tela de erro
                              │
                    "Ver minhas fotos" → /
                    "Ver eventos"      → /events
```

### Etapa 6 — ChooseOptionScreen (`/choose`)
- Dentro do **FlowLayout** (requer `memberId`)
- "Tirar uma Foto" → `/capture`
- "Enviar da Galeria" → clica em `<input ref={fileRef}>` oculto → `handleFileSelect` → `/processing` com `state.selfie = File`
- File é um objeto `File` (estruturalmente clonável pelo React Router)
- Voltar → `navigate(-1)`

### Etapa 7 — CaptureScreen (`/capture`)
- `getUserMedia({ facingMode: 'user', width: 720, height: 720 })`
- **Cleanup obrigatório**: `return () => streamRef.current?.getTracks().forEach(t => t.stop())` — libera câmera ao sair
- Canvas crop: extrai quadrado centralizado do frame do vídeo (evita distorção)
- `canvas.toBlob(blob, 'image/jpeg', 0.92)` → `/processing` com `state.selfie = Blob`
- Estado `denied`: exibe fallback "Câmera bloqueada" + link para galeria

### Etapa 8 — ProcessingScreen (`/processing`)
- **Guard StrictMode**: `ranRef = useRef(false)` — impede que o `useEffect` dispare duas vezes em desenvolvimento (React 18 StrictMode monta, desmonta e remonta)
- Guard de dados: `if (!loc.selfie || !memberId) → /choose`
- Cicla entre 4 mensagens de status a cada 2,2 s enquanto a API processa
- `POST /search` via FormData com `member_id` na query string e `selfie` no body
- **Sucesso com fotos**: dispatch `SET_RESULTS` + `ADD_MY_PHOTOS` → `/success`
- **Sucesso sem fotos**: → `/` com `{ state: { empty: true } }`
- **`CONSENT_REQUIRED`**: redireciona para `/consent` (backend rejeitou — consent expirou ou não aceito)
- **`NO_FACE_DETECTED`**: mensagem específica no estado de erro
- **Demais erros**: tela de erro com botão "Tentar novamente" → `/choose`

### Etapa 9 — SuccessScreen (`/success`)
- Dados vêm do `useLocation().state` (`total`, `results`)
- Conta eventos únicos: `new Set(results.map(r => r.event_id).filter(Boolean)).size`
- Confetti ativo por 4 s (90 partículas geradas via DOM em `useEffect`)
- "Ver minhas fotos" → `/` (ResultsScreen com os resultados já no estado)
- "Ver todos os eventos" → `/events`

---

## Fluxo 3 — Resultados e detalhe de foto

```
/ (ResultsScreen) ── foto ──► /photo/:id (PhotoDetailScreen)
                                    ├── Favoritar (toggle local)
                                    ├── Compartilhar (Web Share API / clipboard)
                                    ├── "Baixar" ──► DownloadModal ──► OTP ──► signed URL
                                    └── "Denunciar" ──► ReportModal ──► POST /report-photo
```

### Etapa 10 — ResultsScreen (`/`)
- Estado inicial (sem busca): empty state com "Buscar fotos" → `/choose`
- Estado `loc.empty = true` (busca sem resultado): dicas de selfie + "Tentar outra foto"
- Com resultados: **3 abas**
  - **Todos**: `state.searchResults` ordenados por similaridade (já ordenados pelo backend)
  - **Eventos**: chips filtragem; nomes reais via `eventNameMap` construído dos próprios resultados (`r.event_name`)
  - **Favoritos**: filtra por `state.favorites` (Set de photo_ids)
- Card foto → `/photo/:id` com `{ state: { photo } }` (sem fetch extra na tela de detalhe)
- "Nova busca" → `/choose`

### Etapa 11 — PhotoDetailScreen (`/photo/:id`)
- **Dados da foto**: vêm de `useLocation().state.photo` — sem chamada de API extra
- Se `state` vazio (acesso direto pela URL): `navigate(-1)` imediato
- **DownloadModal**:
  - `calledRef = useRef(false)` — guard StrictMode (mesmo padrão do ProcessingScreen)
  - `POST /request-download { photo_id, member_id }` → obtém `download_request_id`
  - OTP 6 dígitos: foco automático entre campos; backspace volta campo anterior
  - `POST /confirm-download { download_request_id, code }` → `signed_url` → `<a>.click()`
  - "Reenviar código" → `POST /send-code { member_id, purpose: 'download' }`
  - Erros diferenciados: `INVALID_CODE` / `CODE_EXPIRED` com mensagens específicas
- **ReportModal**: `POST /report-photo { photo_id, member_id?, reason }` — `member_id` omitido se null (denúncia anônima aceita pelo backend)

---

## Fluxo 4 — Minha área

```
BottomNav (presente em todas as telas MainLayout)
    ├── Início (/) ──────────────────────────► ResultsScreen
    ├── Eventos (/events) ──► card evento ──► /my-photos?filterEvent
    ├── 📷 (center) ──────────────────────────► /choose
    ├── Minhas Fotos (/my-photos) ──► foto ──► /photo/:id
    └── Perfil (/profile) ──► Logout ────────► /welcome
```

### Etapa 12 — MyPhotosScreen (`/my-photos`)
- Lê `state.myPhotos` do AppContext (persiste no localStorage entre sessões)
- **Filtro de evento**: lê `useLocation().state.filterEvent` + `eventName` (passados pela EventsScreen via `navigate('/my-photos', { state: {...} })`)
- Quando filtrado: título = `eventName`; back button visível → `/events`
- Abas "Todas" / "Favoritas"
- Foto click → `/photo/:id`
- Empty state com "Buscar fotos" → `/choose`

### Etapa 13 — EventsScreen (`/events`)
- `GET /events` — endpoint público (sem token)
- Emoji rotativo por índice (`EVENT_EMOJIS[i % EMOJIS.length]`) para variedade visual
- Card evento → `navigate('/my-photos', { state: { filterEvent: event.id, eventName: event.name } })`

### Etapa 14 — ProfileScreen (`/profile`)
- Stats: `state.myPhotos.length` (fotos salvas) + `state.favorites.size` (favoritas)
- "Privacidade (LGPD)" → `/consent` (re-consent; `POST /consent` é idempotente no backend)
- **Logout**: `dispatch(LOGOUT)` → `sessionStorage.clear()` → `/welcome`
  - `myPhotos` e `favorites` são mantidos (persistem no localStorage — dados do dispositivo, não da sessão)

---

## Fluxo 5 — Admin

```
/admin (login) ──► token válido ──► /admin/queue ──► card ──► /admin/case/:id
                                         └── "Sair" ◄──────── "Voltar"
```

Token: `sessionStorage.getItem('cciAdminToken')` — nunca localStorage.

### Etapa 15 — AdminLoginScreen (`/admin`)
- Valida token chamando `GET /admin/queue` com `x-admin-token`
- HTTP 403 → "Token inválido"
- Sucesso → `sessionStorage.setItem('cciAdminToken')` → `/admin/queue`

### Etapa 16 — AdminQueueScreen (`/admin/queue`)
- Se sem token → redirect `/admin`
- `GET /admin/queue` com `x-admin-token`; HTTP 403 → redirect `/admin`
- Cada card → `/admin/case/:id` com `{ state: { report } }` (sem fetch extra)
- "Sair" → `sessionStorage.removeItem('cciAdminToken')` → `/admin`

### Etapa 17 — AdminCaseScreen (`/admin/case/:id`)
- Se `!report || !token` → redirect `/admin` imediato
- Exibe: foto preview, motivo, denunciante (ou "Anônimo"), data
- "Aprovar" → `POST /admin/queue/:id/approve` → tela de resultado → `/admin/queue` após 1,8 s
- "Rejeitar" → `POST /admin/queue/:id/reject` → idem

---

## Estado global — AppContext

| Campo | Tipo | Persiste | Descrição |
|---|---|---|---|
| `memberId` | `string \| null` | sessionStorage | ID do membro; define autenticação |
| `memberName` | `string` | sessionStorage | Nome para exibição no Perfil |
| `searchResults` | `Photo[]` | memória | Resultado da última busca |
| `myPhotos` | `Photo[]` | localStorage | Todas as fotos encontradas nas buscas |
| `favorites` | `Set<string>` | localStorage (array) | photo_ids favoritados |
| `toast` | `{msg, kind} \| null` | memória | Auto-clear em 3 s |

### Ações do reducer

| Action | Efeito colateral | Observação |
|---|---|---|
| `SET_MEMBER` | sessionStorage | Usado no RegisterScreen após POST /register |
| `SET_RESULTS` | — | Substitui resultados da busca |
| `ADD_MY_PHOTOS` | localStorage | Merge sem duplicar (compara `photo_id`) |
| `TOGGLE_FAVORITE` | localStorage | Adiciona ou remove do Set |
| `SHOW_TOAST` | — | Auto-clear via useEffect com timeout |
| `CLEAR_TOAST` | — | Limpa o toast manualmente |
| `LOGOUT` | sessionStorage.clear() | Preserva `myPhotos` e `favorites` |

### Formato de um objeto Photo (vem do backend `/search`)

```js
{
  photo_id: string,
  filename: string,
  preview_url: string,   // URL pública do preview (bucket Supabase)
  event_id: string,
  event_name: string,    // nome legível do evento
  similarity: number,    // 0..1
}
```

---

## API — client.js

Todas as chamadas passam pela função `request(method, path, body, opts)` que:
- Lança `Error` com `err.code` e `err.status` em caso de falha
- Retorna `json.data` (campo raiz de todas as respostas de sucesso)

| Método | Path | Função exportada | Tela |
|---|---|---|---|
| POST | `/register` | `api.register` | RegisterScreen |
| POST | `/consent` | `api.consent` | ConsentScreen |
| POST | `/send-code` | `api.sendCode` | DownloadModal |
| POST | `/confirm-code` | `api.confirmCode` | (reservado) |
| POST | `/search` | `api.search` | ProcessingScreen |
| POST | `/request-download` | `api.requestDownload` | DownloadModal |
| POST | `/confirm-download` | `api.confirmDownload` | DownloadModal |
| POST | `/report-photo` | `api.reportPhoto` | ReportModal |
| GET | `/events` | `api.getEvents` | EventsScreen |
| GET | `/admin/queue` | `api.admin.getQueue` | AdminLoginScreen, AdminQueueScreen |
| POST | `/admin/queue/:id/approve` | `api.admin.approve` | AdminCaseScreen |
| POST | `/admin/queue/:id/reject` | `api.admin.reject` | AdminCaseScreen |

---

## Layouts (App.jsx)

| Layout | Guard | Bottom Nav | Toast | Telas |
|---|---|---|---|---|
| `MainLayout` | `memberId` obrigatório | ✅ | ✅ | `/`, `/events`, `/my-photos`, `/profile`, `/photo/:id` |
| `FlowLayout` | `memberId` obrigatório | ❌ | ✅ | `/choose`, `/capture`, `/processing`, `/success` |
| Livre | Nenhum | ❌ | ❌ | `/splash`, `/welcome`, `/register`, `/consent`, `/how-it-works`, `/admin*` |

---

## Pontos de manutenção recorrentes

| Situação | O que fazer |
|---|---|
| Adicionar nova tela | Criar JSX em `screens/`; registrar rota em `App.jsx`; escolher layout |
| Adicionar chamada de API | Adicionar função em `api/client.js`; verificar se precisa header de token |
| Novo campo no estado global | Adicionar a `initialState` e ao `reducer`; decidir onde persiste |
| Campo novo na resposta de `/search` | Atualizar `routes_search.py` + `ADD_MY_PHOTOS` no reducer se precisar guardar |
| Novo fluxo admin | Rota livre em `App.jsx` (sem MainLayout) |
| Alterar TTL de toast | `AppContext.jsx` → `useEffect` do `SHOW_TOAST` (atualmente 3000 ms) |
| Alterar threshold de similaridade | `config.py` → `similarity_threshold` (padrão 0.40) |
