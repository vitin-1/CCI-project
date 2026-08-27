/**
 * AdminQueueScreen — /admin/queue
 * Fluxo 5 / Etapa 16
 *
 * Lista as denúncias com status "pending" aguardando revisão.
 * Guard: se sem token → /admin; se token inválido (403) → /admin.
 *
 * API: GET /admin/queue com header x-admin-token
 * Ao clicar num card → /admin/case/:id com { state: { report } } (sem fetch extra)
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';

function formatDate(iso) {
  try { return new Date(iso).toLocaleString('pt-BR'); } catch { return iso; }
}

export default function AdminQueueScreen() {
  const navigate = useNavigate();
  const token = sessionStorage.getItem('cciAdminToken');
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Guard: sem token → volta para login
    if (!token) { navigate('/admin', { replace: true }); return; }

    api.admin.getQueue(token)
      .then((data) => setQueue(data.queue || []))
      .catch((err) => {
        // 403 = token expirou ou foi invalidado → volta para login
        if (err.status === 403) navigate('/admin', { replace: true });
        else setError(err.message || 'Erro ao carregar fila.');
      })
      .finally(() => setLoading(false));
  }, []);

  function logout() {
    sessionStorage.removeItem('cciAdminToken');
    navigate('/admin', { replace: true });
  }

  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '20px 20px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border)' }}>
        <div>
          <h2 style={{ marginBottom: 2 }}>Fila de Revisão</h2>
          {!loading && <p style={{ fontSize: 13 }}>{queue.length} pendente{queue.length !== 1 ? 's' : ''}</p>}
        </div>
        <button onClick={logout} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontFamily: 'inherit', fontSize: 14 }}>
          Sair
        </button>
      </div>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <span className="spinner spinner-lg" />
        </div>
      )}

      {error && <div className="error-msg" style={{ margin: 20 }}>{error}</div>}

      {!loading && queue.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-icon">✅</div>
          <h2 style={{ marginBottom: 8 }}>Fila vazia</h2>
          <p>Nenhuma denúncia pendente no momento.</p>
        </div>
      )}

      {/* Lista de denúncias */}
      <div style={{ overflowY: 'auto', flex: 1, padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {queue.map((report, i) => (
          <div
            key={report.report_id}
            className="card"
            style={{ cursor: 'pointer', animationDelay: `${i * 0.06}s`, animation: 'stagger-appear 0.4s ease forwards', opacity: 0 }}
            onClick={() => navigate(`/admin/case/${report.report_id}`, { state: { report } })}
          >
            <div style={{ display: 'flex', gap: 12 }}>
              {report.preview_url && (
                <img
                  src={report.preview_url}
                  alt="Preview"
                  style={{ width: 64, height: 64, borderRadius: 8, objectFit: 'cover', flexShrink: 0 }}
                />
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontWeight: 600, color: 'var(--text)', fontSize: 14, marginBottom: 4 }}>
                  {report.reason}
                </p>
                {report.reporter
                  ? <p style={{ fontSize: 12, marginBottom: 4 }}>Por: {report.reporter.full_name}</p>
                  : <p style={{ fontSize: 12, marginBottom: 4, color: 'var(--text-muted)' }}>Anônimo</p>
                }
                <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{formatDate(report.created_at)}</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" style={{ flexShrink: 0, alignSelf: 'center' }}>
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
