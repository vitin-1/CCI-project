/**
 * ProfileScreen — /profile
 * Fluxo 4 / Etapa 14
 *
 * Área do usuário com estatísticas e opções de navegação.
 *
 * Logout:
 *   dispatch(LOGOUT) → sessionStorage.clear() → /welcome
 *   myPhotos e favorites são MANTIDOS (persistem no localStorage — dados do dispositivo)
 *
 * "Privacidade (LGPD)" → /consent
 *   POST /consent é idempotente: re-consent apenas atualiza consent_accepted_at no backend
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export default function ProfileScreen() {
  const navigate = useNavigate();
  const { state, dispatch } = useApp();
  const [confirmLogout, setConfirmLogout] = useState(false);

  function logout() {
    dispatch({ type: 'LOGOUT' });
    navigate('/welcome', { replace: true });
  }

  return (
    <div className="screen screen-pad" style={{ paddingTop: 32, gap: 20 }}>
      {/* Avatar e nome */}
      <div className="anim-fade-in-up" style={{ textAlign: 'center', paddingBottom: 8 }}>
        <div style={{
          width: 72, height: 72,
          background: 'var(--accent-dim)',
          border: '2px solid var(--accent)',
          borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 30, margin: '0 auto 16px',
        }}>
          👤
        </div>
        <h2 style={{ marginBottom: 4 }}>{state.memberName || 'Participante'}</h2>
        <p style={{ fontSize: 13 }}>Membro CCI Aliança</p>
      </div>

      {/* Stats: fotos salvas e favoritas */}
      <div className="anim-fade-in-up delay-1 card" style={{ display: 'flex', gap: 0 }}>
        {[
          { label: 'Fotos salvas', value: state.myPhotos.length },
          { label: 'Favoritas', value: state.favorites.size },
        ].map(({ label, value }, i) => (
          <div key={i} style={{
            flex: 1, textAlign: 'center', padding: '8px 0',
            borderRight: i === 0 ? '1px solid var(--border)' : 'none',
          }}>
            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent)' }}>{value}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Links de navegação */}
      <div className="anim-fade-in-up delay-2 card" style={{ padding: 0, overflow: 'hidden' }}>
        {[
          { icon: '📷', label: 'Minhas Fotos',       action: () => navigate('/my-photos') },
          { icon: '📅', label: 'Eventos',             action: () => navigate('/events') },
          { icon: '🔒', label: 'Privacidade (LGPD)', action: () => navigate('/consent') },
        ].map(({ icon, label, action }, i) => (
          <button
            key={i}
            onClick={action}
            style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '16px 20px', width: '100%',
              background: 'none', border: 'none',
              borderBottom: i < 2 ? '1px solid var(--border)' : 'none',
              color: 'var(--text)', cursor: 'pointer',
              fontFamily: 'inherit', fontSize: 15,
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--surface-2)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
          >
            <span style={{ fontSize: 20 }}>{icon}</span>
            <span style={{ flex: 1, textAlign: 'left' }}>{label}</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        ))}
      </div>

      <div className="anim-fade-in-up delay-3">
        {confirmLogout ? (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <p style={{ fontSize: 14, color: 'var(--text)', textAlign: 'center' }}>
              Tem certeza? Suas fotos salvas serão mantidas.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-danger" style={{ flex: 1 }} onClick={logout}>
                Sair
              </button>
              <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => setConfirmLogout(false)}>
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <button className="btn btn-danger" onClick={() => setConfirmLogout(true)}>
            Sair da conta
          </button>
        )}
      </div>

      <p className="anim-fade-in-up delay-4" style={{ fontSize: 11, textAlign: 'center', color: 'var(--text-muted)', marginTop: 8 }}>
        Dados biométricos protegidos por LGPD — excluídos após 90 dias
      </p>
    </div>
  );
}
