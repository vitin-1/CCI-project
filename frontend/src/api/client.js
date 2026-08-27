/**
 * client.js — Camada de comunicação com o backend FastAPI
 *
 * Todas as respostas de sucesso retornam `json.data`.
 * Todos os erros lançam um Error com:
 *   err.message  — mensagem legível
 *   err.code     — código de erro (ex: "NO_FACE_DETECTED", "INVALID_CODE")
 *   err.status   — HTTP status code
 *
 * URL base: variável de ambiente VITE_API_URL (padrão: http://localhost:8000)
 * Ver: frontend/.env ou frontend/.env.example
 */

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Função central — usada por todas as chamadas abaixo
async function request(method, path, body, opts = {}) {
  const headers = { ...opts.headers };
  let fetchBody;

  if (body instanceof FormData) {
    // FormData: não definir Content-Type — o browser define com o boundary correto
    fetchBody = body;
  } else if (body != null) {
    headers['Content-Type'] = 'application/json';
    fetchBody = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, { method, headers, body: fetchBody });
  const json = await res.json();

  if (!res.ok) {
    const err = new Error(json.detail?.message || 'Erro desconhecido');
    err.code = json.detail?.code || 'UNKNOWN';
    err.status = res.status;
    throw err;
  }
  return json.data;
}

// ─── API pública (membros) ────────────────────────────────────────────────────

export const api = {
  // Fluxo 1 — Onboarding
  register:    (body) => request('POST', '/register', body),
  consent:     (body) => request('POST', '/consent', body),
  sendCode:    (body) => request('POST', '/send-code', body),
  confirmCode: (body) => request('POST', '/confirm-code', body),

  // Fluxo 2 — Busca
  // selfieBlob: Blob ou File capturado na CaptureScreen ou ChooseOptionScreen
  search: (memberId, selfieBlob) => {
    const fd = new FormData();
    fd.append('selfie', selfieBlob, 'selfie.jpg');
    return request('POST', `/search?member_id=${encodeURIComponent(memberId)}`, fd);
  },

  // Fluxo 3 — Download (OTP via WhatsApp)
  requestDownload: (body) => request('POST', '/request-download', body),
  confirmDownload: (body) => request('POST', '/confirm-download', body),

  // Fluxo 3 — Denúncia (member_id pode ser omitido para denúncias anônimas)
  reportPhoto: (body) => request('POST', '/report-photo', body),

  // Fluxo 4 — Eventos
  getEvents: () => request('GET', '/events'),

  // ─── API admin ───────────────────────────────────────────────────────────────
  // Token passado via header x-admin-token (sessionStorage apenas)
  admin: {
    getQueue: (token) =>
      request('GET', '/admin/queue', null, { headers: { 'x-admin-token': token } }),
    approve: (reportId, token) =>
      request('POST', `/admin/queue/${reportId}/approve`, null, { headers: { 'x-admin-token': token } }),
    reject: (reportId, token) =>
      request('POST', `/admin/queue/${reportId}/reject`, null, { headers: { 'x-admin-token': token } }),
  },
};
