/**
 * PhotoDetailScreen — /photo/:id
 * Fluxo 3 / Etapa 11
 *
 * Exibe uma foto em detalhe. Dados vêm do navigation state (sem fetch extra).
 * Se acessado diretamente pela URL (sem state), redireciona para trás.
 *
 * Ações disponíveis:
 *   Favoritar      — toggle local via TOGGLE_FAVORITE
 *   Compartilhar   — Web Share API com fallback para clipboard
 *   Baixar         — abre DownloadModal (fluxo OTP via WhatsApp)
 *   Denunciar      — abre ReportModal
 *
 * ─── DownloadModal ────────────────────────────────────────────────────────────
 * Guard StrictMode (calledRef): React 18 dev monta → desmonta → remonta, então o
 * useEffect dispararia POST /request-download duas vezes, criando dois pedidos.
 * calledRef.current impede a segunda chamada sem afetar o comportamento em produção.
 *
 * Fluxo OTP:
 *   1. mount         → POST /request-download → recebe download_request_id
 *   2. usuário digita → OTP 6 dígitos (auto-foco entre campos)
 *   3. confirmar      → POST /confirm-download → signed_url → <a>.click()
 *   4. reenviar       → POST /send-code { purpose: 'download' }
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../api/client';
import { useApp } from '../context/AppContext';

// ─── OTP Input ────────────────────────────────────────────────────────────────

function OtpInput({ value, onChange }) {
  // Normaliza para array de 6 posições, preenchendo com espaços
  const digits = (value + '      ').slice(0, 6).split('');

  function handleChange(e, idx) {
    const v = e.target.value.replace(/\D/g, '').slice(-1);
    const arr = (value + '      ').slice(0, 6).split('');
    arr[idx] = v || ' ';
    const next = arr.join('').trimEnd();
    onChange(next);
    // Avança foco automaticamente ao preencher um dígito
    if (v && idx < 5) {
      document.getElementById(`otp-${idx + 1}`)?.focus();
    }
  }

  function handleKeyDown(e, idx) {
    // Backspace volta ao campo anterior se o atual estiver vazio
    if (e.key === 'Backspace' && !digits[idx].trim() && idx > 0) {
      document.getElementById(`otp-${idx - 1}`)?.focus();
    }
  }

  return (
    <div className="otp-wrapper">
      {digits.map((d, i) => (
        <input
          key={i}
          id={`otp-${i}`}
          className="otp-input"
          type="tel"
          inputMode="numeric"
          maxLength={1}
          value={d.trim()}
          onChange={(e) => handleChange(e, i)}
          onKeyDown={(e) => handleKeyDown(e, i)}
          autoFocus={i === 0}
        />
      ))}
    </div>
  );
}

// ─── Download Modal ───────────────────────────────────────────────────────────

function DownloadModal({ photo, memberId, onClose }) {
  const [code, setCode] = useState('');
  const [requestId, setRequestId] = useState('');
  const [step, setStep] = useState('requesting'); // 'requesting' | 'code' | 'done'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { dispatch } = useApp();
  const calledRef = useRef(false);  // guard StrictMode — ver comentário no topo do arquivo

  async function requestDownload() {
    setLoading(true);
    setError('');
    try {
      const data = await api.requestDownload({ photo_id: photo.photo_id, member_id: memberId });
      setRequestId(data.download_request_id);
      setStep('code');
    } catch (err) {
      setError(err.message || 'Erro ao solicitar download.');
    } finally {
      setLoading(false);
    }
  }

  async function confirmDownload() {
    if (code.replace(/\s/g, '').length !== 6) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.confirmDownload({ download_request_id: requestId, code: code.replace(/\s/g, '') });
      // Aciona download programaticamente via link temporário
      const a = document.createElement('a');
      a.href = data.signed_url;
      a.download = photo.filename || 'foto-cci.jpg';
      a.target = '_blank';
      a.click();
      setStep('done');
      dispatch({ type: 'SHOW_TOAST', msg: 'Download iniciado!', kind: 'success' });
      setTimeout(onClose, 2000);
    } catch (err) {
      if (err.code === 'INVALID_CODE') setError('Código inválido. Verifique e tente novamente.');
      else if (err.code === 'CODE_EXPIRED') setError('Código expirado. Solicite um novo abaixo.');
      else setError(err.message || 'Erro ao confirmar download.');
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    setError('');
    setCode('');
    try {
      await api.sendCode({ member_id: memberId, purpose: 'download' });
      dispatch({ type: 'SHOW_TOAST', msg: 'Novo código enviado!', kind: 'success' });
    } catch {
      dispatch({ type: 'SHOW_TOAST', msg: 'Erro ao reenviar código.', kind: 'error' });
    }
  }

  // Dispara o pedido de download ao montar — calledRef evita double call no StrictMode
  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;
    requestDownload();
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="modal-handle" />

        {step === 'done' ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
            <h3>Download iniciado!</h3>
          </div>
        ) : step === 'code' ? (
          <>
            <h3 style={{ marginBottom: 8 }}>Digite o código</h3>
            <p style={{ fontSize: 14 }}>Enviamos um código de 6 dígitos para o seu WhatsApp.</p>
            <OtpInput value={code} onChange={setCode} />
            {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}
            <button
              className="btn btn-primary"
              onClick={confirmDownload}
              disabled={code.replace(/\s/g, '').length !== 6 || loading}
            >
              {loading ? <span className="spinner" /> : 'Confirmar'}
            </button>
            <button className="btn btn-ghost" onClick={resend} style={{ marginTop: 12, color: 'var(--accent)' }}>
              Reenviar código
            </button>
          </>
        ) : (
          // Etapa "requesting": aguardando resposta do POST /request-download
          <div style={{ textAlign: 'center', padding: '20px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <span className="spinner spinner-lg" />
            {error ? (
              <>
                <div className="error-msg">{error}</div>
                <button className="btn btn-primary" onClick={requestDownload}>Tentar novamente</button>
              </>
            ) : (
              <p>Enviando código para seu WhatsApp…</p>
            )}
          </div>
        )}

        <button className="btn btn-ghost" onClick={onClose} style={{ marginTop: 8, color: 'var(--text-muted)' }}>
          Cancelar
        </button>
      </div>
    </div>
  );
}

// ─── Report Modal ─────────────────────────────────────────────────────────────

function ReportModal({ photo, memberId, onClose }) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const { dispatch } = useApp();

  async function submit() {
    if (!reason.trim()) return;
    setLoading(true);
    try {
      // member_id pode ser undefined → denúncia anônima (backend aceita)
      await api.reportPhoto({ photo_id: photo.photo_id, member_id: memberId || undefined, reason: reason.trim() });
      setDone(true);
      setTimeout(() => {
        dispatch({ type: 'SHOW_TOAST', msg: 'Obrigado! Vamos revisar em breve.', kind: 'success' });
        onClose();
      }, 1500);
    } catch {
      dispatch({ type: 'SHOW_TOAST', msg: 'Erro ao enviar denúncia.', kind: 'error' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="modal-handle" />
        {done ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🙏</div>
            <h3>Obrigado!</h3>
            <p style={{ marginTop: 8 }}>Vamos revisar esta foto em breve.</p>
          </div>
        ) : (
          <>
            <h3 style={{ marginBottom: 8 }}>Essa foto não é você?</h3>
            <p style={{ fontSize: 14, marginBottom: 16 }}>Descreva o motivo da denúncia e nossa equipe irá revisar.</p>
            <textarea
              className="input"
              placeholder="Ex: Não sou eu nesta foto, rosto de outra pessoa..."
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              style={{ resize: 'none', marginBottom: 16 }}
            />
            <button
              className="btn btn-danger"
              onClick={submit}
              disabled={!reason.trim() || loading}
            >
              {loading ? <span className="spinner" /> : 'Enviar denúncia'}
            </button>
            <button className="btn btn-ghost" onClick={onClose} style={{ marginTop: 8, color: 'var(--text-muted)' }}>
              Cancelar
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Tela principal ───────────────────────────────────────────────────────────

export default function PhotoDetailScreen() {
  const navigate = useNavigate();
  const { state: loc } = useLocation();
  const { state, dispatch } = useApp();
  const [showDownload, setShowDownload] = useState(false);
  const [showReport, setShowReport] = useState(false);

  // Dados da foto vêm do navigation state — sem chamada de API extra
  const photo = loc?.photo;
  const isFav = photo ? state.favorites.has(photo.photo_id) : false;

  // Acesso direto pela URL sem state → volta para a tela anterior
  if (!photo) {
    navigate(-1);
    return null;
  }

  function toggleFav() {
    dispatch({ type: 'TOGGLE_FAVORITE', photoId: photo.photo_id });
    dispatch({
      type: 'SHOW_TOAST',
      msg: isFav ? 'Removido dos favoritos' : 'Adicionado aos favoritos ❤️',
      kind: isFav ? 'default' : 'success',
    });
  }

  async function share() {
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Minha foto — CCI Aliança', url: photo.preview_url });
      } catch {/* usuário cancelou o share sheet */}
    } else {
      // Fallback: copia URL para clipboard (desktop ou browser sem Web Share API)
      await navigator.clipboard.writeText(photo.preview_url);
      dispatch({ type: 'SHOW_TOAST', msg: 'Link copiado!', kind: 'success' });
    }
  }

  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="screen-header">
        <button className="back-btn" onClick={() => navigate(-1)} aria-label="Voltar">‹</button>
        <span className="screen-title">Detalhes</span>
        <button
          onClick={toggleFav}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 24, color: isFav ? '#f472b6' : 'var(--text-muted)' }}
          aria-label={isFav ? 'Remover favorito' : 'Adicionar favorito'}
        >
          {isFav ? '❤️' : '🤍'}
        </button>
      </div>

      {/* Foto em tela cheia */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <img
          src={photo.preview_url}
          alt={photo.filename}
          className="anim-zoom-in"
          style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#000' }}
        />
      </div>

      {/* Metadados e ações */}
      <div className="anim-fade-in-up" style={{ padding: '16px 20px 0', background: 'var(--surface)', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Correspondência</p>
            <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent)' }}>
              {Math.round(photo.similarity * 100)}%
            </span>
          </div>
          <button
            className="btn btn-outline"
            onClick={share}
            style={{ width: 'auto', padding: '10px 20px' }}
          >
            Compartilhar
          </button>
        </div>

        <button className="btn btn-primary" onClick={() => setShowDownload(true)}>
          Baixar Foto Original
        </button>

        <button
          className="btn btn-ghost"
          onClick={() => setShowReport(true)}
          style={{ marginTop: 8, fontSize: 13, color: 'var(--text-muted)' }}
        >
          Essa foto não é minha
        </button>
      </div>

      {showDownload && (
        <DownloadModal
          photo={photo}
          memberId={state.memberId}
          onClose={() => setShowDownload(false)}
        />
      )}
      {showReport && (
        <ReportModal
          photo={photo}
          memberId={state.memberId}
          onClose={() => setShowReport(false)}
        />
      )}
    </div>
  );
}
