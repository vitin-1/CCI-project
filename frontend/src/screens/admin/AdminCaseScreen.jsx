/**
 * AdminCaseScreen — /admin/case/:id
 * Fluxo 5 / Etapa 17
 *
 * Exibe o detalhe de uma denúncia e permite aprovar ou rejeitar.
 * Dados do report vêm do navigation state (sem fetch extra).
 * Guard: se !report || !token → /admin imediato.
 *
 * Aprovar → POST /admin/queue/:id/approve → foto é removida do sistema
 * Rejeitar → POST /admin/queue/:id/reject → denúncia encerrada sem ação
 * Após decidir: tela de confirmação → /admin/queue após 1,8s
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../../api/client';

export default function AdminCaseScreen() {
  const navigate = useNavigate();
  const { state: loc } = useLocation();
  const token = sessionStorage.getItem('cciAdminToken');
  const [loading, setLoading] = useState(null); // 'approve' | 'reject' | null
  const [done, setDone] = useState('');          // 'approve' | 'reject' | ''
  const [error, setError] = useState('');

  const report = loc?.report;

  // Guard: sem report (acesso direto) ou sem token → volta para login
  if (!report || !token) { navigate('/admin', { replace: true }); return null; }

  async function decide(action) {
    setLoading(action);
    setError('');
    try {
      if (action === 'approve') {
        await api.admin.approve(report.report_id, token);
      } else {
        await api.admin.reject(report.report_id, token);
      }
      setDone(action);
      // Volta automaticamente para a fila após mostrar confirmação
      setTimeout(() => navigate('/admin/queue', { replace: true }), 1800);
    } catch (err) {
      setError(err.message || 'Erro ao processar a decisão.');
    } finally {
      setLoading(null);
    }
  }

  // ─── Estado de confirmação ────────────────────────────────────────────────

  if (done) {
    return (
      <div className="screen" style={{ justifyContent: 'center', alignItems: 'center', gap: 16, textAlign: 'center' }}>
        <div style={{ fontSize: 56 }}>{done === 'approve' ? '✅' : '❌'}</div>
        <h2>{done === 'approve' ? 'Denúncia aprovada' : 'Denúncia rejeitada'}</h2>
        <p>Voltando para a fila…</p>
      </div>
    );
  }

  // ─── Tela do caso ─────────────────────────────────────────────────────────

  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="screen-header">
        <button className="back-btn" onClick={() => navigate(-1)} aria-label="Voltar">‹</button>
        <span className="screen-title">Caso #{report.report_id.slice(0, 8)}</span>
      </div>

      {/* Preview da foto denunciada */}
      {report.preview_url && (
        <div style={{ flex: 1, overflow: 'hidden', background: '#000' }}>
          <img
            src={report.preview_url}
            alt="Foto denunciada"
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
          />
        </div>
      )}

      {/* Detalhes da denúncia */}
      <div className="card" style={{ margin: 16, borderRadius: 'var(--r-sm)', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Motivo da denúncia</p>
          <p style={{ color: 'var(--text)', fontWeight: 500 }}>{report.reason}</p>
        </div>

        {report.reporter
          ? (
            <div>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Denunciante</p>
              <p style={{ color: 'var(--text)' }}>{report.reporter.full_name}</p>
            </div>
          )
          : <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Denúncia anônima</p>
        }

        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Enviada em {new Date(report.created_at).toLocaleString('pt-BR')}
        </p>
      </div>

      {error && <div className="error-msg" style={{ margin: '0 16px 8px' }}>{error}</div>}

      {/* Ações */}
      <div style={{ padding: '0 16px 32px', display: 'flex', gap: 10 }}>
        <button
          className="btn btn-primary"
          onClick={() => decide('approve')}
          disabled={!!loading}
          style={{ flex: 1 }}
        >
          {loading === 'approve' ? <span className="spinner" /> : '✓ Aprovar'}
        </button>
        <button
          className="btn btn-danger"
          onClick={() => decide('reject')}
          disabled={!!loading}
          style={{ flex: 1 }}
        >
          {loading === 'reject' ? <span className="spinner" /> : '✕ Rejeitar'}
        </button>
      </div>
    </div>
  );
}
