/**
 * WelcomeScreen — /welcome
 * Fluxo 1 / Etapa 2
 *
 * Tela de boas-vindas para novos usuários.
 * Guard em App.jsx: se já autenticado → redireciona para /.
 *
 * Saídas:
 *   "Vamos Começar"  → /register
 *   "Como funciona?" → /how-it-works
 */

import { useNavigate } from 'react-router-dom';

export default function WelcomeScreen() {
  const navigate = useNavigate();

  return (
    <div className="screen" style={{ justifyContent: 'center', gap: 32, paddingTop: 40, paddingBottom: 40 }}>
      <div className="anim-fade-in-up" style={{ textAlign: 'center' }}>
        <img
          src="/logo.jpg"
          alt="CCI Aliança"
          style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', marginBottom: 24 }}
        />
        <h1 className="anim-fade-in-up delay-1" style={{ marginBottom: 12 }}>Bem-vindo!</h1>
        <p className="anim-fade-in-up delay-2" style={{ fontSize: 16, lineHeight: 1.7, maxWidth: 320, margin: '0 auto' }}>
          Encontre suas fotos nos eventos da nossa igreja usando reconhecimento facial.
        </p>
      </div>

      {/* Ilustração de celular com scan line animado */}
      <div className="anim-fade-in-up delay-3" style={{ display: 'flex', justifyContent: 'center' }}>
        <div style={{
          width: 160,
          height: 240,
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 28,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            width: 80, height: 80,
            border: '2px solid var(--accent)',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'orbPulse 2s infinite',
          }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <div style={{
            position: 'absolute',
            width: '70%',
            height: 2,
            background: 'linear-gradient(90deg, transparent, var(--accent), transparent)',
            left: '15%',
            animation: 'scanLine 2.5s ease-in-out infinite',
          }} />
        </div>
      </div>

      <div className="anim-fade-in-up delay-4" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <button className="btn btn-primary" onClick={() => navigate('/register')}>
          Vamos Começar
        </button>
        <button className="btn btn-ghost" onClick={() => navigate('/how-it-works')} style={{ textAlign: 'center' }}>
          Como funciona?
        </button>
      </div>
    </div>
  );
}
